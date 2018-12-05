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

from networking_opencontrail.ml2 import subnet_dns_integrator


class SubnetDNSCompatibilityIntegratorTestCase(testlib_api.SqlTestCase):
    """Test cases for Subnet DNS Compatibility Integrator.

    Methods to create dns port in Neutron; subscribe events to remove
    dns port on delete subnet or network.
    """

    def setUp(self):
        super(SubnetDNSCompatibilityIntegratorTestCase, self).setUp()
        self.dns_integrator = (
            subnet_dns_integrator.SubnetDNSCompatibilityIntegrator())
        subnet_dns_integrator.directory.get_plugin = mock.Mock()
        self.core_plugin = self.dns_integrator._core_plugin

    def tearDown(self):
        super(SubnetDNSCompatibilityIntegratorTestCase, self).tearDown()

    def test_create_tf_dns_port_in_neutron(self):
        context = self._get_fake_context()
        subnet = self._get_subnet_data()
        dns_port = self._get_dns_port_data(subnet)

        self.dns_integrator.create_tf_dns_in_neutron(context, subnet)

        expected_calls = [
            mock.call.create_port(context, {'port': dns_port})
        ]

        self.core_plugin.assert_has_calls(expected_calls)

    def test_not_create_tf_dns_port_in_neutron(self):
        context = self._get_fake_context()
        subnet = self._get_subnet_data()
        del subnet['dns_server_address']

        self.dns_integrator.create_tf_dns_in_neutron(context, subnet)

        self.core_plugin.create_port.assert_not_called()

    def test_subnet_before_delete_callback(self):
        pass

    def _get_subnet_data(self):
        subnet = {'id': 'ten-1',
                  'network_id': 'test_net-1',
                  'tenant_id': 'ten-1',
                  'name': 'test-subnet',
                  'dns_server_address': '10.10.10.2'}
        return subnet

    def _get_dns_port_data(self, subnet):
        port_data = {'tenant_id': subnet['tenant_id'],
                     'network_id': subnet['network_id'],
                     'fixed_ips': [{
                         'ip_address': subnet['dns_server_address']}],
                     'device_id': subnet['id'],
                     'device_owner': subnet_dns_integrator.TF_DNS_DEVICE_OWNER,
                     'admin_state_up': True,
                     'name': 'tungstenfabric-dns-server'}
        return port_data

    def _get_fake_context(self):
        return mock.Mock()
