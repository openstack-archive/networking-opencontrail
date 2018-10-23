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
import six

from neutron.tests.unit.extensions import base as test_extensions_base
from neutron_lib.plugins import constants

from networking_opencontrail.l3 import opencontrail_rt_callback
from networking_opencontrail.l3.tungstenfabric_api import \
    TungstenFabricApiConnector


def get_mock_network_operation_context():
    current = {'status': 'ACTIVE',
               'subnets': [],
               'name': 'net1',
               'provider:physical_network': None,
               'admin_state_up': True,
               'tenant_id': 'test-tenant',
               'provider:network_type': 'local',
               'router:external': False,
               'shared': False,
               'id': 'd897e21a-dfd6-4331-a5dd-7524fa421c3e',
               'provider:segmentation_id': None}
    context = mock.Mock(current=current)
    return context


class L3OpenContrailTestCases(test_extensions_base.ExtensionTestCase):
    """Main test cases for ML2 mechanism driver for OpenContrail.

    Tests all ML2 API supported by OpenContrail. It invokes the back-end
    driver APIs as they would normally be invoked by the driver.
    """

    def setUp(self):
        super(L3OpenContrailTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(L3OpenContrailTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @staticmethod
    def _get_router_test():
        router_id = "234237d4-1e7f-11e5-9bd7-080027328c3a"
        router = {'router': {'name': 'router1', 'admin_state_up': True,
                             'tenant_id': router_id,
                             'project_id': router_id,
                             'external_gateway_info': None}}
        return router_id, router

    @staticmethod
    def _get_interface_info():
        interface_info = {
            "subnet_id": "a2f1f29d-571b-4533-907f-5803ab96ead1",
            "port_id": "3a44f4e5-1694-493a-a1fb-393881c673a4"
        }

        return interface_info

    @staticmethod
    def _get_floating_ip():
        floatingip = {
            'floatingip': {
                'id': 'a2f1f29d-571b-4533-907f-5803ab96ead1',
            },
        }

        return floatingip

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    def test_get_plugin_type(self, _, cfg):
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        type = hook.get_plugin_type()

        self.assertEqual(constants.L3, type, "Wrong plugin type")

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    def test_get_plugin_description(self, _, cfg):
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        description = hook.get_plugin_description()

        self.assertIsInstance(description, six.string_types)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.l3_gwmode_db.L3_NAT_db_mixin.create_router")
    def test_create_router(self, l3_nat, driver, cfg):
        router_id, router = self._get_router_test()
        context = get_mock_network_operation_context()
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()
        new_router = router
        new_router['id'] = router_id

        with mock.patch.object(hook, '_sync_snat_interfaces'):
            hook.create_router(context, router)

        hook.driver.create_router.assert_called_with(context, router)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.l3_gwmode_db.L3_NAT_db_mixin.delete_router")
    def test_delete_router(self, l3_nat, driver, cfg):
        router_id, _ = self._get_router_test()
        context = get_mock_network_operation_context()
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        hook.delete_router(context, router_id)

        hook.driver.delete_router.assert_called_with(context, router_id)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.extraroute_db.ExtraRoute_db_mixin.update_router")
    def test_update_router(self, extra_route, driver, cfg):
        router_id, router = self._get_router_test()
        context = get_mock_network_operation_context()
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        with mock.patch.object(hook, '_sync_snat_interfaces'):
            hook.update_router(context, router_id, router)

        hook.driver.update_router.assert_called_with(context, router_id,
                                                     router)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.l3_gwmode_db.L3_NAT_db_mixin."
                "add_router_interface")
    def test_add_router_interface(self, l3_nat, driver, cfg):
        router_id, _ = self._get_router_test()
        interface_info = self._get_interface_info()
        context = get_mock_network_operation_context()
        l3_nat.return_value = interface_info
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        hook.add_router_interface(context, router_id, interface_info)

        hook.driver.add_router_interface.assert_called_with(context,
                                                            router_id,
                                                            mock.ANY)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.l3_gwmode_db.L3_NAT_db_mixin."
                "remove_router_interface")
    def test_remove_router_interface(self, l3_nat, driver, cfg):
        router_id, _ = self._get_router_test()
        interface_info = self._get_interface_info()
        context = get_mock_network_operation_context()
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        hook.remove_router_interface(context, router_id, interface_info)

        hook.driver.remove_router_interface.assert_called_with(context,
                                                               router_id,
                                                               interface_info)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.l3_dvr_db.L3_NAT_with_dvr_db_mixin."
                "create_floatingip")
    def test_create_floatingip(self, l3_nat, driver, cfg):
        context = get_mock_network_operation_context()
        floatingip = self._get_floating_ip()
        l3_nat.return_value = floatingip
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        hook.create_floatingip(context, floatingip)

        l3_nat.assert_called_with(context, mock.ANY, mock.ANY)
        hook.driver.create_floatingip.assert_called_with(context,
                                                         mock.ANY)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.l3_dvr_db.L3_NAT_with_dvr_db_mixin."
                "get_floatingip")
    @mock.patch("neutron.db.l3_dvr_db.L3_NAT_with_dvr_db_mixin."
                "update_floatingip")
    @mock.patch("neutron.db.l3_dvr_db.L3_NAT_with_dvr_db_mixin."
                "update_floatingip_status")
    def test_update_floatingip(self, l3_nat, l3_get, driver, driver2, cfg):
        context = get_mock_network_operation_context()
        floatingip = self._get_floating_ip()
        l3_nat.return_value = floatingip
        l3_get.return_value = floatingip['floatingip']
        fip_id = floatingip['floatingip']['id']
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        hook.update_floatingip(context, fip_id, floatingip)

        l3_nat.assert_called_with(context, mock.ANY, mock.ANY)
        hook.driver.update_floatingip.assert_called_with(context,
                                                         fip_id,
                                                         mock.ANY)

    @mock.patch("networking_opencontrail.l3.tungstenfabric_api.cfg")
    @mock.patch("networking_opencontrail.drivers.drv_opencontrail."
                "OpenContrailDrivers")
    @mock.patch("neutron.db.l3_dvr_db.L3_NAT_with_dvr_db_mixin."
                "get_floatingip")
    @mock.patch("neutron.db.l3_dvr_db.L3_NAT_with_dvr_db_mixin."
                "delete_floatingip")
    def test_delete_floatingip(self, l3_nat, l3_get, driver, cfg):
        context = get_mock_network_operation_context()
        floatingip = self._get_floating_ip()
        l3_nat.return_value = floatingip
        l3_get.return_value = floatingip['floatingip']
        fip_id = floatingip['floatingip']['id']
        hook = opencontrail_rt_callback.OpenContrailRouterHandler()

        hook.delete_floatingip(context, fip_id)

        l3_nat.assert_called_with(context, fip_id)
        hook.driver.delete_floatingip.assert_called_with(context,
                                                         fip_id)


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
            resource_infos.get(resource_type, {}).get(resource_type, {})
        )
        response.status_code = 200
        return response

    @staticmethod
    def _get_router_rest():
        return {
            'logical-router':
                {
                    'service_instance_refs': [
                        {
                            'uuid': '32adb91e-3e32-4064-a3cf-c4e631a247a3',
                            'to': ['snat_'],
                        }
                    ]
                }
        }

    @staticmethod
    def _get_service_instance_rest():
        return {
            'service-instance':
                {
                    'virtual_machine_back_refs': [
                        {'uuid': 'cde8f476-8342-4792-b020-82b40446b18a'},
                    ]
                }
        }

    @staticmethod
    def _get_virtual_machine_rest():
        return {
            'virtual-machine':
                {
                    'virtual_machine_interface_back_refs': [
                        {'uuid': '0f716eb5-2820-4edc-921d-bdd6f8670733'},
                    ]
                }
        }

    @staticmethod
    def _get_virtual_machine_interface_rest():
        return {
            'virtual-machine-interface':
                {
                    'instance_ip_back_refs': [
                        {'uuid': 'a905c5e1-7564-44bb-9edc-436caad7d7a2'},
                    ],
                    'virtual_machine_interface_properties': {
                        'service_interface_type': 'right',
                    }
                }
        }

    @staticmethod
    def _get_instance_ip():
        return {
            'instance-ip':
                {
                    'instance_ip_address': '10.10.10.10',
                }
        }

    @mock.patch("networking_opencontrail.drivers.drv_opencontrail.cfg")
    @mock.patch("networking_opencontrail.drivers.rest_driver.requests")
    def test_get_snat_ips(self, requests, cfg):
        cfg.CONF.APISERVER.api_server_ip = '127.0.0.1'
        cfg.CONF.APISERVER.api_server_port = 8082
        cfg.CONF.APISERVER.use_ssl = False
        cfg.CONF.APISERVER.insecure = True
        cfg.CONF.APISERVER.cafile = None
        requests.get.side_effect = self._get_rest_response
        tf_api = TungstenFabricApiConnector()

        snat_ips = tf_api.get_snat_ips('9e824605-64b4-4f29-bbbb-4a537dea9f4c')

        self.assertIn('10.10.10.10', snat_ips)
