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


import mock

from neutron.tests.unit.extensions import base as test_extensions_base
from requests import codes as http_statuses

from networking_opencontrail.agents import dhcp_scheduler


@mock.patch('networking_opencontrail.agents.dhcp_scheduler.TFDHCPFilter')
class DHCPSchedulerTestCase(test_extensions_base.ExtensionTestCase):
    def setUp(self):
        super(DHCPSchedulerTestCase, self).setUp()

    def tearDown(self):
        super(DHCPSchedulerTestCase, self).tearDown()

    def test_create_scheduler_with_tf_filter(self, dhcp_filter):
        dhcp_scheduler.TFIgnoreDHCPScheduler()

        dhcp_filter.assert_called_with()

    def test_call_filter_on_schedule(self, _):
        plugin = mock.Mock()
        context = mock.Mock()
        resource = {'id': 'net-1'}
        agents = [mock.Mock()]
        tf_scheduler = dhcp_scheduler.TFIgnoreDHCPScheduler()
        mock_dhcp_filter_result(tf_scheduler.resource_filter,
                                hostable_agents=agents)

        tf_scheduler.schedule(plugin, context, resource)

        expected_calls = [
            mock.call.filter_agents(plugin, context, resource),
            mock.call.bind(context, agents, resource['id'])]
        tf_scheduler.resource_filter.assert_has_calls(expected_calls)


class TFDHCPFilterTestCase(test_extensions_base.ExtensionTestCase):
    def setUp(self):
        super(TFDHCPFilterTestCase, self).setUp()
        dhcp_scheduler.ContrailRestApiDriver = mock.Mock()
        self.dhcp_filter = dhcp_scheduler.TFDHCPFilter()
        self.tf_rest_driver = dhcp_scheduler.ContrailRestApiDriver()

    def tearDown(self):
        super(TFDHCPFilterTestCase, self).tearDown()

    @mock.patch('networking_opencontrail.agents.dhcp_scheduler'
                '.dhcp_agent_scheduler.DhcpFilter.bind')
    def test_bind_tf_network(self, base_bind):
        context = mock.Mock()
        agents = ['agent-1']
        network_id = 'net-id'
        self._mock_network_exist_in_tf()

        self.dhcp_filter.bind(context, agents, network_id)

        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network_id)
        base_bind.assert_not_called()

    @mock.patch('networking_opencontrail.agents.dhcp_scheduler'
                '.dhcp_agent_scheduler.DhcpFilter.bind')
    def test_bind_not_tf_network(self, base_bind):
        context = mock.Mock()
        agents = ['agent-1']
        network_id = 'net-id'
        self._mock_network_not_exist_in_tf()

        self.dhcp_filter.bind(context, agents, network_id)

        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network_id)
        base_bind.assert_called_with(context, agents, network_id)

    @mock.patch('networking_opencontrail.agents.dhcp_scheduler'
                '.dhcp_agent_scheduler.DhcpFilter.bind')
    def test_bind_tf_server_error(self, base_bind):
        context = mock.Mock()
        agents = ['agent-1']
        network_id = 'net-id'
        args = [context, agents, network_id]
        self._mock_tf_api_error()

        self.assertRaises(dhcp_scheduler.TFResponseNotExpectedError,
                          self.dhcp_filter.bind, *args)

        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network_id)
        base_bind.assert_not_called()

    @mock.patch('networking_opencontrail.agents.dhcp_scheduler'
                '.dhcp_agent_scheduler.DhcpFilter.filter_agents')
    def test_filter_tf_network(self, base_filter):
        context = mock.Mock()
        plugin = mock.Mock()
        hostable_agents = ['agent-1']
        hosted_agents = ['agent-2']
        network = {'id': 'net-id'}
        mock_filter_agents(base_filter, hostable_agents, hosted_agents)
        self._mock_network_exist_in_tf()

        result = self.dhcp_filter.filter_agents(plugin, context, network)

        expected_dict = {'n_agents': 0, 'hostable_agents': [],
                         'hosted_agents': hosted_agents}
        self.assertEqual(result, expected_dict)
        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network['id'])
        base_filter.assert_called_with(plugin, context, network)

    @mock.patch('networking_opencontrail.agents.dhcp_scheduler'
                '.dhcp_agent_scheduler.DhcpFilter.filter_agents')
    def test_filter_not_tf_network(self, base_filter):
        context = mock.Mock()
        plugin = mock.Mock()
        hostable_agents = ['agent-1']
        hosted_agents = ['agent-2']
        network = {'id': 'net-id'}
        mock_filter_agents(base_filter, hostable_agents, hosted_agents)
        self._mock_network_not_exist_in_tf()

        result = self.dhcp_filter.filter_agents(plugin, context, network)

        expected_dict = {'n_agents': len(hostable_agents),
                         'hostable_agents': hostable_agents,
                         'hosted_agents': hosted_agents}
        self.assertEqual(result, expected_dict)
        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network['id'])
        base_filter.assert_called_with(plugin, context, network)

    @mock.patch('networking_opencontrail.agents.dhcp_scheduler'
                '.dhcp_agent_scheduler.DhcpFilter.filter_agents')
    def test_filter_tf_server_error(self, base_filter):
        context = mock.Mock()
        plugin = mock.Mock()
        hostable_agents = ['agent-1']
        hosted_agents = ['agent-2']
        network = {'id': 'net-id'}
        mock_filter_agents(base_filter, hostable_agents, hosted_agents)
        args = [plugin, context, network]
        self._mock_tf_api_error()

        self.assertRaises(dhcp_scheduler.TFResponseNotExpectedError,
                          self.dhcp_filter.filter_agents, *args)

        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network['id'])
        base_filter.assert_called_with(plugin, context, network)

    def _mock_network_exist_in_tf(self):
        self.tf_rest_driver.get_resource = mock.Mock(
            return_value=(http_statuses.ok, None))

    def _mock_network_not_exist_in_tf(self):
        self.tf_rest_driver.get_resource = mock.Mock(
            return_value=(http_statuses.not_found, None))

    def _mock_tf_api_error(self):
        self.tf_rest_driver.get_resource = mock.Mock(
            return_value=(http_statuses.server_error,
                          {"message": "Internal Server Error"}))


def mock_dhcp_filter_result(dhcp_filter, hostable_agents):
    filter_agents = mock.Mock()
    mock_filter_agents(filter_agents, hostable_agents)
    dhcp_filter.filter_agents = filter_agents


def mock_filter_agents(mocked_filter, hostable_agents, hosted_agents=None):
    if hosted_agents is None:
        hosted_agents = []
    result = {'n_agents': len(hostable_agents),
              'hostable_agents': hostable_agents,
              'hosted_agents': hosted_agents}
    mocked_filter.return_value = result
