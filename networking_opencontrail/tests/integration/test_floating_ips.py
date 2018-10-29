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
import uuid

from networking_opencontrail.tests.base import IntegrationTestCase


class TestFloatingIPs(IntegrationTestCase):

    def setUp(self):
        super(TestFloatingIPs, self).setUp()

        net = {
            'name': 'test_subnet_network',
            'admin_state_up': True,
            'provider:network_type': 'vlan',
            'router:external': True,
        }
        self.test_network = self.q_create_network(**net)

        sub = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'dns_nameservers': ['10.10.11.2'],
            # TODO(mlastawi) not in final version
            'allocation_pools': [
                {
                    'start': '10.10.11.3',
                    'end': '10.10.11.254'
                }
            ],
        }
        self.test_subnet = self.q_create_subnet(**sub)

    def test_create_floatingip(self):

        fip = {
            'floating_network_id': self.test_network['network']['id'],
        }

        q_fip = self.q_create_floating_ip(**fip)

        expected = {
            'floating_ip_address':
                q_fip.get('floatingip', {}).get('floating_ip_address'),
            'project_id':
                uuid.UUID(q_fip.get('floatingip', {}).get('project_id')),
            'uuid':
                uuid.UUID(q_fip.get('floatingip', {}).get('id'))
        }

        tf_fip = self.tf_get_resource(
            'floating-ip', q_fip['floatingip']['id'])
        self.assertIsNotNone(tf_fip)

        contrail_dict = {
            'floating_ip_address':
                tf_fip.get('floating_ip_address'),
            'project_id':
                uuid.UUID(tf_fip.get('project_refs', [{}])[0].get('uuid')),
            'uuid':
                uuid.UUID(tf_fip.get('uuid'))
        }

        self.assertDictEqual(expected, contrail_dict)

    def test_delete_floatingip(self):

        fip = {
            'floating_network_id': self.test_network['network']['id'],
        }

        q_fip = self.q_create_floating_ip(**fip)
        tf_fip = self.tf_get_resource(
            'floating-ip', q_fip['floatingip']['id'])

        self.assertIsNotNone(tf_fip)

        self.q_delete_floating_ip(q_fip)

        req = self.tf_request_resource(
            'floating-ip', q_fip['floatingip']['id'])
        self.assertEqual(req.status_code, 404)

    def test_update_floatingip(self):
        """Update port association of floating ip

        To create this test, port has to be created.
        We need to create two networks and connect them by router.
        """

        pass
