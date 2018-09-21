# Copyright (c) 2016 OpenStack Foundation
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


import mock

from neutron.tests.unit import testlib_api

from networking_opencontrail.ml2 import mech_driver


class OpenContrailTestCases(testlib_api.SqlTestCase):
    """Main test cases for ML2 mechanism driver for OpenContrail.

    Tests all ML2 API supported by OpenContrail. It invokes the back-end
    driver APIs as they would normally be invoked by the driver.
    """

    def setUp(self):
        super(OpenContrailTestCases, self).setUp()
        self.fake_api = mock.MagicMock()
        mech_driver.drv = mock.MagicMock()
        self.drv = mech_driver.OpenContrailMechDriver()
        self.drv.initialize()

    def tearDown(self):
        super(OpenContrailTestCases, self).tearDown()

    def test_create_network(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'

        net_context, network = self.get_network_context(tenant_id, network_id)
        self.drv.create_network_postcommit(net_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_network(
                net_context._plugin_context, network)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_delete_network(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'

        net_context, network = self.get_network_context(tenant_id, network_id)
        self.drv.delete_network_postcommit(net_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().delete_network(
                net_context._plugin_context, network_id)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_update_network(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'
        net_name = 'name-1'

        net_context, network = self.get_network_context(tenant_id,
                                                        network_id,
                                                        net_name=net_name)
        self.drv.create_network_postcommit(net_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_network(
                net_context._plugin_context, network)
        ]
        # Change the name of the network
        net_name = 'name-2'
        net_context, network = self.get_network_context(tenant_id,
                                                        network_id,
                                                        net_name=net_name)
        self.drv.update_network_postcommit(net_context)

        expected_calls.append(
            mock.call.OpenContrailDrivers().update_network(
                net_context._plugin_context, network_id, network))

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_create_subnet(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'
        subnet_id = 'sub-1'

        subnet_context, subnet = self.get_subnet_context(tenant_id, network_id,
                                                         subnet_id)
        self.drv.create_subnet_postcommit(subnet_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_subnet(
                subnet_context._plugin_context, subnet)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_delete_subnet(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'
        subnet_id = 'sub-1'

        subnet_context, subnet = self.get_subnet_context(tenant_id, network_id,
                                                         subnet_id)
        self.drv.delete_subnet_postcommit(subnet_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().delete_subnet(
                subnet_context._plugin_context, subnet_id)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_update_subnet(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'
        subnet_id = 'sub-1'
        subnet_name = 'test-sub-1'

        subnet_context, subnet = self.get_subnet_context(tenant_id, network_id,
                                                         subnet_id,
                                                         subnet_name)
        self.drv.create_subnet_postcommit(subnet_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_subnet(
                subnet_context._plugin_context, subnet)
        ]

        # Change the subnet information
        subnet_name = 'test-sub-2'
        subnet_context, subnet = self.get_subnet_context(tenant_id, network_id,
                                                         subnet_id,
                                                         subnet_name)
        self.drv.update_subnet_postcommit(subnet_context)

        expected_calls.append(
            mock.call.OpenContrailDrivers().update_subnet(
                subnet_context._plugin_context, subnet_id, subnet))

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_create_port(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'
        port_id = 'port-1'

        port_context, port = self.get_port_context(tenant_id, network_id,
                                                   port_id)
        self.drv.create_port_postcommit(port_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_port(
                port_context._plugin_context, port)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_delete_port(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'
        port_id = 'port-1'

        port_context, port = self.get_port_context(tenant_id, network_id,
                                                   port_id)
        self.drv.delete_port_postcommit(port_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().delete_port(
                port_context._plugin_context, port_id)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_update_port(self):
        network_id = 'test_net1'
        tenant_id = 'ten-1'
        port_id = 'port-1'
        port_name = 'first-port'

        port_context, port = self.get_port_context(tenant_id, network_id,
                                                   port_id, port_name)
        self.drv.create_port_postcommit(port_context)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_port(
                port_context._plugin_context, port)
        ]

        # Chnage the port properties
        port_name = 'second-port'

        port_context, port = self.get_port_context(tenant_id, network_id,
                                                   port_id, port_name)
        self.drv.update_port_postcommit(port_context)

        expected_calls.append(
            mock.call.OpenContrailDrivers().update_port(
                port_context._plugin_context, port_id, port))

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_create_security_group(self):
        ctx = fake_plugin_context('ten-1')
        sg = {'id': 'sg-1', 'name': 'test-security-group'}
        self.drv.create_security_group(ctx, sg)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_security_group(
                ctx, {'security_group': sg})
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_delete_security_group(self):
        ctx = fake_plugin_context('ten-1')
        sg_id = 'sg-1'
        self.drv.delete_security_group(ctx, {'id': sg_id})

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().delete_security_group(
                ctx, sg_id)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_update_security_group(self):
        ctx = fake_plugin_context('ten-1')
        sg_id = 'sg-1'
        sg = {'id': sg_id}
        self.drv.update_security_group(ctx, sg_id, sg)

        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().update_security_group(
                ctx, sg_id, {'security_group': sg})
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_create_security_group_rule(self):
        ctx = fake_plugin_context('ten-1')
        sg_rule = {'direction': 'ingress',
                   'security_group_id': 'sg-1',
                   'remote_group_id': 'remote-1'}
        self.drv.create_security_group_rule(ctx, sg_rule)
        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().create_security_group_rule(
                ctx, {'security_group_rule': sg_rule})
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def test_delete_security_group_rule(self):
        ctx = fake_plugin_context('ten-1')
        sg_rule = {'id': 'sg-rule-1'}
        self.drv.delete_security_group_rule(ctx, sg_rule)
        expected_calls = [
            mock.call.OpenContrailDrivers(),
            mock.call.OpenContrailDrivers().delete_security_group_rule(
                ctx, sg_rule)
        ]

        mech_driver.drv.assert_has_calls(expected_calls)

    def get_network_context(self, ten_id, net_id, net_name=None):
        if not net_name:
            net_name = 'test_network'
        network = {'id': net_id,
                   'tenant_id': ten_id,
                   'name': net_name}
        context = fake_network_context(ten_id, network, network)
        net = {'network': network}
        return context, net

    def get_subnet_context(self, ten_id, net_id, sub_id, sub_name=None):
        if not sub_name:
            sub_name = 'test_subnet'
        subnet = {'id': sub_id,
                  'network_id': net_id,
                  'tenant_id': ten_id,
                  'name': sub_name}
        context = fake_subnet_context(ten_id, subnet, subnet)
        subnt = {'subnet': subnet}
        return context, subnt

    def get_port_context(self, ten_id, net_id, port_id, port_name=None):
        if not port_name:
            port_name = 'test_port'
        port = {'id': port_id,
                'network_id': net_id,
                'tenant_id': ten_id,
                'name': port_name}
        context = fake_port_context(ten_id, port, port)
        prt = {'port': port}
        return context, prt


class fake_network_context(object):
    """Generate network context for testing purposes."""

    def __init__(self, tenant_id, network, original_network=None):
        self._network = network
        self._original_network = original_network
        self._plugin_context = fake_plugin_context(tenant_id)

    @property
    def current(self):
        return self._network

    @property
    def original(self):
        return self._original_network


class fake_subnet_context(object):
    """Generate subnet context for testing purposes."""

    def __init__(self, tenant_id, subnet, original_subnet=None):
        self._subnet = subnet
        self._original_subnet = original_subnet
        self._plugin_context = fake_plugin_context(tenant_id)

    @property
    def current(self):
        return self._subnet

    @property
    def original(self):
        return self._original_subnet


class fake_port_context(object):
    """Generate port context for testing purposes."""

    def __init__(self, tenant_id, port, original_port=None):
        self._port = port
        self._original_port = original_port
        self._plugin_context = fake_plugin_context(tenant_id)

    @property
    def current(self):
        return self._port

    @property
    def original(self):
        return self._original_port


class fake_plugin_context(object):
    """ML2 Plugin context for testing purposes only."""

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.session = mock.MagicMock()
