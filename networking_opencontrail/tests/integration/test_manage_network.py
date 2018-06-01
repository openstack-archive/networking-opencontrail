# -*- coding: utf-8 -*-
# Copyright (c) 2018 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import requests

from networking_opencontrail.tests.base import IntegrationTestCase


class TestManageNetwork(IntegrationTestCase):
    def setUp(self):
        super(TestManageNetwork, self).setUp()
        self.api_virtual_nets = '{}/virtual-networks'.format(self.contrail_api)

    @staticmethod
    def find_network(name, networks):
        """Iterate over virtual-networks list obtained from OpenContrail API.

        Lookup for network name in fq_name list.
        """
        for net in networks:
            if name in net['fq_name']:
                result = requests.get(net['href']).json()
                return result['virtual-network']
        return None

    def test_contrail_synchronized_projects(self):
        pass

    def test_create_vlan_network(self):
        """Create vlan network using openstack CLI.

        Check if network exists in OpenContrail and all properties are
        the same as used in create command call.
        """
        network = {
            'name': 'test_public_1',
            'provider:network_type': 'vlan',
            'provider:segmentation_id': 10,
            'provider:physical_network': 'public',
            'admin_state_up': True
        }
        self.neutron.create_network({'network': network})

        result = requests.get(self.api_virtual_nets).json()
        check_network = self.find_network(network['name'],
                                          result['virtual-networks'])

        self.assertIsNotNone(check_network)  # check if network exists first
        self.assertEqual(check_network['name'], network['name'])
        self.assertDictEqual(
            check_network['provider_properties'],
            {'segmentation_id': network['provider:segmentation_id'],
             'physical_network': network['provider:physical_network']})
