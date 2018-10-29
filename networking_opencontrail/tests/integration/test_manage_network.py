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

from networking_opencontrail.tests.base import IntegrationTestCase


class TestManageNetwork(IntegrationTestCase):
    # def test_create_vlan_network_and_subnet(self):
    #     """Create vlan network using openstack CLI.
    #
    #     Check if network exists in OpenContrail and all properties are
    #     the same as used in create command call.
    #     """
    #     network = self.neutron.create_network({
    #         'network': {
    #             'name': 'test_public_1',
    #             'provider:network_type': 'vlan',
    #             'provider:segmentation_id': 10,
    #             'provider:physical_network': 'public',
    #             'admin_state_up': True,
    #         },
    #     })
    #     self.neutron.create_subnet({
    #         'subnet': {
    #             'name': 'test_subnet_1',
    #             'cidr': '192.168.2.0/24',
    #             'network_id': network['network']['id'],
    #             'gateway_ip': None,
    #             'ip_version': 4,
    #         }
    #     })
    #
    #     contrail_network = self.contrail_network_get(network['network']['id'])
    #     expected_network_subdict = {
    #         'segmentation_id': network['network']['provider:segmentation_id'],
    #         'physical_network': network['network']['provider:physical_network']
    #     }
    #     self.assertDictEqual(contrail_network['provider_properties'],
    #                          expected_network_subdict)

    def test_create_network_local(self):
        net = {
            'name': 'test_local_network',
            'provider:network_type': 'local',
            'admin_state_up': True,
        }
        q_net = self.q_create_network(**net)
        tf_net = self.tf_get_resource('virtual-network', q_net['network']['id'])

        self.assertIsNone(tf_net.get('provider_properties'))

    def test_create_network_flat(self):
        net = {
            'name': 'test_flat_network',
            'provider:network_type': 'flat',
            'provider:physical_network': 'public',
            'admin_state_up': True,
        }
        q_net = self.q_create_network(**net)
        tf_net = self.tf_get_resource('virtual-network', q_net['network']['id'])

        expected_provider_props = {
            'segmentation_id': None,
            'physical_network': q_net['network']['provider:physical_network']
        }
        self.assertIsNotNone(tf_net.get('provider_properties'))
        self.assertDictEqual(tf_net['provider_properties'],
                             expected_provider_props)

    def test_create_network_vlan(self):
        net = {
            'name': 'test_vlan_network',
            'provider:network_type': 'vlan',
            'provider:physical_network': 'public',
            'admin_state_up': True,
        }
        q_net = self.q_create_network(**net)
        tf_net = self.tf_get_resource('virtual-network', q_net['network']['id'])

        self.assertIsNotNone(tf_net.get('provider_properties'))
        self.assertEqual(tf_net['provider_properties']['physical_network'],
                         q_net['network']['provider:physical_network'])
        self.assertIsNotNone(tf_net['provider_properties']['segmentation_id'])

    def test_create_network_vlan_with_seg_id(self):
        net = {
            'name': 'test_vlan_10_network',
            'provider:network_type': 'vlan',
            'provider:physical_network': 'public',
            'provider:segmentation_id': 10,
            'admin_state_up': True,
        }
        q_net = self.q_create_network(**net)
        tf_net = self.tf_get_resource('virtual-network', q_net['network']['id'])

        expected_provider_props = {
            'segmentation_id': q_net['network']['provider:segmentation_id'],
            'physical_network': q_net['network']['provider:physical_network']
        }
        self.assertIsNotNone(tf_net.get('provider_properties'))
        self.assertDictEqual(tf_net['provider_properties'],
                             expected_provider_props)
