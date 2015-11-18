#!/usr/bin/env python
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
""" Tests for validator.api.middleware.ssl """
from __future__ import unicode_literals

import mock
from validator.api.middleware.ssl import SSLMiddleware

from validator.tests.base import ValidatorTestCase


class SSLMiddlewareTestCase(ValidatorTestCase):
    """ Tests for class SSLMiddleware """

    def setUp(self):
        """ Create a SSLMiddleware instance """
        super(SSLMiddlewareTestCase, self).setUp()
        self.item = SSLMiddleware()


    def test_process_request(self):
        """ Tests for method process_request """
        self.item.external = mock.MagicMock()
        input = "MyInput"
        expected = "OK"
        self.item.external.return_value = "OK"
        observed = self.item.process_request(input)
        self.assertEqual(expected, observed)

    def tearDown(self):
        """ Cleanup the SSLMiddleware instance """
        super(SSLMiddlewareTestCase, self).tearDown()
        self.m.UnsetStubs()
        self.m.ResetAll()
