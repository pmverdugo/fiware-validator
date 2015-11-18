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
""" Tests for validator.engine.validate """
from __future__ import unicode_literals

import mock
from validator.engine.validate import ValidateEngine

from validator.tests.base import ValidatorTestCase


class ValidateEngineTestCase(ValidatorTestCase):
    """ Tests for class ValidateEngine """

    def setUp(self):
        """ Create a ValidateEngine instance """
        super(ValidateEngineTestCase, self).setUp()
        self.item = ValidateEngine()


    def test_validate_cookbook(self):
        """ Tests for method validate_cookbook """
        self.item.external = mock.MagicMock()
        input = "MyInput"
        expected = "OK"
        self.item.external.return_value = "OK"
        observed = self.item.validate_cookbook(input)
        self.assertEqual(expected, observed)

    def tearDown(self):
        """ Cleanup the ValidateEngine instance """
        super(ValidateEngineTestCase, self).tearDown()
        self.m.UnsetStubs()
        self.m.ResetAll()
