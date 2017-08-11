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
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.tests.unit import testlib_api
from neutron_lib.fixture import CallbackRegistryFixture

from networking_opencontrail.ml2 import opencontrail_sg_callback as sgc


class OpenContrailSecurityGroupTestCases(testlib_api.SqlTestCase):
    """Main test cases for Security Group Handler for OpenContrail.

    Tests all operations supported by OpenContrail. It invokes the back-end
    driver APIs as they would normally be invoked by the driver.
    """
    def setUp(self):
        super(OpenContrailSecurityGroupTestCases, self).setUp()
        self.registry_fixture = CallbackRegistryFixture()
        self.useFixture(self.registry_fixture)
        self.fake_api = mock.MagicMock()

        self.handler = sgc.OpenContrailSecurityGroupHandler(self.fake_api)

    def tearDown(self):
        super(OpenContrailSecurityGroupTestCases, self).tearDown()

    def test_create_security_group_hook(self):
        context = fake_plugin_context("ten-1")
        group = self.get_fake_security_group()

        registry.notify(resources.SECURITY_GROUP, events.AFTER_CREATE,
                        None, context=context, security_group=group)

        expected_calls = [
            mock.call.create_security_group(context, group),
        ]

        self.fake_api.assert_has_calls(expected_calls)

    def test_failed_create_security_group_hook(self):
        context = fake_plugin_context("ten-1")
        group = self.get_fake_security_group()

        self.fake_api.create_security_group = mock.Mock(
            side_effect=Exception('Test'))
        registry.notify(resources.SECURITY_GROUP, events.AFTER_CREATE,
                        None, context=context, security_group=group)

        expected_calls = [
            mock.call.create_security_group(context, group),
            mock.call.delete_security_group(group),
        ]

        self.fake_api.assert_has_calls(expected_calls)

    def test_update_security_group_hook(self):
        context = fake_plugin_context("ten-1")
        group = self.get_fake_security_group()

        registry.notify(resources.SECURITY_GROUP, events.AFTER_UPDATE,
                        None, context=context, security_group=group,
                        security_group_id=group['id'])

        expected_calls = [
            mock.call.update_security_group(context, group['id'], group),
        ]

        self.fake_api.assert_has_calls(expected_calls)

    def test_failed_update_security_group_hook(self):
        context = fake_plugin_context("ten-1")
        group = self.get_fake_security_group()

        self.fake_api.update_security_group = mock.Mock(
            side_effect=Exception())
        registry.notify(resources.SECURITY_GROUP, events.AFTER_UPDATE,
                        None, context=context, security_group=group,
                        security_group_id=group['id'])

        self.fake_api.update_security_group.assert_called_with(context,
                                                               group['id'],
                                                               group)

    def test_delete_security_group_hook(self):
        context = fake_plugin_context("ten-1")
        group = self.get_fake_security_group()
        self.fake_api.update_security_group = mock.Mock(
            side_effect=Exception())

        registry.notify(resources.SECURITY_GROUP, events.BEFORE_DELETE,
                        None, context=context, security_group=group)

        expected_calls = [
            mock.call.delete_security_group(context, group),
        ]

        self.fake_api.assert_has_calls(expected_calls)

    def test_create_security_group_rule(self):
        context = fake_plugin_context("ten-1")
        rule = self.get_fake_security_group_rule()

        registry.notify(resources.SECURITY_GROUP_RULE, events.AFTER_CREATE,
                        None, context=context, security_group_rule=rule)

        expected_calls = [
            mock.call.create_security_group_rule(context, rule),
        ]

        self.fake_api.assert_has_calls(expected_calls)

    def test_delete_security_group_rule(self):
        context = fake_plugin_context("ten-1")
        rule = self.get_fake_security_group_rule()

        registry.notify(resources.SECURITY_GROUP_RULE, events.BEFORE_DELETE,
                        None, context=context,
                        security_group_rule_id=rule['id'])

        expected_calls = [
            mock.call.delete_security_group_rule(context, rule['id']),
        ]

        self.fake_api.assert_has_calls(expected_calls)

    def get_fake_security_group_rule(self, rule_id="rul-1"):
        rule = {
            'id': rule_id,
        }
        return rule

    def get_fake_security_group(self, group_id="grp-1"):
        group = {
            'id': group_id,
        }
        return group


class fake_plugin_context(object):
    """ML2 Plugin context for testing purposes only."""

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.session = mock.MagicMock()
