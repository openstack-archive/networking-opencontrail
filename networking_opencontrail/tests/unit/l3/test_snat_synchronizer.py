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

import logging
import mock

from networking_opencontrail.l3 import snat_synchronizer

from neutron.tests.unit.extensions import base as test_extensions_base


class TungstenFabricSNATTestCases(test_extensions_base.ExtensionTestCase):
    def setUp(self):
        super(TungstenFabricSNATTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

        self.tf_helper = self._get_tf_helper()

        self.rest_driver_mock = RestDriverMock()
        self.tf_helper.rest_driver = self.rest_driver_mock

    def tearDown(self):
        super(TungstenFabricSNATTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_get_snat_ips(self):
        snat_ips = self.tf_helper.get_snat_ips(
            '9e824605-64b4-4f29-bbbb-4a537dea9f4c')

        self.assertIn('10.10.10.10', snat_ips)
        self.assertNotIn('10.10.10.11', snat_ips)

    @mock.patch("retrying.time.sleep")
    def test_retry_get_snat_ips(self, _):
        self.rest_driver_mock.exceptions = [KeyError()]

        snat_ips = self.tf_helper.get_snat_ips(
            '9e824605-64b4-4f29-bbbb-4a537dea9f4c')

        self.assertIn('10.10.10.10', snat_ips)
        self.assertNotIn('10.10.10.11', snat_ips)

    @mock.patch("retrying.time.sleep")
    def test_max_attempt_get_snat_ips(self, _):
        self.rest_driver_mock.exceptions = [KeyError()] * 4

        snat_ips = self.tf_helper.get_snat_ips(
            '9e824605-64b4-4f29-bbbb-4a537dea9f4c')

        self.assertEqual(snat_ips, [])

    @mock.patch("networking_opencontrail.drivers.drv_opencontrail.cfg")
    def _get_tf_helper(self, cfg):
        cfg.CONF.APISERVER.use_ssl = False
        cfg.CONF.APISERVER.insecure = True
        cfg.CONF.APISERVER.cafile = None
        return snat_synchronizer.TFHelper()


class SnatSynchronizerTestCases(test_extensions_base.ExtensionTestCase):
    def setUp(self):
        super(SnatSynchronizerTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

        self.snat_sync = self._get_snat_synchronizer()
        self.neutron = mock.Mock()
        self.tf = mock.Mock()
        self.snat_sync.neutron_helper = self.neutron
        self.snat_sync.tf_helper = self.tf

        self.context = mock.Mock()
        self.router = {'id': '9e824605-64b4-4f29-bbbb-4a537dea9f4c',
                       'external_gateway_info': mock.Mock()}

    def tearDown(self):
        super(SnatSynchronizerTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_create_snat_interface(self):
        self.tf.get_snat_ips.return_value = ['10.10.10.10']
        self.neutron.get_snat_interfaces.return_value = []

        self.snat_sync.sync_snat_interfaces(self.context,
                                            self.router['id'],
                                            self.router)

        self.neutron.create_snat_interface.assert_called_once_with(
            self.context,
            self.router['external_gateway_info'],
            self.router['id'],
            '10.10.10.10'
        )

    def test_remove_snat_interface(self):
        snat_interface = {'fixed_ips': [{'ip_address': '10.10.10.10'}]}
        self.neutron.get_snat_interfaces.return_value = [snat_interface]
        self.tf.get_snat_ips.return_value = []

        self.snat_sync.sync_snat_interfaces(self.context,
                                            self.router['id'],
                                            self.router)

        self.neutron.delete_snat_interface.assert_called_once_with(
            self.context, snat_interface)

    @mock.patch("networking_opencontrail.drivers.drv_opencontrail.cfg")
    def _get_snat_synchronizer(self, cfg):
        cfg.CONF.APISERVER.use_ssl = False
        cfg.CONF.APISERVER.insecure = True
        cfg.CONF.APISERVER.cafile = None
        snat_sync = snat_synchronizer.SnatSynchronizer()
        return snat_sync


class RestDriverMock(object):
    def __init__(self):
        self._exceptions = iter([])

    def get_resource(self, res_type, query, id):
        if res_type != 'logical-router':
            try:
                raise next(self._exceptions)
            except StopIteration:
                pass
        return self._get_resource(res_type, query, id)

    def _get_resource(self, res_type, query, id):
        resource_infos = {
            'logical-router': self._get_router_rest(),
            'service-instance': self._get_service_instance_rest(),
            'virtual-machine': self._get_virtual_machine_rest(),
            'virtual-machine-interface':
                self._get_virtual_machine_interface_rest(id),
            'instance-ip': self._get_instance_ip(id),
        }
        content = resource_infos.get(res_type, {})
        status_code = 200
        return status_code, content

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
            'virtual_machine_interface_back_refs': [
                {'uuid': '0f716eb5-2820-4edc-921d-bdd6f8670733'},
                {'uuid': 'fb33517f-eddb-4a4b-bf54-05226a0956c9'}
            ]}
        }

    @staticmethod
    def _get_virtual_machine_interface_rest(uuid):
        interfaces = {
            '0f716eb5-2820-4edc-921d-bdd6f8670733': {
                'virtual-machine-interface': {
                    'instance_ip_back_refs': [{
                        'uuid': 'a905c5e1-7564-44bb-9edc-436caad7d7a2'
                    }],
                    'virtual_machine_interface_properties': {
                        'service_interface_type': 'right',
                    }
                }},
            'fb33517f-eddb-4a4b-bf54-05226a0956c9': {
                'virtual-machine-interface': {
                    'instance_ip_back_refs': [{
                        'uuid': 'af32f3d9-708e-444b-b0dc-3ed3a60d4e8a'
                    }],
                    'virtual_machine_interface_properties': {
                        'service_interface_type': 'left',
                    }
                }},
        }
        return interfaces.get(uuid)

    @staticmethod
    def _get_instance_ip(uuid):
        ips = {
            'a905c5e1-7564-44bb-9edc-436caad7d7a2': {
                'instance-ip': {
                    'instance_ip_address': '10.10.10.10',
                }},
            'af32f3d9-708e-444b-b0dc-3ed3a60d4e8a': {
                'instance-ip': {
                    'instance_ip_address': '10.10.10.11',
                }},
        }
        return ips.get(uuid)

    @property
    def exceptions(self):
        return [exc for exc in self._exceptions]

    @exceptions.setter
    def exceptions(self, exceptions):
        self._exceptions = iter(exceptions)
