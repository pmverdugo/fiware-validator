# -*- coding: utf-8 -*-
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

"""Utility methods for working with WSGI servers."""
import abc
import time
import errno

import routes.middleware
from paste import deploy
import routes
import six
import webob.dec
import webob.exc
import eventlet

from validator.common.utils import JSONSerializer, JSONDeserializer

eventlet.patcher.monkey_patch(all=False, socket=True)
import eventlet.wsgi
from eventlet.green import socket

from oslo_service import service
from oslo_service import sslutils
from oslo_log import log as logging
from oslo_utils import importutils
from oslo_config import cfg

from validator.common import exception
from validator.common.i18n import _, _LW

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Service(service.Service):
    """Provides a Service API for wsgi servers.

    This gives us the ability to launch wsgi servers with the
    Launcher classes in oslo_service.service.py.
    """

    def __init__(self, application, port, host='0.0.0.0', backlog=4096,
                 threads=1000):
        self.application = application
        self._port = port
        self._host = host
        self._backlog = backlog if backlog else CONF.backlog
        super(Service, self).__init__(threads)

    @staticmethod
    def _get_socket(host, port, backlog):
        info = socket.getaddrinfo(
            host, port, socket.AF_UNSPEC, socket.SOCK_STREAM
        )[0]
        family = info[0]
        bind_addr = info[-1]

        sock = None
        retry_until = time.time() + 30
        while not sock and time.time() < retry_until:
            try:
                sock = eventlet.listen(bind_addr, backlog=backlog,
                                       family=family)
                if sslutils.is_enabled(CONF):
                    sock = sslutils.wrap(CONF, sock)

            except socket.error as err:
                if err.args[0] != errno.EADDRINUSE:
                    raise
        if not sock:
            raise RuntimeError(_(
                "Could not bind to %(host)s:%(port)s "
                "after trying for 30 seconds") %
                               {'host': host, 'port': port})
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sockets can hang around forever without keepalive
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # This option isn't available in the OS X version of eventlet
        if hasattr(socket, 'TCP_KEEPIDLE'):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE,
                            CONF.tcp_keepidle)

        return sock

    def start(self):
        """Start serving this service using the provided server instance.

        :returns: None

        """
        super(Service, self).start()
        self._socket = self._get_socket(self._host, self._port, self._backlog)
        self.tg.add_thread(self._run, self.application, self._socket)

    @property
    def backlog(self):
        return self._backlog

    @property
    def host(self):
        return self._socket.getsockname()[0] if self._socket else self._host

    @property
    def port(self):
        return self._socket.getsockname()[1] if self._socket else self._port

    def stop(self):
        """Stop serving this API.

        :returns: None

        """
        super(Service, self).stop()

    def reset(self):
        super(Service, self).reset()
        logging.setup(CONF, 'validator')

    def _run(self, application, asocket):
        """Start a WSGI server in a new green thread."""
        logger = logging.getLogger('eventlet.wsgi')
        eventlet.wsgi.server(
            asocket,
            application,
            custom_pool=self.tg.pool,
            log=logger
        )


class Middleware(object):
    """Base WSGI middleware wrapper. These classes require an application to be
    initialized that will be called next.  By default the middleware will
    simply call its wrapped app, or you can override __call__ to customize its
    behavior.
    """

    def __init__(self, application):
        self.application = application

    def process_request(self, req):
        """Called on each request.

        If this returns None, the next application down the stack will be
        executed. If it returns a response then that response will be returned
        and execution will stop here.
        """
        return None

    @staticmethod
    def process_response(response):
        """Do whatever you'd like to the response."""
        return response

    @webob.dec.wsgify
    def __call__(self, req):
        response = self.process_request(req)
        if response:
            return response
        response = req.get_response(self.application)
        return self.process_response(response)


