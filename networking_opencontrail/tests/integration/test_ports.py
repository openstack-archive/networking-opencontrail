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

class TestPorts(IntegrationTestCase):

    def setUp(self):
        super(TestPorts, self).setUp()
        net = {
            'name': 'test_subnet_network',
            'admin_state_up': True,
            'provider:network_type': 'local',
        }
        self.test_network = self.q_create_network(**net)

    def test_create_port(self):
        port = {
            'name': 'test_port',
            'network_id': self.test_network['network']['id'],
        }

        q_port = self.q_create_port(**port)

        expected = {
            'id': uuid.UUID(q_port['port'].get('id')),
            'name': q_port['port'].get('name'),
            'port_security_enabled':
                q_port['port'].get('port_security_enabled'),
        }

        tf_port = self.tf_get_resource('virtual-machine-interface',
                                       q_port['port']['id'])
        self.assertIsNotNone(tf_port)

        contrail_dict = {
            'id': uuid.UUID(tf_port.get('uuid')),
            'name': tf_port.get('name'),
            'port_security_enabled':
                tf_port.get('port_security_enabled'),
        }

        self.assertDictEqual(expected, contrail_dict)

    @unittest.skip("Port update does not work")
    def test_update_port(self):
        port = {
            'name': 'test_port',
            'network_id': self.test_network['network']['id'],
        }

        q_port = self.q_create_port(**port)

        tf_port = self.tf_get_resource('virtual-machine-interface',
                                       q_port['port']['id'])
        self.assertIsNotNone(tf_port)

        changed_fields = {
            'name': 'new_name'
        }

        q_port = self.q_update_port(q_port, **changed_fields)

        expected = {
            'id': uuid.UUID(q_port['port'].get('id')),
            'name': q_port['port'].get('name'),
            'port_security_enabled':
                q_port['port'].get('port_security_enabled'),
        }

        tf_port = self.tf_get_resource(
            'virtual-machine-interface', q_port['port']['id'])

        contrail_dict = {
            'id': uuid.UUID(tf_port.get('uuid')),
            'name': tf_port.get('name'),
            'port_security_enabled': tf_port.get('port_security_enabled'),
        }

        self.assertDictEqual(expected, contrail_dict)

    def test_delete_port(self):
        port = {
            'name': 'test_port',
            'network_id': self.test_network['network']['id'],
        }

        q_port = self.q_create_port(**port)
        tf_port = self.tf_get_resource('virtual-machine-interface',
                                       q_port['port']['id'])

        self.assertIsNotNone(tf_port)

        self.q_delete_port(q_port)

        req = self.tf_request_resource('virtual-machine-interface',
                                       q_port['port']['id'])

        self.assertEqual(req.status_code, 404)
