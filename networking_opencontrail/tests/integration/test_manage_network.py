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
import subprocess

import requests

from networking_opencontrail.tests.base import IntegrationTestCase


class TestManageNetwork(IntegrationTestCase):
    def setUp(self):
        super(TestManageNetwork, self).super()
        self.api_url = '{}/virtual-networks'.format(self.contrail_api)

    def find_network(self, name, networks):
        """Iterate over virtual-networks list obtained from OpenContrail API.

        Lookup for network name in fq_name list.
        """
        for net in networks:
            if name in net['fq_name']:
                result = requests.get(net['href']).json()
                return result['virtual-network']
        return None

    def test_create_vlan_network(self):
        """Create vlan network using openstack CLI.

        Check if network exists in OpenContrail and all properties are
        the same as used in create command call.
        """
        network_name = 'test_public_1'
        provider_segment = 10
        provider_physical = 'public'

        subprocess.call(['openstack', 'network', 'create',
                         '--project', 'demo',
                         '--provider-network-type', 'vlan',
                         '--provider-segment', provider_segment,
                         '--provider-physical-network', provider_physical,
                         network_name], stdout=subprocess.PIPE)

        result = requests.get(self.api_url).json()
        network = self.find_network(network_name, result['virtual-networks'])

        self.assertIsNotNone(network)  # check if network exists first
        self.assertEqual(network['display_name'], network_name)
        self.assertEqual(network['name'], network_name)
        self.assertDictEqual(network['provider_properties'],
                             {'segmentation_id': provider_segment,
                              'physical_network': provider_physical})

    def test_update_vlan_network(self):
        network_name = 'test_public_2'
        network_name_updated = 'test_public_2_updated'
        provider_segment = 11
        provider_physical = 'public'

        subprocess.call(['openstack', 'network', 'create',
                         '--project', 'demo',
                         '--provider-network-type', 'vlan',
                         '--provider-segment', provider_segment,
                         '--provider-physical-network', provider_physical,
                         '--enable',
                         network_name])

        result = requests.get(self.api_url).json()
        network = self.find_network(network_name, result['virtual-networks'])

        self.assertIsNotNone(network)  # check if network exists first

        subprocess.call(['openstack', 'network', 'set',
                         '--name', network_name_updated,
                         '--disable',
                         network['uuid']])

        self.assertEqual(network['display_name'], network_name_updated)
        self.assertEqual(network['name'], network_name)
        self.assertDictEqual(network['provider_properties'],
                             {'segmentation_id': provider_segment,
                              'physical_network': provider_physical})
        self.assertFalse(network['id_perms']['enable'])

    def test_delete_vlan_network(self):
        network_name = 'test_public_3'
        provider_segment = 12
        provider_physical = 'public'

        subprocess.call(['openstack', 'network', 'create',
                         '--project', 'demo',
                         '--provider-network-type', 'vlan',
                         '--provider-segment', provider_segment,
                         '--provider-physical-network', provider_physical,
                         network_name])

        result = requests.get(self.api_url).json()
        network = self.find_network(network_name, result['virtual-networks'])

        self.assertIsNotNone(network)  # check if network exists first

        subprocess.call(['openstack', 'network', 'delete', network['uuid']])
        self.assertIsNone(self.find_network(network_name, result['virtual-networks']))