class Request(webob.Request):
    """Add some Openstack API-specific logic to the base webob.Request."""

    default_request_content_types = ('application/json',)
    default_accept_types = ('application/json',)
    default_accept_type = 'application/json'

    def best_match_content_type(self, supported_content_types=None):
        """Determine the requested response content-type.

        Based on the query extension then the Accept header.
        Defaults to default_accept_type if we don't find a preference

        """
        supported_content_types = (supported_content_types
                                   or self.default_accept_types)

        parts = self.path.rsplit('.', 1)
        if len(parts) > 1:
            ctype = 'application/{0}'.format(parts[1])
            if ctype in supported_content_types:
                return ctype

        bm = self.accept.best_match(supported_content_types)
        return bm or self.default_accept_type

    def get_content_type(self, allowed_content_types=None):
        """Determine content type of the request body.

        Does not do any body introspection, only checks header

        """
        if "Content-Type" not in self.headers:
            return None

        content_type = self.content_type
        allowed_content_types = (allowed_content_types
                                 or self.default_request_content_types)

        if content_type not in allowed_content_types:
            raise exception.InvalidContentType(content_type=content_type)
        return content_type


class Resource(object):
    """WSGI app that handles (de)serialization and controller dispatch.

    Reads routing information supplied by RoutesMiddleware and calls
    the requested action method upon its deserializer, controller,
    and serializer. Those three objects may implement any of the basic
    controller action methods (create, update, show, index, delete)
    along with any that may be specified in the api router. A 'default'
    method may also be implemented to be used in place of any
    non-implemented actions. Deserializer methods must accept a request
    argument and return a dictionary. Controller methods must accept a
    request argument. Additionally, they must also accept keyword
    arguments that represent the keys returned by the Deserializer. They
    may raise a webob.exc exception or return a dict, which will be
    serialized by requested content type.
    """

    def __init__(self, controller, deserializer=None, serializer=None):
        """Resource init.
        :param controller: object that implement methods created by routes lib
        :param deserializer: object that supports webob request deserialization
                             through controller-like actions
        :param serializer: object that supports webob response serialization
                           through controller-like actions
        """
        self.controller = controller
        self.deserializer = deserializer or JSONDeserializer()
        self.serializer = serializer or JSONSerializer()

    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, request):
        """WSGI method that controls (de)serialization and method dispatch."""

        try:
            action_args = self.get_action_args(request.environ)
            action = action_args.pop('action', None)
            deserialized_request = self.deserialize_request(request)
            action_args.update(deserialized_request)
        except exception.InvalidContentType:
            msg = _("Unsupported Content-Type")
            return webob.exc.HTTPUnsupportedMediaType(explanation=msg)
        except exception.MalformedRequestBody:
            msg = _("Malformed request body")
            return webob.exc.HTTPBadRequest(explanation=msg)

        action_result = self.execute_action(action, request, **action_args)

        try:
            response = webob.Response(request=request)
            self.dispatch(self.serializer, action, response, action_result)
            return response
        # return unserializable result (typically a webob exc)
        except Exception:
            try:
                err_body = action_result.get_unserialized_body()
                self.serializer.default(action_result, err_body)
            except Exception:
                LOG.warning(_LW("Unable to serialize exception response"))
            return action_result

    def deserialize_request(self, request):
        return self.deserializer.deserialize(request)

    def serialize_response(self, action, action_result, accept):
        return self.serializer.serialize(action_result, accept, action)

    def execute_action(self, action, request, **action_args):
        return self.dispatch(self.controller, action, request, **action_args)

    @staticmethod
    def dispatch(obj, action, *args, **kwargs):
        """Find action-specific method on self and call it."""
        try:
            method = getattr(obj, action)
        except AttributeError:
            method = getattr(obj, 'default')
        return method(*args, **kwargs)

    @staticmethod
    def get_action_args(request_environment):
        """Parse dictionary created by routes library."""
        args = {}
        try:
            args = request_environment['wsgiorg.routing_args'][1].copy()
        except Exception:
            pass
        if 'controller' in args.keys():
            del args['controller']
        return args


class Router(object):
    """WSGI middleware that maps incoming requests to WSGI apps."""

    def __init__(self, mapper):
        """Create a router for the given routes.Mapper.

        Each route in `mapper` must specify a 'controller', which is a
        WSGI app to call.  You'll probably want to specify an 'action' as
        well and have your controller be a wsgi.Controller, who will route
        the request to the action method.

        Examples:
          mapper = routes.Mapper()
          sc = ServerController()

          # Explicit mapping of one route to a controller+action
          mapper.connect(None, "/svrlist", controller=sc, action="list")

          # Actions are all implicitly defined
          mapper.resource("server", "servers", controller=sc)

          # Pointing to an arbitrary WSGI app.  You can specify the
          # {path_info:.*} parameter so the target app can be handed just that
          # section of the URL.
          mapper.connect(None, "/v1.0/{path_info:.*}", controller=BlogApp())
        """
        self.map = mapper
        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                          self.map)

    @webob.dec.wsgify
    def __call__(self, req):
        """Route the incoming request to a controller based on self.map.
           If no match, return a 404.
        """
        return self._router

    @staticmethod
    @webob.dec.wsgify
    def _dispatch(req):
        """Called by self._router after matching the incoming request to
           a route and putting the information into req.environ.
           Either returns 404 or the routed WSGI app's response.
        """
        match = req.environ['wsgiorg.routing_args'][1]
        if not match:
            return webob.exc.HTTPNotFound()
        app = match['controller']
        return app


