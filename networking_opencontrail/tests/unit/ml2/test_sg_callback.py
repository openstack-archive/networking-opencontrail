# Copyright (c) 2016 OpenStack Foundation
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

from neutron.callbacks import events
from neutron.callbacks import resources

from neutron.tests.unit import testlib_api

from networking_opencontrail.ml2 import opencontrail_sg_callback as sgc


class SecurityGroupTestCases(testlib_api.SqlTestCase):
    """Test cases for ML2 security group handler.

    Callbacks for create, delete, and update operations of security
    groups and rules.
    """

    def setUp(self):
        super(SecurityGroupTestCases, self).setUp()
        self.sg_handler = sgc.OpenContrailSecurityGroupHandler(mock.Mock())
        self.client = self.sg_handler.client

    def tearDown(self):
        super(SecurityGroupTestCases, self).tearDown()

    @staticmethod
    def _get_mock_network_operation_context():
        current = {'status': 'ACTIVE',
                   'subnets': [],
                   'name': 'net1',
                   'provider:physical_network': None,
                   'admin_state_up': True,
                   'tenant_id': 'test-tenant',
                   'provider:network_type': 'local',
                   'router:external': False,
                   'shared': False,
                   'id': 'd894125634',
                   'provider:segmentation_id': None}
        context = mock.Mock(current=current)
        return context

    @classmethod
    def _get_callback_params(cls, params):
        """Returns parameters for calling security group operations

        """
        params['resource'] = resources.SECURITY_GROUP
        params['event'] = events.AFTER_CREATE
        params['trigger'] = mock.Mock()
        params['context'] = cls._get_mock_network_operation_context()

    @classmethod
    def _get_secgroup_params(cls, params):
        """Adds parameters for calling security group rule operations

        """
        params['security_group'] = 'secgroup-1'
        params['security_group_id'] = '982540-abc3152-54989dd'
        params['security_group_rule'] = 'secgroup-rule-1'
        params['security_group_rule_id'] = '627d-21345154a-bc787'

    def test_create_security_group(self):
        kwargs = {}
        self._get_callback_params(kwargs)
        self._get_secgroup_params(kwargs)
        self.sg_handler.create_security_group(**kwargs)
        self.sg_handler.client.create_security_group.assert_called_with(
            kwargs['context'],
            kwargs['security_group'])

    def test_delete_security_group(self):
        kwargs = {}
        self._get_callback_params(kwargs)
        self._get_secgroup_params(kwargs)
        self.sg_handler.delete_security_group(**kwargs)
        self.sg_handler.client.delete_security_group.assert_called_with(
            kwargs['context'],
            kwargs['security_group'])

    def test_update_security_group(self):
        kwargs = {}
        self._get_callback_params(kwargs)
        self._get_secgroup_params(kwargs)
        self.sg_handler.update_security_group(**kwargs)
        self.sg_handler.client.update_security_group.assert_called_with(
            kwargs['context'],
            kwargs['security_group_id'],
            kwargs['security_group'])

    def test_create_security_group_rule(self):
        kwargs = {}
        self._get_callback_params(kwargs)
        self._get_secgroup_params(kwargs)
        self.sg_handler.create_security_group_rule(**kwargs)
        self.sg_handler.client.create_security_group_rule.assert_called_with(
            kwargs['context'],
            kwargs['security_group_rule'])

    def test_delete_security_group_rule(self):
        kwargs = {}
        self._get_callback_params(kwargs)
        self._get_secgroup_params(kwargs)
        self.sg_handler.delete_security_group_rule(**kwargs)
        self.sg_handler.client.delete_security_group_rule.assert_called_with(
            kwargs['context'],
            kwargs['security_group_rule_id'])
