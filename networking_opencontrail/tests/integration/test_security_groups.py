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


class TestSecurityGroups(IntegrationTestCase):

    def setUp(self):
        super(TestSecurityGroups, self).setUp()
        net = {
            'name': 'test_subnet_network',
            'admin_state_up': True,
            'provider:network_type': 'local',
        }
        self.test_network = self.q_create_network(**net)

    def test_create_security_group(self):
        security_group = {
            'name': 'test_security_group',
        }

        q_security_group = self.q_create_security_group(**security_group)

        expected = {
            'id': uuid.UUID(q_security_group['security_group'].get('id')),
            'name': q_security_group['security_group'].get('name')
        }

        tf_security_group = self.tf_get_resource('security-group',
                                                 q_security_group['security_group']['id'])
        self.assertIsNotNone(tf_security_group)

        contrail_dict = {
            'id': uuid.UUID(tf_security_group.get('uuid')),
            'name': tf_security_group.get('name')
        }

        self.assertDictEqual(expected, contrail_dict)

    @unittest.skip("Security group update does not work")
    def test_update_security_group(self):
        security_group = {
            'name': 'test_security_group',
        }

        q_security_group = self.q_create_security_group(**security_group)

        tf_security_group = self.tf_get_resource('security-group',
                                                 q_security_group['security_group']['id'])
        self.assertIsNotNone(tf_security_group)

        changed_fields = {
            'name': 'new_name'
        }

        q_security_group = self.q_update_security_group(q_security_group, **changed_fields)

        expected = {
            'id': uuid.UUID(q_security_group['security_group'].get('id')),
            'name': q_security_group['security_group'].get('name'),
        }

        tf_security_group = self.tf_get_resource(
            'security-group', q_security_group['security_group']['id'])

        contrail_dict = {
            'id': uuid.UUID(tf_security_group.get('uuid')),
            'name': tf_security_group.get('name'),
        }

        self.assertDictEqual(expected, contrail_dict)

    def test_delete_security_group(self):
        security_group = {
            'name': 'test_security_group',
        }

        q_security_group = self.q_create_security_group(**security_group)
        tf_security_group = self.tf_get_resource('security-group',
                                                 q_security_group['security_group']['id'])

        self.assertIsNotNone(tf_security_group)

        self.q_delete_security_group(q_security_group)

        req = self.tf_request_resource('security-group',
                                       q_security_group['security_group']['id'])

        self.assertEqual(req.status_code, 404)
