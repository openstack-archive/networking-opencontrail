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
import unittest
import uuid

from networking_opencontrail.tests.base import IntegrationTestCase


class TestSubnets(IntegrationTestCase):

    def setUp(self):
        super(TestSubnets, self).setUp()
        net = {
            'name': 'test_subnet_network',
            'admin_state_up': True,
            'provider:network_type': 'local',
        }
        self.test_network = self.q_create_network(**net)

    def test_create_subnet(self):
        subnet = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '10.10.11.3',
                    'end': '10.10.11.254'
                }
            ],
        }
        q_subnet = self.q_create_subnet(**subnet)

        expected = {
            'name': q_subnet['subnet']['name'],
            'network_id': q_subnet['subnet']['network_id'],
            'cdir': q_subnet['subnet']['cidr'],
            'gateway_ip': q_subnet['subnet']['gateway_ip'],
            'allocation_pools': q_subnet['subnet']['allocation_pools'],
            'id': q_subnet['subnet']['id'],
        }

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])

        tf_network = self.tf_get_resource('virtual-network',
                                          self.test_network['network']['id'])

        self.assertIsNotNone(sub)

        sub_ip = sub.get('subnet', {})
        contrail_dict = {
            'name': sub.get('subnet_name'),
            'network_id': tf_network.get('uuid'),
            'cdir': '/'.join([sub_ip.get('ip_prefix', ''),
                              str(sub_ip.get('ip_prefix_len', ''))]),
            'gateway_ip': sub.get('default_gateway'),
            'allocation_pools': sub.get('allocation_pools'),
            'id': sub.get('subnet_uuid'),
        }
        for pool in contrail_dict['allocation_pools']:
            pool.pop('vrouter_specific_pool')

        self.assertDictEqual(expected, contrail_dict)

    @unittest.skip("Subnet update does not work")
    def test_update_subnet(self):
        """Update subnet properties.

        Update of gateway is called which causes the exception.
        It happens even if gateway isn't changed explicitly.

        Exception message:
        "Update Subnet Failed: BadRequest: Bad subnet request: update of
        gateway is not supported."
        """
        subnet = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '10.10.11.3',
                    'end': '10.10.11.254'
                }
            ],
        }
        q_subnet = self.q_create_subnet(**subnet)

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])
        self.assertIsNotNone(sub)

        changed_fields = {
            'name': 'new_subnet_name',
        }
        q_subnet = self.q_update_subnet(q_subnet, **changed_fields)

        expected = {
            'name': q_subnet['subnet']['name'],
            'network_id': q_subnet['subnet']['network_id'],
            'cdir': q_subnet['subnet']['cidr'],
            'gateway_ip': q_subnet['subnet']['gateway_ip'],
            'allocation_pools': q_subnet['subnet']['allocation_pools'],
            'id': q_subnet['subnet']['id'],
        }

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])

        tf_network = self.tf_get_resource('virtual-network',
                                          self.test_network['network']['id'])

        sub_ip = sub.get('subnet')
        s = {
            'name': sub.get('subnet_name'),
            'network_id': tf_network.get('uuid'),
            'cdir': '/'.join([sub_ip.get('ip_prefix', ''),
                              str(sub_ip.get('ip_prefix_len', ''))]),
            'gateway_ip': sub.get('default_gateway'),
            'allocation_pools': sub.get('allocation_pools'),
            'id': sub.get('subnet_uuid'),
        }
        for pool in s['allocation_pools']:
            pool.pop('vrouter_specific_pool')

        self.assertDictEqual(expected, s)

    def test_delete_subnet(self):
        subnet = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '10.10.11.3',
                    'end': '10.10.11.254'
                }
            ],
        }

        q_subnet = self.q_create_subnet(**subnet)

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])
        self.assertIsNotNone(sub)

        self.q_delete_subnet(q_subnet)
        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])
        self.assertIsNone(sub)

    def _get_subnet_from_network(self, subnet_id, network_id):
        tf_network = self.tf_get_resource('virtual-network', network_id)
        ipam_refs = tf_network.get('network_ipam_refs')

        self.assertIsNotNone(ipam_refs)

        for ref in ipam_refs:
            subnets = ref.get('attr', {}).get('ipam_subnets', [])
            for sub in subnets:
                if uuid.UUID(subnet_id) == uuid.UUID(sub.get('subnet_uuid')):
                    return sub
        return None
