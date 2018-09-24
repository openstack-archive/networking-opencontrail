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

    def test_create_vlan_network(self):
        network = self.neutron.create_network({
            'network': {
                'name': 'test_public_1',
                'provider:network_type': 'vlan',
                'provider:segmentation_id': 12,
                'provider:physical_network': 'public',
                'admin_state_up': True,
            },
        })

        contrail_network = self.contrail_network_get(network['network']['id'])
        expected_network_subdict = {
            'segmentation_id': network['network']['provider:segmentation_id'],
            'physical_network': network['network']['provider:physical_network']
        }
        self.assertDictEqual(contrail_network['provider_properties'],
                             expected_network_subdict)

    def test_create_vlan_network_and_subnet(self):
        """Create vlan network using openstack CLI.

        Check if network exists in OpenContrail and all properties are
        the same as used in create command call.
        """
        network = self.neutron.create_network({
            'network': {
                'name': 'test_public_1',
                'provider:network_type': 'vlan',
                'provider:segmentation_id': 13,
                'provider:physical_network': 'public',
                'admin_state_up': True,
            },
        })
        subnet = self.neutron.create_subnet({
            'subnet': {
                'name': 'test_subnet_1',
                'cidr': '192.168.2.0/24',
                'network_id': network['network']['id'],
                'gateway_ip': None,
                'ip_version': 4,
            }
        })

        contrail_subnet = self.contrail_subnet_get(network['network']['id'])
        self.assertIsNotNone(contrail_subnet)
        self.assertEqual(subnet['subnet']['name'], contrail_subnet['subnet_name'])

    def contrail_network_get(self, network_id):
        url = '{}/virtual-network/{}'.format(self.contrail_api, network_id)
        network_result = requests.get(url)
        self.assertIn(network_result.status_code, {200, 301, 302, 303, 304})
        return network_result.json().get('virtual-network')

    def contrail_subnet_get(self, network_id):
        url = '{}/virtual-network/{}'.format(self.contrail_api, network_id)
        network_result = requests.get(url)
        self.assertIn(network_result.status_code, {200, 301, 302, 303, 304})
        return network_result.json().get('network_ipam_refs')[0].get('attr').get('ipam_subnets')[0].get('subnet')
