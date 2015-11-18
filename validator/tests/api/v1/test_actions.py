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
""" Tests for validator.api.v1.actions """
from __future__ import unicode_literals

import mock
from validator.api.v1.actions import ValidateController

from validator.tests.base import ValidatorTestCase


class ValidateControllerTestCase(ValidatorTestCase):
    """ Tests for class ValidateController """

    def setUp(self):
        """ Create a ValidateController instance """
        super(ValidateControllerTestCase, self).setUp()
        self.item = ValidateController()


    def test_validate(self):
        """ Tests for method validate """
        self.item.external = mock.MagicMock()
        input = "MyInput"
        expected = "OK"
        self.item.external.return_value = "OK"
        observed = self.item.validate(input)
        self.assertEqual(expected, observed)

    def tearDown(self):
        """ Cleanup the ValidateController instance """
        super(ValidateControllerTestCase, self).tearDown()
        self.m.UnsetStubs()
        self.m.ResetAll()
