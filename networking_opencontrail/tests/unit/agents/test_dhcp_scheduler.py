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


class DHCPSchedulerTestCase(test_extensions_base.ExtensionTestCase):
    """Test cases for TF DHCP Scheduler."""

    def setUp(self):
        super(DHCPSchedulerTestCase, self).setUp()
        dhcp_scheduler.ContrailRestApiDriver = mock.Mock()
        self.tf_rest_driver = dhcp_scheduler.ContrailRestApiDriver()

    def tearDown(self):
        super(DHCPSchedulerTestCase, self).tearDown()

    def test_scheduling_tf_network(self):
        context = mock.Mock()
        plugin = mock.Mock()
        network = {'id': 'net-id'}
        self._mock_network_exist_in_tf()

        tf_scheduler = dhcp_scheduler.TFIgnoreDHCPScheduler()
        ret_value = tf_scheduler.schedule(plugin, context, network)

        self.assertEqual(ret_value, [])
        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network['id'])

    @mock.patch('networking_opencontrail.agents.dhcp_scheduler'
                '.dhcp_agent_scheduler.ChanceScheduler.schedule')
    def test_scheduling_not_tf_network(self, base_schedule):
        context = mock.Mock()
        plugin = mock.Mock()
        network = {'id': 'net-id'}
        agents = ['agent-1']
        self._mock_network_not_exist_in_tf()
        base_schedule.return_value = agents

        tf_scheduler = dhcp_scheduler.TFIgnoreDHCPScheduler()
        ret_value = tf_scheduler.schedule(plugin, context, network)

        self.assertEqual(ret_value, agents)
        base_schedule.assert_called_with(plugin, context, network)
        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network['id'])

    def test_tf_server_error(self):
        context = mock.Mock()
        plugin = mock.Mock()
        network = {'id': 'net-id'}
        args = [context, plugin, network]
        self._mock_tf_api_error()

        tf_scheduler = dhcp_scheduler.TFIgnoreDHCPScheduler()
        self.assertRaises(dhcp_scheduler.TFResponseNotExpected,
                          tf_scheduler.schedule, *args)

        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network['id'])

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
