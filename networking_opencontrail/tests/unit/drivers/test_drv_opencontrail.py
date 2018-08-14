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

import json
import logging
import mock
import requests

from neutron.tests.unit.extensions import base as test_extensions_base
from neutron_lib.constants import ATTR_NOT_SPECIFIED
from neutron_lib import exceptions

from networking_opencontrail.drivers import drv_opencontrail


class ApiRequestsTestCases(test_extensions_base.ExtensionTestCase):

    def setUp(self):
        super(ApiRequestsTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(ApiRequestsTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    def _get_driver(self, options, config):
        config.APISERVER = mock.MagicMock(api_server_ip="localhost",
                                          use_ssl=False,
                                          cafile=None,
                                          api_server_port="8082")
        config.auth_strategy = 'keystone'
        config.keystone_authtoken = mock.MagicMock(cafile=None)

        return drv_opencontrail.OpenContrailDrivers()

    @mock.patch("requests.post")
    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_request_api_server_authorized(self, options, config, request):
        driver = self._get_driver(options, config)
        driver._apiinsecure = True
        response = requests.Response()
        response.status_code = requests.codes.ok
        request.return_value = response
        url = "/URL"

        result = driver._request_api_server(url)

        self.assertEqual(response, result)

        request.assert_called_with(url, data=None, headers=mock.ANY,
                                   verify=False)

    @mock.patch("requests.post")
    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_request_api_server_auth_failed(self, options, config, request):
        driver = self._get_driver(options, config)
        driver._apiinsecure = False
        driver._use_api_certs = False
        response = requests.Response()
        response.status_code = requests.codes.unauthorized
        request.return_value = response
        url = "/URL"

        self.assertRaises(RuntimeError, driver._request_api_server, url)

    @mock.patch("requests.Response.text", new_callable=mock.PropertyMock)
    @mock.patch("requests.post")
    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_request_api_server_auth_recover(self, options, config, request,
                                             text):
        driver = self._get_driver(options, config)
        driver._apiinsecure = False
        driver._use_api_certs = False
        response_bad = requests.Response()
        response_bad.status_code = requests.codes.unauthorized
        token = "xyztoken"
        text.return_value = json.dumps({
            'access': {
                'token': {
                    'id': token
                },
            },
        })
        response_good = requests.Response()
        response_good.status_code = requests.codes.ok
        request.side_effect = [response_bad, response_good, response_good]
        url = "/URL"

        driver._request_api_server(url)

        request.assert_called_with('/URL', data=None,
                                   headers={'X-AUTH-TOKEN': token})

    @mock.patch("requests.post")
    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_request_api_server_authn(self, options, config, request):
        driver = self._get_driver(options, config)
        driver._apiinsecure = True
        response = requests.Response()
        response.status_code = requests.codes.ok
        request.return_value = response
        url = "/URL"

        result = driver._request_api_server_authn(url)

        self.assertEqual(response, result)

        request.assert_called_with(url, data=None, headers=mock.ANY,
                                   verify=False)

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_relay_request(self, options, config):
        driver = self._get_driver(options, config)
        driver._apiserverconnect = "API"
        driver._request_api_server_authn = mock.MagicMock()
        response = 404
        driver._request_api_server_authn.return_value = response

        result = driver._relay_request("/URL")

        self.assertEqual(response, result)
        url = "API://localhost:8082/URL"
        driver._request_api_server_authn.assert_called_with(url,
                                                            data=None,
                                                            headers=mock.ANY)

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_request_backend(self, options, config):
        driver = self._get_driver(options, config)
        driver._relay_request = mock.MagicMock()
        response = requests.Response()
        response.status_code = requests.codes.ok
        driver._relay_request.return_value = response

        context = mock.MagicMock()
        data_dict = {}
        obj_name = 'object'
        action = 'TEST'

        code, message = driver._request_backend(context, data_dict, obj_name,
                                                action)

        self.assertEqual(requests.codes.ok, code)
        self.assertEqual({'message': None}, message)
        driver._relay_request.assert_called()

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_encode_resource(self, options, config):
        driver = self._get_driver(options, config)
        resource_id = "resource-id"
        resource = {'data': 'nothing'}

        result = driver._encode_resource(resource_id, resource)

        expected = {
            'fields': None,
            'id': 'resource-id',
            'filters': None,
            'resource': resource,
        }
        self.assertEqual(expected, result)

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_transform_response_dict(self, options, config):
        driver = self._get_driver(options, config)
        code = requests.codes.ok
        info = {'id': 'field-1234'}
        fields = ['text']

        result = driver._transform_response(code, info, fields=fields)

        self.assertEqual({}, result)

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_transform_response_list(self, options, config):
        driver = self._get_driver(options, config)
        code = requests.codes.ok
        info = [{'id': 'field-1234'}]
        fields = []

        result = driver._transform_response(code, info, fields=fields)

        self.assertEqual(info, result)

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_transform_response_error(self, options, config):
        driver = self._get_driver(options, config)
        code = requests.codes.unauthorized
        info = {
            'exception': 'TenantIdProjectIdFilterConflict',
        }

        self.assertRaises(exceptions.TenantIdProjectIdFilterConflict,
                          driver._transform_response,
                          code, info)


class ApiCrudTestCases(test_extensions_base.ExtensionTestCase):

    def setUp(self):
        super(ApiCrudTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(ApiCrudTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    def _get_driver(self, options, config):
        config.APISERVER = mock.MagicMock(api_server_ip="localhost",
                                          use_ssl=False,
                                          cafile=None,
                                          api_server_port="8082")
        config.auth_strategy = 'keystone'
        config.keystone_authtoken = mock.MagicMock(cafile=None)

        return drv_opencontrail.OpenContrailDrivers()

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_create_resource(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'network'
        res_data = {
            'id': 'network-123',
            'tenant_id': ATTR_NOT_SPECIFIED,
        }
        driver._request_backend.return_value = (status_code, res_data)

        response = driver._create_resource(res_type,
                                           context,
                                           {res_type: res_data})

        self.assertEqual(response, res_data)
        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'CREATE')

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_get_resource(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'network'
        res_data = {
            'id': 'network-123',
        }
        fields = ['id']
        driver._request_backend.return_value = (status_code, res_data)

        response = driver._get_resource(res_type,
                                        context, res_data['id'], fields)

        self.assertEqual(response, res_data)
        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'READ')

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_update_resource(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'network'
        res_data = {
            'id': 'network-123',
        }
        driver._request_backend.return_value = (status_code, res_data)

        response = driver._update_resource(res_type, context, res_data['id'],
                                           {res_type: res_data})

        self.assertEqual(response, res_data)
        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'UPDATE')

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_delete_resource(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'network'
        res_data = {
            'id': 'network-123',
        }
        driver._request_backend.return_value = (status_code, res_data)

        driver._delete_resource(res_type, context, res_data['id'])

        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'DELETE')

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_list_resource(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'network'
        res_data = {
            'id': 'network-123',
        }
        fields = ['id']
        driver._request_backend.return_value = (status_code, [res_data])

        response = driver._list_resource(res_type, context, None, fields)

        self.assertEqual(response, [res_data])
        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'READALL')

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_count_resource(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'network'
        result = {'count': 0}
        driver._request_backend.return_value = (status_code, result)

        response = driver._count_resource(res_type, context, None)

        self.assertEqual(response, result)
        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'READCOUNT')

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_add_router_interface(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'router'
        res_data = {
            'id': 'router-123',
        }
        res_id = res_data['id']
        driver._request_backend.return_value = (status_code, res_data)

        response = driver.add_router_interface(context, res_id, res_data)

        self.assertEqual(response, res_data)
        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'ADDINTERFACE')

    @mock.patch("oslo_config.cfg.CONF")
    @mock.patch("oslo_config.cfg.CONF.register_opts")
    def test_remove_router_interface(self, options, config):
        driver = self._get_driver(options, config)
        driver._request_backend = mock.MagicMock()
        status_code = requests.codes.ok
        context = mock.MagicMock()
        res_type = 'router'
        res_data = {
            'id': 'router-123',
        }
        res_id = res_data['id']
        driver._request_backend.return_value = (status_code, res_data)

        response = driver.remove_router_interface(context, res_id, res_data)

        self.assertEqual(response, res_data)
        driver._request_backend.assert_called_with(context, mock.ANY,
                                                   res_type, 'DELINTERFACE')
