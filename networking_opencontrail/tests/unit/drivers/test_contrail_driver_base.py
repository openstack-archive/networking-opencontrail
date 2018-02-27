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

from neutron.common import exceptions as neutron_exc
from neutron.extensions import securitygroup
from neutron.tests.unit.extensions import base as test_extensions_base
from neutron_lib import exceptions
from neutron_lib.constants import ATTR_NOT_SPECIFIED
from neutron_lib.exceptions import allowedaddresspairs
from neutron_lib.exceptions import l3

from networking_opencontrail.common.exceptions import HttpResponseError
from networking_opencontrail.drivers import contrail_driver_base as base


class ErrorTestCases(test_extensions_base.ExtensionTestCase):

    def setUp(self):
        super(ErrorTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(ErrorTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    def _get_info(self, exception=None, msg='error'):
        return {
            'exception': exception,
            'msg': msg,
        }

    def test_raise_contrail_error(self):
        info = self._get_info()

        self.assertRaises(exceptions.NeutronException,
                          base._raise_contrail_error,
                          info, None)

    def test_raise_contrail_error_bad_request(self):
        info = self._get_info('BadRequest')

        self.assertRaises(exceptions.NeutronException,
                          base._raise_contrail_error,
                          info, None)

    def test_raise_contrail_error_vrouter(self):
        info = self._get_info('VirtualRouterNotFound')

        self.assertRaises(HttpResponseError,
                          base._raise_contrail_error,
                          info, None)

    def test_raise_contrail_error_neutron(self):
        info = self._get_info('SubnetPoolNotFound')
        info['subnetpool_id'] = "123chips"

        self.assertRaises(neutron_exc.SubnetPoolNotFound,
                          base._raise_contrail_error,
                          info, None)

    def test_raise_contrail_error_l3(self):
        info = self._get_info('RouterNotFound')
        info['router_id'] = "router"

        self.assertRaises(l3.RouterNotFound,
                          base._raise_contrail_error,
                          info, None)

    def test_raise_contrail_error_securitygroup(self):
        info = self._get_info('SecurityGroupInUse')
        info['id'] = "sg_id"

        self.assertRaises(securitygroup.SecurityGroupInUse,
                          base._raise_contrail_error,
                          info, None)

    def test_raise_contrail_error_allowedaddresspairs(self):
        info = self._get_info('AllowedAddressPairExhausted')
        info['quota'] = "255"

        self.assertRaises(allowedaddresspairs.AllowedAddressPairExhausted,
                          base._raise_contrail_error,
                          info, None)

    def test_raise_contrail_error_strange(self):
        info = self._get_info('VeryStrangeUnknownException')

        self.assertRaises(exceptions.NeutronException,
                          base._raise_contrail_error,
                          info, None)


class NetworkTestCases(test_extensions_base.ExtensionTestCase):

    RESOURCE_NAME = 'network'

    def setUp(self):
        super(NetworkTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(NetworkTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("networking_opencontrail.common.utils."
                "register_vnc_api_options")
    def _get_drv(self, options):
        return base.OpenContrailDriversBase()

    def test_create_network(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        network = "MockNetwork"
        context = mock.Mock()
        drv._create_resource.return_value = network

        result = drv.create_network(context, network)

        self.assertEqual(result, network)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                network)

    def test_get_network(self):
        drv = self._get_drv()
        drv._get_resource = mock.Mock()
        network = "MockNetwork"
        context = mock.Mock()
        drv._get_resource.return_value = network

        result = drv.get_network(context, network)

        self.assertEqual(result, network)
        drv._get_resource.assert_called_with(self.RESOURCE_NAME, context,
                                             network, None)

    def test_delete_network(self):
        drv = self._get_drv()
        drv._delete_resource = mock.Mock()
        network = "MockNetwork"
        context = mock.Mock()

        drv.delete_network(context, network)

        drv._delete_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                network)

    def test_update_network(self):
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        network = "MockNetwork"
        network_id = "network_id"
        context = mock.Mock()

        drv.update_network(context, network_id, network)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                network_id, network)

    def test_get_networks(self):
        drv = self._get_drv()
        drv._list_resource = mock.Mock()
        list = ["MockNetwork"]
        context = mock.Mock()
        drv._list_resource.return_value = list

        result = drv.get_networks(context)

        self.assertEqual(result, list)
        drv._list_resource.assert_called_with(self.RESOURCE_NAME, context,
                                              None, None)

    def test_get_networks_count(self):
        drv = self._get_drv()
        drv._count_resource = mock.Mock()
        count = 0
        returned = {
            'count': count,
        }
        context = mock.Mock()
        drv._count_resource.return_value = returned

        result = drv.get_networks_count(context)

        self.assertEqual(result, count)
        drv._count_resource.assert_called_with(self.RESOURCE_NAME, context,
                                               None)


class SubnetTestCases(test_extensions_base.ExtensionTestCase):

    RESOURCE_NAME = 'subnet'

    def setUp(self):
        super(SubnetTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(SubnetTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("networking_opencontrail.common.utils."
                "register_vnc_api_options")
    def _get_drv(self, options):
        return base.OpenContrailDriversBase()

    def _get_subnet(self, gateway_ip=None, ip_version=4,
                    host_routes=ATTR_NOT_SPECIFIED):
        subnet = {
            'id': "test-subnet-1",
            'gateway_ip': gateway_ip,
            'ip_version': ip_version,
            'host_routes': host_routes,
        }

        return {'subnet': subnet}

    def test_create_subnet(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        subnet = self._get_subnet()
        context = mock.Mock()
        drv._create_resource.return_value = subnet

        result = drv.create_subnet(context, subnet)

        self.assertEqual(result, subnet)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                subnet)

    def test_create_subnet_gw_ip(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        subnet = self._get_subnet(gateway_ip="127.0.0.1")
        context = mock.Mock()
        drv._create_resource.return_value = subnet

        result = drv.create_subnet(context, subnet)

        self.assertEqual(result, subnet)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                subnet)

    def test_create_subnet_gw_ipv6(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        subnet = self._get_subnet(ip_version=6)
        context = mock.Mock()
        drv._create_resource.return_value = subnet

        result = drv.create_subnet(context, subnet)

        self.assertEqual(result, subnet)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                subnet)

    @mock.patch("oslo_config.cfg.CONF")
    def test_create_subnet_routes_exhausted(self, config):
        drv = self._get_drv()
        host_routes = ["route-1", "route-2"]
        subnet = self._get_subnet(host_routes=host_routes)
        drv._create_resource = mock.Mock()
        drv._create_resource.return_value = subnet
        context = mock.Mock()
        config.max_subnet_host_routes = 0

        self.assertRaises(neutron_exc.HostRoutesExhausted,
                          drv.create_subnet, context, subnet)

    @mock.patch("oslo_config.cfg.CONF")
    def test_create_subnet_routes_not_exhausted(self, config):
        drv = self._get_drv()
        host_routes = ["route-1", "route-2"]
        subnet = self._get_subnet(host_routes=host_routes)
        drv._create_resource = mock.Mock()
        drv._create_resource.return_value = subnet
        context = mock.Mock()
        config.max_subnet_host_routes = len(host_routes)

        result = drv.create_subnet(context, subnet)

        self.assertEqual(result, subnet)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                subnet)

    def test_get_subnet(self):
        drv = self._get_drv()
        drv._get_resource = mock.Mock()
        subnet = self._get_subnet()
        context = mock.Mock()
        drv._get_resource.return_value = subnet

        result = drv.get_subnet(context, subnet)

        self.assertEqual(result, subnet)
        drv._get_resource.assert_called_with(self.RESOURCE_NAME, context,
                                             subnet, None)

    def test_delete_subnet(self):
        drv = self._get_drv()
        drv._delete_resource = mock.Mock()
        subnet = self._get_subnet()
        context = mock.Mock()

        drv.delete_subnet(context, subnet)

        drv._delete_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                subnet)

    def test_update_subnet(self):
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        subnet = self._get_subnet()
        subnet_id = subnet['subnet']['id']
        context = mock.Mock()

        drv.update_subnet(context, subnet_id, subnet)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                subnet_id, subnet)

    def test_get_subnets(self):
        drv = self._get_drv()
        drv._list_resource = mock.Mock()
        list = [self._get_subnet()]
        context = mock.Mock()
        drv._list_resource.return_value = list

        result = drv.get_subnets(context)

        self.assertEqual(result, list)
        drv._list_resource.assert_called_with(self.RESOURCE_NAME, context,
                                              None, None)

    def test_get_subnet_count(self):
        drv = self._get_drv()
        drv._count_resource = mock.Mock()
        count = 0
        returned = {
            'count': count,
        }
        context = mock.Mock()
        drv._count_resource.return_value = returned

        result = drv.get_subnets_count(context)

        self.assertEqual(result, count)
        drv._count_resource.assert_called_with(self.RESOURCE_NAME, context,
                                               None)


class SecurityGroupTestCases(test_extensions_base.ExtensionTestCase):

    RESOURCE_NAME = 'security_group'

    def setUp(self):
        super(SecurityGroupTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(SecurityGroupTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("networking_opencontrail.common.utils."
                "register_vnc_api_options")
    def _get_drv(self, options):
        return base.OpenContrailDriversBase()

    def test_create_security_group(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        group = "Mock-1"
        context = mock.Mock()
        drv._create_resource.return_value = group

        result = drv.create_security_group(context, group)

        self.assertEqual(result, group)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                group)

    def test_get_security_group(self):
        drv = self._get_drv()
        drv._get_resource = mock.Mock()
        group = "Mock-1"
        context = mock.Mock()
        drv._get_resource.return_value = group

        result = drv.get_security_group(context, group)

        self.assertEqual(result, group)
        drv._get_resource.assert_called_with(self.RESOURCE_NAME, context,
                                             group, None)

    def test_delete_security_group(self):
        drv = self._get_drv()
        drv._delete_resource = mock.Mock()
        group = "Mock-1"
        context = mock.Mock()

        drv.delete_security_group(context, group)

        drv._delete_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                group)

    def test_update_security_group(self):
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        group = "Mock-1"
        group_id = "mock_id"
        context = mock.Mock()

        drv.update_security_group(context, group, group_id)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                group, group_id)

    def test_get_security_groups(self):
        drv = self._get_drv()
        drv._list_resource = mock.Mock()
        list = ["MockGroup"]
        context = mock.Mock()
        drv._list_resource.return_value = list

        result = drv.get_security_groups(context)

        self.assertEqual(result, list)
        drv._list_resource.assert_called_with(self.RESOURCE_NAME, context,
                                              None, None)

    def test_get_security_groups_count(self):
        drv = self._get_drv()
        drv._count_resource = mock.Mock()
        count = 0
        returned = {
            'count': count,
        }
        context = mock.Mock()
        drv._count_resource.return_value = returned

        result = drv.get_security_groups_count(context)

        self.assertEqual(result, count)


class SecurityGroupRuleTestCases(test_extensions_base.ExtensionTestCase):

    RESOURCE_NAME = 'security_group_rule'

    def setUp(self):
        super(SecurityGroupRuleTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(SecurityGroupRuleTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("networking_opencontrail.common.utils."
                "register_vnc_api_options")
    def _get_drv(self, options):
        return base.OpenContrailDriversBase()

    def test_create_security_group_rule(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        group = "Mock-1"
        context = mock.Mock()
        drv._create_resource.return_value = group

        result = drv.create_security_group_rule(context, group)

        self.assertEqual(result, group)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                group)

    def test_get_security_group_rule(self):
        drv = self._get_drv()
        drv._get_resource = mock.Mock()
        group = "Mock-1"
        context = mock.Mock()
        drv._get_resource.return_value = group

        result = drv.get_security_group_rule(context, group)

        self.assertEqual(result, group)
        drv._get_resource.assert_called_with(self.RESOURCE_NAME, context,
                                             group, None)

    def test_delete_security_group_rule(self):
        drv = self._get_drv()
        drv._delete_resource = mock.Mock()
        group = "Mock-1"
        context = mock.Mock()

        drv.delete_security_group_rule(context, group)

        drv._delete_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                group)

    def test_get_security_group_rules(self):
        drv = self._get_drv()
        drv._list_resource = mock.Mock()
        list = ["MockGroup"]
        context = mock.Mock()
        drv._list_resource.return_value = list

        result = drv.get_security_group_rules(context)

        self.assertEqual(result, list)
        drv._list_resource.assert_called_with(self.RESOURCE_NAME, context,
                                              None, None)

    def test_get_security_group_rules_count(self):
        drv = self._get_drv()
        drv._count_resource = mock.Mock()
        count = 0
        returned = {
            'count': count,
        }
        context = mock.Mock()
        drv._count_resource.return_value = returned

        result = drv.get_security_group_rules_count(context)

        self.assertEqual(result, count)


class RouterTestCases(test_extensions_base.ExtensionTestCase):

    RESOURCE_NAME = 'router'

    def setUp(self):
        super(RouterTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(RouterTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("networking_opencontrail.common.utils."
                "register_vnc_api_options")
    def _get_drv(self, options):
        return base.OpenContrailDriversBase()

    def test_create_router(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        router = "Mock-1"
        context = mock.Mock()
        drv._create_resource.return_value = router

        result = drv.create_router(context, router)

        self.assertEqual(result, router)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                router)

    def test_get_router(self):
        drv = self._get_drv()
        drv._get_resource = mock.Mock()
        router = "Mock-1"
        context = mock.Mock()
        drv._get_resource.return_value = router

        result = drv.get_router(context, router)

        self.assertEqual(result, router)
        drv._get_resource.assert_called_with(self.RESOURCE_NAME, context,
                                             router, None)

    def test_update_router(self):
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        router = "Mock-1"
        router_id = "Mock-1"
        context = mock.Mock()

        drv.update_router(context, router_id, router)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                router_id, router)

    def test_delete_router(self):
        drv = self._get_drv()
        drv._delete_resource = mock.Mock()
        router = "Mock-1"
        context = mock.Mock()

        drv.delete_router(context, router)

        drv._delete_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                router)

    def test_get_routers(self):
        drv = self._get_drv()
        drv._list_resource = mock.Mock()
        list = ["MockGroup"]
        context = mock.Mock()
        drv._list_resource.return_value = list

        result = drv.get_routers(context)

        self.assertEqual(result, list)
        drv._list_resource.assert_called_with(self.RESOURCE_NAME, context,
                                              None, None)

    def test_get_routers_count(self):
        drv = self._get_drv()
        drv._count_resource = mock.Mock()
        count = 0
        returned = {
            'count': count,
        }
        context = mock.Mock()
        drv._count_resource.return_value = returned

        result = drv.get_routers_count(context)

        self.assertEqual(result, count)

    def test_add_router_interface(self):
        drv = self._get_drv()
        context = mock.Mock()
        interface = "Mock-1"
        router_id = "Mock-1"

        drv.add_router_interface(context, router_id, interface)

    def test_remove_router_interface(self):
        drv = self._get_drv()
        context = mock.Mock()
        interface = "Mock-1"
        router_id = "Mock-1"

        drv.remove_router_interface(context, router_id, interface)


class PortTestCases(test_extensions_base.ExtensionTestCase):

    RESOURCE_NAME = 'port'

    def setUp(self):
        super(PortTestCases, self).setUp()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super(PortTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch("networking_opencontrail.common.utils."
                "register_vnc_api_options")
    def _get_drv(self, options):
        return base.OpenContrailDriversBase()

    def _get_port(self, fixed_ips=None, host_id=None):
        port = {
            'id': "port-mock-id",
            'network_id': 'net-id',
        }

        if fixed_ips:
            port['fixed_ips'] = fixed_ips

        if host_id:
            port['binding:host_id'] = host_id

        return {'port': port}

    def _get_ip(self, ip="127.0.0.1"):
        return {
            'ip_address': ip,
        }

    def test_create_port(self):
        drv = self._get_drv()
        drv._create_resource = mock.Mock()
        port = self._get_port()
        context = mock.Mock()
        drv._create_resource.return_value = port

        result = drv.create_port(context, port)

        self.assertEqual(result, port)
        drv._create_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                port)

    def test_get_port(self):
        drv = self._get_drv()
        drv._get_resource = mock.Mock()
        port = self._get_port()
        context = mock.Mock()
        drv._get_resource.return_value = port

        result = drv.get_port(context, port)

        self.assertEqual(result, port)
        drv._get_resource.assert_called_with(self.RESOURCE_NAME, context,
                                             port, None)

    def test_delete_port(self):
        drv = self._get_drv()
        drv._delete_resource = mock.Mock()
        port = self._get_port()
        context = mock.Mock()

        drv.delete_port(context, port)

        drv._delete_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                port)

    def test_update_port(self):
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        port = self._get_port()
        port_id = port['port']['id']
        context = mock.Mock()

        drv.update_port(context, port_id, port)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                port_id, port)

    def test_update_port_binding(self):
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        drv._get_port = mock.Mock()
        drv._get_port.return_value = self._get_port()
        port = self._get_port(host_id="mock123")
        port_id = port['port']['id']
        context = mock.Mock()

        drv.update_port(context, port_id, port)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                port_id, port)

    @mock.patch("oslo_config.cfg.CONF")
    def test_update_port_fixed_ips_error(self, config):
        config.max_fixed_ips_per_port = 0
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        port = self._get_port(fixed_ips=["127.0.0.1"])
        port_id = port['port']['id']
        drv._get_port = mock.Mock()
        drv._get_port.return_value = port['port']
        context = mock.Mock()

        self.assertRaises(exceptions.InvalidInput, drv.update_port,
                          context, port_id, port)

    @mock.patch("oslo_config.cfg.CONF")
    def test_update_port_fixed_ips(self, config):
        config.max_fixed_ips_per_port = 10
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        port = self._get_port(fixed_ips=[self._get_ip()])
        port_id = port['port']['id']
        drv._get_port = mock.Mock()
        old_port = self._get_port(fixed_ips=[self._get_ip()])['port']
        drv._get_port.return_value = old_port
        context = mock.Mock()

        drv.update_port(context, port_id, port)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                port_id, port)

    @mock.patch("oslo_config.cfg.CONF")
    def test_update_port_different_fixed_ips(self, config):
        config.max_fixed_ips_per_port = 10
        drv = self._get_drv()
        drv._update_resource = mock.Mock()
        port = self._get_port(fixed_ips=[self._get_ip("192.168.0.1")])
        port_id = port['port']['id']
        drv._get_port = mock.Mock()
        old_port = self._get_port(fixed_ips=[self._get_ip()])['port']
        drv._get_port.return_value = old_port
        context = mock.Mock()

        drv.update_port(context, port_id, port)

        drv._update_resource.assert_called_with(self.RESOURCE_NAME, context,
                                                port_id, port)

    def test_get_ports(self):
        drv = self._get_drv()
        drv._list_resource = mock.Mock()
        list = [self._get_port()]
        context = mock.Mock()
        drv._list_resource.return_value = list

        result = drv.get_ports(context)

        self.assertEqual(result, list)
        drv._list_resource.assert_called_with(self.RESOURCE_NAME, context,
                                              None, None)

    def test_get_ports_count(self):
        drv = self._get_drv()
        drv._count_resource = mock.Mock()
        count = 0
        returned = {
            'count': count,
        }
        context = mock.Mock()
        drv._count_resource.return_value = returned

        result = drv.get_ports_count(context)

        self.assertEqual(result, count)
