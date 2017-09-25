# Copyright (c) 2017 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import logging
import mock
import requests

from neutron.tests.unit.extensions import base as test_extensions_base

from networking_opencontrail.common import utils


class UtilsTestCases(test_extensions_base.ExtensionTestCase):
    """Main test cases for ML2 mechanism driver for OpenContrail.

    Tests all ML2 API supported by OpenContrail. It invokes the back-end
    driver APIs as they would normally be invoked by the driver.
    """

    def setUp(self):
        super(UtilsTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(UtilsTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_register_vnc_api_options(self, register):
        utils.register_vnc_api_options()

        register.assert_called_with(mock.ANY, 'APISERVER')

    @mock.patch("requests.get")
    @mock.patch("oslo_config.cfg.CONF")
    def test_vnc_api_is_authenticated_ok(self, config, request):
        config.APISERVER = mock.MagicMock()
        config.APISERVER.use_ssl = False
        config.APISERVER.api_server_ip = "localhost"
        config.APISERVER.api_server_port = "8082"
        response = requests.Response()
        response.status_code = requests.codes.ok
        request.return_value = response

        result = utils.vnc_api_is_authenticated()

        request.assert_called_with(mock.ANY)
        self.assertEqual(False, result)

    @mock.patch("requests.get")
    @mock.patch("oslo_config.cfg.CONF")
    def test_vnc_api_is_authenticated_unauthorized(self, config, request):
        config.APISERVER = mock.MagicMock()
        config.APISERVER.use_ssl = False
        config.APISERVER.api_server_ip = "localhost"
        config.APISERVER.api_server_port = "8082"
        response = requests.Response()
        response.status_code = requests.codes.unauthorized
        request.return_value = response

        result = utils.vnc_api_is_authenticated()

        request.assert_called_with(mock.ANY)
        self.assertEqual(True, result)

    @mock.patch("requests.get")
    @mock.patch("oslo_config.cfg.CONF")
    def test_vnc_api_is_authenticated_invalid(self, config, request):
        config.APISERVER = mock.MagicMock()
        config.APISERVER.use_ssl = True
        config.APISERVER.api_server_ip = "localhost"
        config.APISERVER.api_server_port = "8082"
        response = requests.Response()
        response.status_code = requests.codes.server_error
        request.return_value = response

        self.assertRaises(requests.exceptions.HTTPError,
                          utils.vnc_api_is_authenticated)

        request.assert_called_with(mock.ANY)
