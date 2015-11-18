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

from __future__ import unicode_literals
from oslo_log import log as logging
from oslo_config import cfg
from validator.clients.puppet_client import PuppetClient
from validator.clients.chef_client import ChefClient
LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ValidateEngine(object):
    """Engine for validations"""

    @staticmethod
    def validate_chef_cookbook(cookbook, image, request):
        """
        Cookbook validation
        :param image: name of the image to deploy
        :param cookbook: name of the cookbook to validate
        :param request: request context
        :return:
        """
        res = None
        # process request based on configuration options
        if hasattr(CONF, 'clients_docker') \
                and hasattr(CONF.clients_docker, 'url') \
                and len(CONF.clients_docker.url) > 1:

            # use direct docker connection, fast and simple
            d = ChefClient()
            res = d.cookbook_deployment_test(cookbook, image)
        return res

    @staticmethod
    def validate_puppet_cookbook(cookbook, image, request):
        """
        Cookbook validation
        :param image: name of the image to deploy
        :param cookbook: name of the cookbook to validate
        :param request: request context
        :return:
        """
        res = None
        # process request based on configuration options
        if hasattr(CONF, 'clients_docker') \
                and hasattr(CONF.clients_docker, 'url') \
                and len(CONF.clients_docker.url) > 1:
            # use direct docker connection, fast and simple
            d = PuppetClient()
            res = d.cookbook_deployment_test(cookbook, image)
        return res
