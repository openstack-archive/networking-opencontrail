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

from oslo_log import log as logging

import networking_opencontrail.drivers.drv_opencontrail as drv
from neutron_lib.plugins.ml2 import api

from networking_opencontrail.ml2 import opencontrail_sg_callback
from networking_opencontrail.l3.opencontrail_rt_callback import (
    TF_SNAT_DEVICE_OWNER)

LOG = logging.getLogger(__name__)


class OpenContrailMechDriver(api.MechanismDriver):
    """Main ML2 Mechanism driver from OpenContrail.

    This driver deals with all resources managed through ML2
    Plugin. Additionally, it manages the Security Groups
    Note: All the xxx_precommit() calls are ignored at the
    moment as there is no relevance for them in the OpenContrial
    SDN controller.
    """

    def initialize(self):
        self.drv = drv.OpenContrailDrivers()
        self.sg_handler = (
            opencontrail_sg_callback.OpenContrailSecurityGroupHandler(self))
        LOG.info("Initialization of networking-opencontrail plugin: COMPLETE")

    def create_network_precommit(self, context):
        pass

    def create_network_postcommit(self, context):
        """Create a network in OpenContrail."""
        network = {'network': context.current}
        try:
            self.drv.create_network(context._plugin_context, network)
        except Exception:
            LOG.exception("Create Network Failed")

    def delete_network_precommit(self, context):
        pass

    def delete_network_postcommit(self, context):
        """Delete a network from OpenContrail."""
        network = context.current
        try:
            self.drv.delete_network(context._plugin_context, network['id'])
        except Exception:
            LOG.exception("Delete Network Failed")

    def update_network_precommit(self, context):
        pass

    def update_network_postcommit(self, context):
        """Update an existing network in OpenContrail."""
        network = {'network': context.current}
        try:
            self.drv.update_network(context._plugin_context,
                                    network['network']['id'], network)
        except Exception:
            LOG.exception("Update Network Failed")

    def create_subnet_precommit(self, context):
        pass

    def create_subnet_postcommit(self, context):
        """Create a subnet in OpenContrail."""
        subnet = {'subnet': context.current}
        try:
            self.drv.create_subnet(context._plugin_context, subnet)
        except Exception:
            LOG.exception("Create Subnet Failed")

    def delete_subnet_precommit(self, context):
        pass

    def delete_subnet_postcommit(self, context):
        """Delete a subnet from OpenContrail."""
        subnet = context.current
        try:
            self.drv.delete_subnet(context._plugin_context, subnet['id'])
        except Exception:
            LOG.exception("Delete Subnet Failed")

    def update_subnet_precommit(self, context):
        pass

    def update_subnet_postcommit(self, context):
        """Update a subnet in OpenContrail."""
        subnet = {'subnet': context.current}
        try:
            self.drv.update_subnet(context._plugin_context,
                                   subnet['subnet']['id'], subnet)
        except Exception:
            LOG.exception("Update Subnet Failed")

    def create_port_precommit(self, context):
        pass

    def create_port_postcommit(self, context):
        """Create a port in OpenContrail."""
        port = {'port': dict(context.current)}

        if self._is_callback_to_omit(port['port']['device_owner']):
            return

        try:
            self.drv.create_port(context._plugin_context, port)
        except Exception:
            LOG.exception("Create Port Failed")

    def update_port_precommit(self, context):
        pass

    def update_port_postcommit(self, context):
        """Update a port in OpenContrail."""
        port = {'port': dict(context.current)}

        if self._is_callback_to_omit(port['port']['device_owner']):
            return

        try:
            self.drv.update_port(context._plugin_context,
                                 port['port']['id'], port)
        except Exception:
            LOG.exception("Update port Failed")

    def delete_port_precommit(self, context):
        pass

    def delete_port_postcommit(self, context):
        """Delete a port from OpenContrail."""
        port = context.current

        if self._is_callback_to_omit(port['device_owner']):
            return

        try:
            self.drv.delete_port(context._plugin_context, port['id'])
        except Exception:
            LOG.exception("Delete Port Failed")

    def bind_port(self, context):
        """Bind port in OpenContrail."""
        try:
            self.drv.bind_port(context)
        except Exception:
            LOG.exception("Bind Port Failed")

    def create_security_group(self, context, sg):
        """Create a Security Group in OpenContrail."""
        # vnc_openstack does not allow to create default security group
        if sg.get('name') == 'default':
            sg['name'] = 'default-openstack'
            sg['description'] = 'default-openstack security group'
        sec_g = {'security_group': sg}
        try:
            self.drv.create_security_group(context, sec_g)
        except Exception:
            LOG.exception('Failed to create Security Group %s' % sg)

    def delete_security_group(self, context, sg):
        """Delete a Security Group from OpenContrail."""
        sg_id = sg.get('id')
        try:
            self.drv.delete_security_group(context, sg_id)
        except Exception:
            LOG.exception('Failed to delete Security Group %s' % sg_id)

    def update_security_group(self, context, sg_id, sg):
        """Update a Security Group in OpenContrail."""
        sec_g = {'security_group': sg}
        try:
            self.drv.update_security_group(context, sg_id, sec_g)
        except Exception:
            LOG.exception('Failed to update Security Group %s' % sg_id)

    def create_security_group_rule(self, context, sgr):
        """Create a Security Group Rule in OpenContrail."""
        sgr_r = {'security_group_rule': sgr}
        try:
            self.drv.create_security_group_rule(context, sgr_r)
        except Exception:
            LOG.exception('Failed to create Security Group rule %s' % sgr)

    def delete_security_group_rule(self, context, sgr_id):
        """Delete a Security Group Rule from OpenContrail."""
        try:
            self.drv.delete_security_group_rule(context, sgr_id)
        except Exception:
            LOG.exception('Failed to delete Security Group rule %s' % sgr_id)

    def _is_callback_to_omit(self, device_owner):
        # Some device type have ports in Neutron, which are not necessary
        # in TungstenFabric and operation on it should be not propagated to TF
        omit_device_types = ["network:floatingip", TF_SNAT_DEVICE_OWNER]

        if device_owner in omit_device_types:
            LOG.debug("Port device is %s: omit callback to TungstenFabric" %
                      device_owner)
            return True
        return False
