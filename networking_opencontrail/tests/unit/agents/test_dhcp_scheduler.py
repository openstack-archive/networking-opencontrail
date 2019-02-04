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

from neutron.tests.unit import testlib_api
from requests import codes as http_statuses

from networking_opencontrail.agents import dhcp_scheduler


class DHCPSchedulerTestCase(testlib_api.SqlTestCase):
    """Test cases for TF DHCP Scheduler."""

    def setUp(self):
        super(DHCPSchedulerTestCase, self).setUp()
        dhcp_scheduler.dhcp_agent_scheduler = mock.Mock()
        dhcp_scheduler.ContrailRestApiDriver = mock.Mock()

        self.tf_scheduler = dhcp_scheduler.TFIgnoreDHCPScheduler()
        self.tf_rest_driver = self.tf_scheduler.tf_rest_driver

    def tearDown(self):
        super(DHCPSchedulerTestCase, self).tearDown()

    def test_scheduling_tf_network(self):
        context = mock.Mock()
        plugin = mock.Mock()
        network = {'id': 'net-id'}
        self._mock_network_exist_in_tf()

        ret_value = self.tf_scheduler.schedule(plugin, context, network)

        self.assertEqual(ret_value, [])
        self.tf_rest_driver.get_resource.assert_called_with(
            'virtual-network', None, network['id'])

    # def test_scheduling_not_tf_network(self):
    #     context = mock.Mock()
    #     plugin = mock.Mock()
    #     network = {'id': 'net-id'}
    #     agents = ['agent-1']
    #     self._mock_network_not_exist_in_tf()
    #     base_schedule = mock.Mock(return_value=agents)

    #     ret_value = self.tf_scheduler.schedule(plugin, context, network)

    #     self.assertEqual(ret_value, agents)
    #     base_schedule.assert_called_with(plugin, context, network)
    #     self.tf_rest_driver.get_resource.assert_called_with(
    #         'virtual-network', None, network['id'])

    def _mock_network_exist_in_tf(self):
        self.tf_rest_driver.get_resource = mock.Mock(
            return_value=(http_statuses.ok, None))

    def _mock_network_not_exist_in_tf(self):
        self.tf_rest_driver.get_resource = mock.Mock(
            return_value=(http_statuses.not_found, None))
