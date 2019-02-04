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
    """Test cases for TF DHCP Scheduler."""

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
        agents = ['agent-1']
        tf_scheduler = dhcp_scheduler.TFIgnoreDHCPScheduler()
        self._mock_dhcp_filter_result(tf_scheduler.resource_filter,
                                      agents=agents)

        tf_scheduler.schedule(plugin, context, resource)

        expected_calls = [
            mock.call.filter_agents(plugin, context, resource),
            mock.call.bind(context, agents, resource['id'])]
        tf_scheduler.resource_filter.assert_has_calls(expected_calls)

    def _mock_dhcp_filter_result(self, dhcp_filter, agents):
        result = {'n_agents': len(agents), 'hostable_agents': agents,
                  'hosted_agents': []}
        dhcp_filter.filter_agents = mock.Mock(return_value=result)


@mock.patch('networking_opencontrail.agents.dhcp_scheduler'
            '.dhcp_agent_scheduler.DhcpFilter.bind')
class TFDHCPFilterTestCase(test_extensions_base.ExtensionTestCase):
    def setUp(self):
        super(TFDHCPFilterTestCase, self).setUp()
        dhcp_scheduler.ContrailRestApiDriver = mock.Mock()
        self.dhcp_filter = dhcp_scheduler.TFDHCPFilter()
        self.tf_rest_driver = dhcp_scheduler.ContrailRestApiDriver()

    def tearDown(self):
        super(TFDHCPFilterTestCase, self).tearDown()

    def test_bind_tf_network(self, base_bind):
        context = mock.Mock()
        agents = ['agent-1']
        network_id = 'net-id'
        self._mock_network_exist_in_tf()

        self.dhcp_filter.bind(context, agents, network_id)

        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network_id)
        base_bind.assert_not_called()

    # bind_not_tf
    # bind_exception
    # filter_tf
    # filter_not_tf
    # filter_exception

    # def test_scheduling_not_tf_network(self, base_schedule):
    #     context = mock.Mock()
    #     plugin = mock.Mock()
    #     network = {'id': 'net-id'}
    #     agents = ['agent-1']
    #     self._mock_network_not_exist_in_tf()
    #     base_schedule.return_value = agents

    #     ret_value = self.tf_scheduler.schedule(plugin, context, network)

    #     self.assertEqual(ret_value, agents)
    #     base_schedule.assert_called_with(plugin, context, network)
    #     self.tf_rest_driver.get_resource.assert_called_with(
    #         'virtual-network', None, network['id'])

    # def test_tf_server_error(self, base_schedule):
    #     context = mock.Mock()
    #     plugin = mock.Mock()
    #     network = {'id': 'net-id'}
    #     args = [context, plugin, network]
    #     self._mock_tf_api_error()

    #     self.assertRaises(dhcp_scheduler.TFResponseNotExpectedError,
    #                       self.tf_scheduler.schedule, *args)

    #     self.tf_rest_driver.get_resource.assert_called_with(
    #         'virtual-network', None, network['id'])

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
