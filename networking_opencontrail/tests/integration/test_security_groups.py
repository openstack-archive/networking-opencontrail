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
import unittest2 as unittest
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
        # GIVEN
        # WHEN
        q_security_group = self._q_create_some_security_group()

        # THEN
        security_group_id = q_security_group['security_group']['id']
        tf_security_group = self.tf_get_resource(
            'security-group',
            security_group_id
        )
        self.assertIsNotNone(tf_security_group)

        # AND
        expected = {
            'id': uuid.UUID(security_group_id),
            'name': q_security_group['security_group'].get('name')
        }
        contrail_dict = {
            'id': uuid.UUID(tf_security_group.get('uuid')),
            'name': tf_security_group.get('name')
        }

        self.assertDictEqual(expected, contrail_dict)

    def test_update_security_group(self):
        # GIVEN
        q_security_group = self._q_create_some_security_group()
        security_group_id = q_security_group['security_group']['id']
        tf_security_group = self.tf_get_resource(
            'security-group',
            security_group_id
        )
        self.assertIsNotNone(tf_security_group)

        changed_fields = {
            'name': 'new_name'
        }

        # WHEN
        q_security_group = self.q_update_security_group(
            q_security_group,
            **changed_fields
        )

        # THEN
        tf_security_group = self.tf_get_resource(
            'security-group', security_group_id
        )
        expected = {
            'id': uuid.UUID(security_group_id),
            'name': q_security_group['security_group'].get('name'),
        }
        # tf field `name` does not change; instead, `display_name` is updated
        contrail_dict = {
            'id': uuid.UUID(tf_security_group.get('uuid')),
            'name': tf_security_group.get('display_name'),
        }
        self.assertDictEqual(expected, contrail_dict)

    def test_delete_security_group(self):
        # GIVEN
        q_security_group = self._q_create_some_security_group()
        security_group_id = q_security_group['security_group']['id']
        tf_security_group = self.tf_get_resource(
            'security-group',
            security_group_id
        )
        self.assertIsNotNone(tf_security_group)

        # WHEN
        self.q_delete_security_group(q_security_group)

        # THEN
        req = self.tf_request_resource(
            'security-group',
            security_group_id
        )
        self.assertEqual(
            req.status_code,
            requests.status_codes.codes['not_found']
        )

    @unittest.skip("NTF-123")
    def test_create_rules_upon_security_group_creation(self):
        # GIVEN
        # WHEN
        q_security_group = self._q_create_some_security_group()

        # THEN
        tf_security_group = self.tf_get_resource(
            'security-group',
            q_security_group['security_group']['id']
        )

        q_sg_rules = self._q_extract_sg_rules(q_security_group)
        q_sg_rule_ids = [rule['id'] for rule in q_sg_rules]
        tf_sg_rules = self._tf_extract_sg_rules(tf_security_group)
        tf_sg_rule_ids = [rule['rule_uuid'] for rule in tf_sg_rules]

        expected_rule_ids = set(q_sg_rule_ids)
        tf_actual_rule_ids = set(tf_sg_rule_ids)
        self.assertEqual(expected_rule_ids, tf_actual_rule_ids)

    def test_create_security_group_rule(self):
        # GIVEN
        q_security_group = self._q_create_some_security_group()
        security_group_id = q_security_group['security_group']['id']

        starting_tf_sg_rule_ids = self._tf_sg_rule_ids(security_group_id)
        some_protocol = "udp"
        some_ethertype = "IPv6"

        # WHEN
        new_q_rule = self._q_create_some_sg_rule(
            security_group_id,
            protocol=some_protocol,
            ethertype=some_ethertype
        )

        # THEN
        new_rule_id = new_q_rule['security_group_rule']['id']
        updated_tf_sg_rule_ids = self._tf_sg_rule_ids(security_group_id)

        expected_new_rule_ids = {new_rule_id}
        new_tf_sg_rule_ids = \
            set(updated_tf_sg_rule_ids) - set(starting_tf_sg_rule_ids)
        self.assertEqual(expected_new_rule_ids, new_tf_sg_rule_ids)

        # AND
        updated_tf_sg_rules = self._tf_sg_rules(security_group_id)

        expected_parameters = (some_protocol, some_ethertype)
        # we can take the 0-th element, because exactly one rule is expected
        tf_new_rule_parameters = [
            (rule['protocol'], rule['ethertype'])
            for rule
            in updated_tf_sg_rules
            if rule['rule_uuid'] == new_rule_id
        ][0]
        self.assertEqual(expected_parameters, tf_new_rule_parameters)

    def test_delete_security_group_rule(self):
        # GIVEN
        q_security_group = self._q_create_some_security_group()
        security_group_id = q_security_group['security_group']['id']

        new_q_rule = self._q_create_some_sg_rule(security_group_id)
        new_rule_id = new_q_rule['security_group_rule']['id']

        starting_tf_sg_rule_ids = self._tf_sg_rule_ids(security_group_id)

        # WHEN
        self.q_delete_security_group_rule(new_q_rule)

        # THEN
        updated_tf_sg_rule_ids = self._tf_sg_rule_ids(security_group_id)

        expected_deleted_rule_ids = {new_rule_id}
        deleted_tf_sg_rule_ids = \
            set(starting_tf_sg_rule_ids) - set(updated_tf_sg_rule_ids)
        self.assertEqual(expected_deleted_rule_ids, deleted_tf_sg_rule_ids)

    def _q_create_some_security_group(
            self,
            name="test_security_group"
    ):
        security_group = {
            'name': name,
        }
        return self.q_create_security_group(**security_group)

    def _q_create_some_sg_rule(
            self,
            security_group_id,
            direction="ingress",
            protocol="tcp",
            ethertype="IPv4",
            port_range_min="80",
            port_range_max="90",
            description="",
            remote_group_id=None
    ):
        return self.q_create_security_group_rule(
            security_group_id,
            direction=direction,
            protocol=protocol,
            ethertype=ethertype,
            port_range_min=port_range_min,
            port_range_max=port_range_max,
            description=description,
            remote_group_id=remote_group_id
        )

    def _tf_sg_rule_ids(self, security_group_id):
        tf_sg_rules = self._tf_sg_rules(security_group_id)
        tf_rule_ids = [rule['rule_uuid'] for rule in tf_sg_rules]
        return tf_rule_ids

    def _tf_sg_rules(self, security_group_id):
        tf_security_group = self.tf_get_resource(
            'security-group',
            security_group_id
        )
        return self._tf_extract_sg_rules(tf_security_group)

    @staticmethod
    def _q_extract_sg_rules(q_security_group):
        return q_security_group['security_group']['security_group_rules']

    @staticmethod
    def _tf_extract_sg_rules(tf_security_group):
        return tf_security_group['security_group_entries']['policy_rule']
