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

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
try:
    from neutron_lib import context as neutron_context
except ImportError:
    from neutron import context as neutron_context
from neutron.db.db_base_plugin_v2 import NeutronDbPluginV2
from neutron.db.securitygroups_db import SecurityGroupDbMixin
from neutron.extensions.securitygroup import SecurityGroupNotFound

from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

LOG = logging.getLogger(__name__)


class OpenContrailSecurityGroupHandler(NeutronDbPluginV2,
                                       SecurityGroupDbMixin):
    """Security Group Handler for OpenContrail networking.

    Registers for the notification of security group updates.
    """
    def __init__(self, client, synchronize_groups=False):
        self.client = client
        self.subscribe()

        if synchronize_groups:
            self.synchronize_security_groups()

    def translate_security_group_id(self, context, group):
        if group['name'] == 'default':
            context.tenant = group['tenant_id']
            filters = {
                'name': 'default',
            }
            fields = ['tenant_id', 'id']
            groups = self.client.drv.get_security_groups(context,
                                                         filters=filters,
                                                         fields=fields)
            for remote in groups:
                if remote['tenant_id'] == group['tenant_id']:
                    group['id'] = remote['id']
                    break

        return group

    def delete_remote_group_rules(self, context, group_id):
        group = self.client.drv.get_security_group(context, group_id)
        for rule in group['security_group_rules']:
            self.client.delete_security_group_rule(context, rule['id'])

    def does_security_group_exist(self, context, group_id):
        try:
            self.client.drv.get_security_group(context, group_id)
            return True
        except SecurityGroupNotFound:
            return False

    def synchronize_group(self, context, group):
        LOG.debug("Syncing group... name: %(name)s, id: %(id)s",
                  {"name": group['name'], "id": group['id']})

        # Empty tenant breaks Contrail routines. Such group cannot be used
        # anyway, so it's not synchronized.
        if group['tenant_id'] == '':
            return

        group = self.translate_security_group_id(context, group)

        if self.does_security_group_exist(context, group['id']):
            self.client.update_security_group(context, group['id'], group)
            self.delete_remote_group_rules(context, group['id'])

            for rule in group['security_group_rules']:
                if rule.get('remote_group_id') is not None:
                    remote_group = self.get_security_group(
                        context,
                        rule['remote_group_id'])
                    remote_group = self.translate_security_group_id(
                        context,
                        remote_group)
                    rule['remote_group_id'] = remote_group['id']
                rule['security_group_id'] = group['id']
                self.client.create_security_group_rule(context, rule)
        else:
            self.client.create_security_group(context, group)

    def synchronize_security_groups(self):
        """Performs full synchronization of security groups with OpenContrail.

        Basically, it takes all groups available in Neutron and pushes their
        rules to OpenContrail node, so groups created in OpenContrail that
        are absent in Neutron remain unchanged.
        """
        LOG.info("Started syncing Security Groups with Contrail")

        context = neutron_context.get_admin_context()
        groups = self.get_security_groups(context)

        for group in groups:
            self.synchronize_group(context, group)

        LOG.info("Finished syncing Security Groups with Contrail")

    @log_helpers.log_method_call
    def create_security_group(self, resource, event, trigger, **kwargs):
        """Create Security Group callback handler for OpenContrail networking.

        Invokes back-end driver to create secutriy group in OpenContrail.
        """
        sg = kwargs.get('security_group')
        context = kwargs.get('context')
        try:
            self.client.create_security_group(context, sg)
        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a security group %(sg_id)s"
                          ": %(err)s", {"sg_id": sg["id"], "err": e})
                try:
                    self.client.delete_security_group(sg)
                except Exception:
                    LOG.exception("Failed to delete security group %s",
                                  sg['id'])

    @log_helpers.log_method_call
    def delete_security_group(self, resource, event, trigger, **kwargs):
        """Delete Security Group callback handler for OpenContrail networking.

        Invokes back-end driver to delete a secutriy group from OpenContrail.
        """
        sg = kwargs.get('security_group')
        context = kwargs.get('context')
        try:
            self.client.delete_security_group(context, sg)
        except Exception as e:
            LOG.error("Failed to delete security group %(sg_id)s"
                      ": %(err)s", {"sg_id": sg["id"], "err": e})

    @log_helpers.log_method_call
    def update_security_group(self, resource, event, trigger, **kwargs):
        """Update Security Group callback handler for OpenContrail networking.

        Invokes back-end driver to update secutriy group in OpenContrail.
        """
        sg = kwargs.get('security_group')
        sg_id = kwargs.get('security_group_id')
        context = kwargs.get('context')
        try:
            self.client.update_security_group(context, sg_id, sg)
        except Exception as e:
            LOG.error("Failed to update security group %(sg_id)s"
                      ": %(err)s"), {"sg_id": sg["id"], "err": e}

    @log_helpers.log_method_call
    def create_security_group_rule(self, resource, event, trigger, **kwargs):
        """Create Security Group Rule callback handler for OpenContrail.

        Invokes back-end driver to create secutriy group rule in OpenContrail.
        """
        sgr = kwargs.get('security_group_rule')
        context = kwargs.get('context')
        try:
            self.client.create_security_group_rule(context, sgr)
        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a security group %(sgr_id)s "
                          "rule: %(err)s",
                          {"sgr_id": sgr["id"], "err": e})
                try:
                    self.client.delete_security_group_rule(context, sgr)
                except Exception:
                    LOG.exception("Failed to delete security group "
                                  "rule %s", sgr['id'])

    @log_helpers.log_method_call
    def delete_security_group_rule(self, resource, event, trigger, **kwargs):
        """Delete Security Group rule callback handler for OpenContrail.

        Invokes back-end driver to delete secutriy group rule from
        OpenContrail.
        """
        sgr_id = kwargs.get('security_group_rule_id')
        context = kwargs.get('context')
        try:
            self.client.delete_security_group_rule(context, sgr_id)
        except Exception as e:
            LOG.error("Failed to delete security group %(sgr_id)s "
                      "rule: %(err)s",
                      {"sgr_id": sgr_id, "err": e})

    def subscribe(self):
        """Subscribe to the events related to security groups and rules."""
        registry.subscribe(
            self.create_security_group, resources.SECURITY_GROUP,
            events.AFTER_CREATE)
        registry.subscribe(
            self.update_security_group, resources.SECURITY_GROUP,
            events.AFTER_UPDATE)
        registry.subscribe(
            self.delete_security_group, resources.SECURITY_GROUP,
            events.BEFORE_DELETE)
        registry.subscribe(
            self.create_security_group_rule, resources.SECURITY_GROUP_RULE,
            events.AFTER_CREATE)
        registry.subscribe(
            self.delete_security_group_rule, resources.SECURITY_GROUP_RULE,
            events.BEFORE_DELETE)
