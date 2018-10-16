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

from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

LOG = logging.getLogger(__name__)


class OpenContrailSecurityGroupHandler(object):
    """Security Group Handler for OpenContrail networking.

    Registers for the notification of security group updates.
    """
    def __init__(self, client):
        self.client = client
        self.subscribe()

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
    def delete_security_group(self, resource, event, trigger, payload=None):
        """Delete Security Group callback handler for OpenContrail networking.

        Invokes back-end driver to delete a secutriy group from OpenContrail.
        """
        sg = payload.latest_state
        context = payload.contex
        try:
            self.client.delete_security_group(context, sg)
        except Exception as e:
            LOG.error("Failed to delete security group %(sg_id)s"
                      ": %(err)s"), {"sg_id": sg["id"], "err": e}

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
