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

from neutron_lib.callbacks import events
from neutron_lib.callbacks import resources

from neutron.tests.unit import testlib_api

from networking_opencontrail.ml2 import subnet_dns_integrator


class SubnetDNSCompatibilityIntegratorTestCase(testlib_api.SqlTestCase):
    """Test cases for Subnet DNS Compatibility Integrator.

    Methods to create dns port in Neutron; subscribe events to remove
    dns port on delete subnet or network.
    """

    def setUp(self):
        super(SubnetDNSCompatibilityIntegratorTestCase, self).setUp()
        subnet_dns_integrator.directory.get_plugin = mock.Mock()
        self.tf_driver = mock.Mock()
        self.dns_integrator = (
            subnet_dns_integrator.SubnetDNSCompatibilityIntegrator(
                self.tf_driver))
        self.core_plugin = self.dns_integrator._core_plugin

    def tearDown(self):
        super(SubnetDNSCompatibilityIntegratorTestCase, self).tearDown()

    def test_synchronize_tf_dns_port_in_neutron(self):
        context = self._get_fake_context()
        subnet = self._get_subnet_data()
        dns_port = self._get_dns_port_data(subnet)
        self._mock_core_plugin_get_port(ports=[])

        self.dns_integrator.synchronize_dns_port_for_subnet(context, subnet)

        expected_filters = {
            'device_id': [subnet['id']],
            'device_owner': [subnet_dns_integrator.TF_DNS_DEVICE_OWNER]}
        expected_calls = [
            mock.call.get_ports(context, filters=expected_filters),
            mock.call.create_port(context, {'port': dns_port})]
        self.core_plugin.assert_has_calls(expected_calls)

    def test_synchronize_tf_dns_port_in_neutron_when_port_exists(self):
        context = self._get_fake_context()
        subnet = self._get_subnet_data()

        ports = [{'fixed_ips': [{'ip_address': subnet['dns_server_address']}]}]
        self._mock_core_plugin_get_port(ports=ports)

        self.dns_integrator.synchronize_dns_port_for_subnet(context, subnet)

        expected_filters = {
            'device_id': [subnet['id']],
            'device_owner': [subnet_dns_integrator.TF_DNS_DEVICE_OWNER]}
        expected_calls = [
            mock.call.get_ports(context, filters=expected_filters)]
        self.core_plugin.assert_has_calls(expected_calls)
        self.core_plugin.create_port.assert_not_called()

    def test_synchronize_tf_dns_port_in_neutron_when_no_dns(self):
        context = self._get_fake_context()
        subnet = self._get_subnet_data()
        del subnet['dns_server_address']

        self.dns_integrator.synchronize_dns_port_for_subnet(context, subnet)

        self.core_plugin.get_ports.assert_not_called()
        self.core_plugin.create_port.assert_not_called()

    def test_subnet_before_delete_callback(self):
        payload = self._get_payload('sub-1', 'test-subnet')
        kwargs = self._get_callback_params(
            resources.SUBNET, payload, events.BEFORE_DELETE)

        ports = [{'id': 'port-1', 'name': 'test-port'}]
        self._mock_core_plugin_get_port(ports=ports)
        expected_filter = {
            'device_id': [payload.resource_id],
            'device_owner': [subnet_dns_integrator.TF_DNS_DEVICE_OWNER]}

        self.dns_integrator.before_delete_subnet(**kwargs)

        expected_calls = [
            mock.call.get_ports(payload.context, filters=expected_filter),
            mock.call.delete_port(payload.context, ports[0]['id'])]
        self.core_plugin.assert_has_calls(expected_calls)

    def test_subnet_before_delete_callback_no_port(self):
        payload = self._get_payload('sub-1', 'test-subnet')
        kwargs = self._get_callback_params(
            resources.SUBNET, payload, events.BEFORE_DELETE)

        self._mock_core_plugin_get_port(ports=[])
        expected_filter = {
            'device_id': [payload.resource_id],
            'device_owner': [subnet_dns_integrator.TF_DNS_DEVICE_OWNER]}

        self.dns_integrator.before_delete_subnet(**kwargs)

        expected_calls = [
            mock.call.get_ports(payload.context, filters=expected_filter)]
        self.core_plugin.assert_has_calls(expected_calls)
        self.core_plugin.delete_port.assert_not_called()

    def test_subnet_abort_delete_callback(self):
        subnet = self._get_subnet_data()
        payload = self._get_payload(subnet['id'], subnet['name'])
        kwargs = self._get_callback_params(
            resources.SUBNET, payload, events.ABORT_DELETE)

        self._mock_tf_driver_get_subnet(subnet_data=subnet)
        self._mock_core_plugin_get_port(ports=[])
        self.dns_integrator.synchronize_dns_port_for_subnet = mock.Mock()

        self.dns_integrator.abort_delete_subnet(**kwargs)

        self.dns_integrator.synchronize_dns_port_for_subnet.assert_called_with(
            payload.context, subnet)

    def test_network_before_delete_callback(self):
        payload = self._get_payload('net-1', 'test-network')
        kwargs = self._get_callback_params(
            resources.NETWORK, payload, events.BEFORE_DELETE)

        ports = [{'id': 'port-1', 'name': 'test-port'},
                 {'id': 'port-2', 'name': 'test-port2'}]
        self._mock_core_plugin_get_port(ports=ports)
        expected_filter = {
            'network_id': [payload.resource_id],
            'device_owner': [subnet_dns_integrator.TF_DNS_DEVICE_OWNER]}

        self.dns_integrator.before_delete_network(**kwargs)

        expected_calls = [
            mock.call.get_ports(payload.context, filters=expected_filter),
            mock.call.delete_port(payload.context, ports[0]['id']),
            mock.call.delete_port(payload.context, ports[1]['id'])]
        self.core_plugin.assert_has_calls(expected_calls)

    def test_network_before_delete_callback_no_port(self):
        payload = self._get_payload('net-1', 'test-network')
        kwargs = self._get_callback_params(
            resources.NETWORK, payload, events.BEFORE_DELETE)

        self._mock_core_plugin_get_port(ports=[])
        expected_filter = {
            'network_id': [payload.resource_id],
            'device_owner': [subnet_dns_integrator.TF_DNS_DEVICE_OWNER]}

        self.dns_integrator.before_delete_network(**kwargs)

        expected_calls = [
            mock.call.get_ports(payload.context, filters=expected_filter)]
        self.core_plugin.assert_has_calls(expected_calls)
        self.core_plugin.delete_port.assert_not_called()

    def test_network_abort_delete_callback(self):
        pass

    def _mock_core_plugin_get_port(self, ports):
        self.core_plugin.get_ports = mock.Mock(return_value=ports)

    def _mock_tf_driver_get_subnet(self, subnet_data):
        self.tf_driver.get_subnet = mock.Mock(return_value=subnet_data)

    def _get_subnet_data(self, sub_id='sub-1', sub_name='test-subnet',
                         dns_address='10.10.10.2'):
        subnet = {'id': sub_id,
                  'network_id': 'test_net-1',
                  'tenant_id': 'ten-1',
                  'name': sub_name,
                  'dns_server_address': dns_address}
        return subnet

    def _get_dns_port_data(self, subnet):
        port_data = {'tenant_id': subnet['tenant_id'],
                     'network_id': subnet['network_id'],
                     'fixed_ips': [{
                         'ip_address': subnet['dns_server_address']}],
                     'device_id': subnet['id'],
                     'device_owner': subnet_dns_integrator.TF_DNS_DEVICE_OWNER,
                     'admin_state_up': True,
                     'name': 'tungstenfabric-dns-service'}
        return port_data

    def _get_callback_params(self, resource, payload, event):
        params = {}
        params['resource'] = resource
        params['event'] = event
        params['trigger'] = mock.Mock()
        params['payload'] = payload

        return params

    def _get_payload(self, resource_id, resource_name):
        payload = mock.Mock()
        payload.context = self._get_fake_context()
        payload.latest_state = {'id': resource_id,
                                'name': resource_name}
        payload.resource_id = resource_id

        return payload

    def _get_fake_context(self, **kwargs):
        return mock.Mock(**kwargs)