@six.add_metaclass(abc.ABCMeta)
class BasePasteFactory(object):
    """A base class for paste app and filter factories.

    Sub-classes must override the KEY class attribute and provide
    a __call__ method.
    """

    KEY = None

    def __init__(self, conf):
        self.conf = conf

    @abc.abstractmethod
    def __call__(self, global_conf, **local_conf):
        return

    def _import_factory(self, local_conf):
        """Import an app/filter class.

        Lookup the KEY from the PasteDeploy local conf and import the
        class named there. This class can then be used as an app or
        filter factory.

        Note we support the <module>:<class> format.

        Note also that if you do e.g.

          key =
              value

        then ConfigParser returns a value with a leading newline, so
        we strip() the value before using it.
        """
        class_name = local_conf[self.KEY].replace(':', '.').strip()
        return importutils.import_class(class_name)


class AppFactory(BasePasteFactory):
    """A Generic paste.deploy app factory.

    This requires validator.app_factory to be set to a callable which
    returns a WSGI app when invoked. The format of the name is
    <module>:<callable> e.g.

      [app:apiv1app]
      paste.app_factory = validator.common.wsgi:app_factory
      validator.app_factory = validator.api.cfn.v1:API

    The WSGI app constructor must accept a ConfigOpts object and a local config
    dict as its two arguments.
    """

    KEY = 'validator.app_factory'

    def __call__(self, global_conf, **local_conf):
        """The actual paste.app_factory protocol method."""
        factory = self._import_factory(local_conf)
        return factory(self.conf, **local_conf)


class FilterFactory(AppFactory):
    """A Generic paste.deploy filter factory.

    This requires validator.filter_factory to be set to a callable
    which returns a WSGI filter when invoked. The format is
    <module>:<callable> e.g.

      [filter:cache]
      paste.filter_factory = validator.common.wsgi:filter_factory
      validator.filter_factory =
      validator.api.middleware.cache:CacheFilter

    The WSGI filter constructor must accept a WSGI app, a ConfigOpts object and
    a local config dict as its three arguments.
    """

    KEY = 'validator.filter_factory'

    def __call__(self, global_conf, **local_conf):
        """The actual paste.filter_factory protocol method."""
        factory = self._import_factory(local_conf)

        def filter(app):
            return factory(app, self.conf, **local_conf)

        return filter


def setup_paste_factories(conf):
    """Set up the generic paste app and filter factories.

    Set things up so that:

      paste.app_factory = validator.common.wsgi:app_factory

    and

      paste.filter_factory = validator.common.wsgi:filter_factory

    work correctly while loading PasteDeploy configuration.

    The app factories are constructed at runtime to allow us to pass a
    ConfigOpts object to the WSGI classes.

    :param conf: a ConfigOpts object
    """
    global app_factory, filter_factory
    app_factory = AppFactory(conf)
    filter_factory = FilterFactory(conf)


def teardown_paste_factories():
    """Reverse the effect of setup_paste_factories()."""
    global app_factory, filter_factory
    del app_factory
    del filter_factory


def paste_deploy_app(paste_config_file, app_name, conf):
    """Load a WSGI app from a PasteDeploy configuration.

    Use deploy.loadapp() to load the app from the PasteDeploy configuration,
    ensuring that the supplied ConfigOpts object is passed to the app and
    filter constructors.

    :param paste_config_file: a PasteDeploy config file
    :param app_name: the name of the app/pipeline to load from the file
    :param conf: a ConfigOpts object to supply to the app and its filters
    :returns: the WSGI app
    """
    setup_paste_factories(conf)
    try:
        return deploy.loadapp("config:%s" % paste_config_file, name=app_name)
    finally:
        teardown_paste_factories()
