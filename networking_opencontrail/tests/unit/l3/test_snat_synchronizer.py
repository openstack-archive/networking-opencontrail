# Copyright (c) 2019 OpenStack Foundation
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

from networking_opencontrail.l3.snat_synchronizer import TungstenFabricHelper

from neutron.tests.unit.extensions import base as test_extensions_base


class TungstenFabricSNATTestCases(test_extensions_base.ExtensionTestCase):
    def setUp(self):
        super(TungstenFabricSNATTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(TungstenFabricSNATTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    def _get_rest_response(self, url, **request):
        response = mock.Mock()
        resource_type = url.split('/')[-2]
        resource_infos = {
            'logical-router': self._get_router_rest(),
            'service-instance': self._get_service_instance_rest(),
            'virtual-machine': self._get_virtual_machine_rest(),
            'virtual-machine-interface':
                self._get_virtual_machine_interface_rest(),
            'instance-ip': self._get_instance_ip(),
        }
        response.json.return_value = resource_infos.get(resource_type, {})
        response.text = json.dumps(
            resource_infos.get(resource_type, {})
        )
        response.status_code = 200
        return response

    @staticmethod
    def _get_router_rest():
        return {'logical-router': {
            'service_instance_refs': [{
                'uuid': '32adb91e-3e32-4064-a3cf-c4e631a247a3',
                'to': ['snat_'],
            }]
        }}

    @staticmethod
    def _get_service_instance_rest():
        return {'service-instance': {
            'virtual_machine_back_refs': [{
                'uuid': 'cde8f476-8342-4792-b020-82b40446b18a',
            }]
        }}

    @staticmethod
    def _get_virtual_machine_rest():
        return {'virtual-machine': {
            'virtual_machine_interface_back_refs': [{
                'uuid': '0f716eb5-2820-4edc-921d-bdd6f8670733',
            }]
        }}

    @staticmethod
    def _get_virtual_machine_interface_rest():
        return {'virtual-machine-interface': {
            'instance_ip_back_refs': [{
                'uuid': 'a905c5e1-7564-44bb-9edc-436caad7d7a2'
            }],
            'virtual_machine_interface_properties': {
                'service_interface_type': 'right',
            }
        }}

    @staticmethod
    def _get_instance_ip():
        return {'instance-ip': {
            'instance_ip_address': '10.10.10.10',
        }}

    @mock.patch("networking_opencontrail.drivers.drv_opencontrail.cfg")
    @mock.patch("networking_opencontrail.drivers.rest_driver.requests")
    def test_get_snat_ips(self, requests, cfg):
        cfg.CONF.APISERVER.use_ssl = False
        cfg.CONF.APISERVER.insecure = True
        cfg.CONF.APISERVER.cafile = None
        requests.get.side_effect = self._get_rest_response
        tf_helper = TungstenFabricHelper()

        snat_ips = tf_helper.get_snat_ips(
            '9e824605-64b4-4f29-bbbb-4a537dea9f4c')

        self.assertIn('10.10.10.10', snat_ips)
        self.assertNotIn('10.10.10.11', snat_ips)

    # TODO: We need to check if this method not only properly get snat IPs,
    #  but also get all of them and not get any other IPs,
    #  so I propose to add an not-snat IP (other vmi, vm, etc.) in mocked
    #  responses an test it here or make another negative test.

    @mock.patch("networking_opencontrail.drivers.drv_opencontrail.cfg")
    @mock.patch("networking_opencontrail.drivers.rest_driver.requests")
    def test_retry_get_snat_ips(self, requests, cfg):
        cfg.CONF.APISERVER.use_ssl = False
        cfg.CONF.APISERVER.insecure = True
        cfg.CONF.APISERVER.cafile = None
        exceptions = iter([KeyError()])

        def side_effect(*args, **kwargs):
            if 'logical-router' in args[0]:
                return self._get_rest_response(*args, **kwargs)
            try:
                raise next(exceptions)
            except StopIteration:
                return self._get_rest_response(*args, **kwargs)

        requests.get.side_effect = side_effect
        tf_helper = TungstenFabricHelper()

        snat_ips = tf_helper.get_snat_ips(
            '9e824605-64b4-4f29-bbbb-4a537dea9f4c')

        self.assertIn('10.10.10.10', snat_ips)
