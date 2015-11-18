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

"""
Validator API Server. An OpenStack ReST API to Validate Chef Cookbooks.
"""

from __future__ import unicode_literals
import os
import sys

import six
import oslo_i18n as i18n
from oslo_log import log as logging

from validator.common.i18n import _LI
from validator.common import config
from validator.common import wsgi


# If ../validator/__init__.py exists, add ../ to Python search path,
# so that it will override what happens to be installed in
# /usr/(local/)lib/python...
root = os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, os.pardir)
if os.path.exists(os.path.join(root, 'validator', '__init__.py')):
    sys.path.insert(0, root)

i18n.enable_lazy()

LOG = logging.getLogger()
CONF = config.CONF

if __name__ == '__main__':
    try:
        logging.register_options(CONF)
        config.parse_args()
        logging.setup(CONF, 'validator_api')

        app = config.load_paste_app("validator_api")
        port, host = (CONF.bind_port, CONF.bind_host)
        LOG.info(_LI('Starting Chef Validator ReST API on %(host)s:%(port)s'),
                 {'host': host, 'port': port})
        server = wsgi.Service(app, port, host)
        server.start()
        server.wait()
    except RuntimeError as e:
        msg = six.text_type(e)
        sys.exit("ERROR: %s" % msg)
