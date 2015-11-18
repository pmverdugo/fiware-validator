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
""" Main action mapper"""

from oslo_log import log as logging
from oslo_config import cfg
from webob import exc

from validator.common import wsgi
from validator.common.i18n import _LI, _
import validator.common.utils
from validator.engine.validate import ValidateEngine

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class PuppetController(object):
    """
    Puppet Controller Object
    Implements Application logic
    """

    @staticmethod
    def validate(request, body):
        """ Validate the given cookbook
        :param request: request context
        :param body: a json with deployment parameters
        :return : a json file with process results
        """
        body = body or {}
        if len(body) < 1:
            raise exc.HTTPBadRequest(_("No action specified"))
        try:
            cookbook = body['cookbook']
            image = body['image']
        except KeyError:
            raise exc.HTTPBadRequest(_("Insufficient payload"))

        LOG.info(_LI('Processing Request for cookbook %s, image %s' % (cookbook, image)))
        res = ValidateEngine().validate_puppet_cookbook(cookbook, image, request)
        return res


class ChefController(object):
    """
    Chef Controller Object
    Implements Application logic
    """

    @staticmethod
    def validate(request, body):
        """ Validate the given cookbook
        :param request: request context
        :param body: a json with deployment parameters
        :return : a json file with process results
        """
        body = body or {}
        if len(body) < 1:
            raise exc.HTTPBadRequest(_("No action specified"))
        try:
            cookbook = body['cookbook']
            image = body['image']
        except KeyError:
            raise exc.HTTPBadRequest(_("Insufficient payload"))

        LOG.info(_LI('Processing Request for cookbook %s, image %s' % (cookbook, image)))
        res = ValidateEngine().validate_chef_cookbook(cookbook, image, request)
        return res


def create_chef_resource():
    """
    Actions action factory method.
    """
    deserializer = validator.common.utils.JSONDeserializer()
    serializer = validator.common.utils.JSONSerializer()
    return wsgi.Resource(ChefController(), deserializer, serializer)


def create_puppet_resource():
    """
    Actions action factory method.
    """
    deserializer = validator.common.utils.JSONDeserializer()
    serializer = validator.common.utils.JSONSerializer()
    return wsgi.Resource(PuppetController(), deserializer, serializer)
