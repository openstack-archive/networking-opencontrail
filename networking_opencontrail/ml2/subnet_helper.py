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
from neutron_lib.plugins import directory
from oslo_log import log as logging
from oslo_utils import excutils

LOG = logging.getLogger(__name__)

TF_DNS_DEVICE_OWNER = 'tf-compatibility:dns'


class SubnetSynchronizeHelper(object):
    """Subnet Handler for TungstenFabrich networking.

    Registers for the notification of some subnet updates,
    due to synchronize DNS servers address.
    """

    def __init__(self):
        self.subscribe()

    def before_delete_subnet(self, resource, event, trigger, payload):
        subnet_id = payload.resource_id
        context = payload.context

        try:
            dns_ports = self._get_tf_dns_for_subnet_in_neutron(context,
                                                               subnet_id)
            self._delete_ports_in_neutron(context, dns_ports)
        except Exception:
            LOG.exception("Cannot delete DNS port for subnet %s" % subnet_id)

    def before_delete_network(self, resource, event, trigger, payload):
        # TODO(kamman): subsribe for abort delete
        network_id = payload.resource_id
        context = payload.context

        try:
            dns_ports = self._get_tf_dns_for_network_in_neutron(context,
                                                                network_id)
            self._delete_ports_in_neutron(context, dns_ports)
        except Exception:
            LOG.exception("Cannot delete DNS port for network %s" % network_id)

    def subscribe(self):
        """Subscribe to the events related to subnet."""
        registry.subscribe(
            self.before_delete_subnet, resources.SUBNET,
            events.BEFORE_DELETE)
        registry.subscribe(
            self.before_delete_network, resources.NETWORK,
            events.BEFORE_DELETE)

    def create_tf_dns_in_neutron(self, context, subnet):
        dns_address = subnet.get('dns_server_address')
        if not dns_address:
            return

        port_data = {'tenant_id': subnet['tenant_id'],
                     'network_id': subnet['network_id'],
                     'fixed_ips': [{'ip_address': dns_address}],
                     'device_id': subnet['id'],
                     'device_owner': TF_DNS_DEVICE_OWNER,
                     'admin_state_up': True,
                     'name': 'tungstenfabric-dns-server'}
        try:
            self._core_plugin.create_port(context, {'port': port_data})
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create DNS port for subnet"
                          "%s with address %s" % (subnet['id'], dns_address))

    def _get_tf_dns_for_subnet_in_neutron(self, context, subnet_id):
        ports = self._core_plugin.get_ports(
            context,
            filters={'device_id': [subnet_id],
                     'device_owner': [TF_DNS_DEVICE_OWNER]})
        return ports

    def _get_tf_dns_for_network_in_neutron(self, context, network_id):
        ports = self._core_plugin.get_ports(
            context,
            filters={'network_id': [network_id],
                     'device_owner': [TF_DNS_DEVICE_OWNER]})
        return ports

    def _delete_ports_in_neutron(self, context, ports):
        for port in ports:
            self._core_plugin.delete_port(context, port['id'])

    @property
    def _core_plugin(self):
        return directory.get_plugin()
