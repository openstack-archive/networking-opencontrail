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


class SubnetDNSCompatibilityIntegrator(object):
    """Subnet DNS Compatibility Integrator for TungstenFabrich networking.

    Registers for the notification of some subnet updates,
    due to synchronize DNS servers address.
    """

    def __init__(self, tf_driver):
        self.tf_driver = tf_driver
        self.subscribe()

    def before_delete_subnet(self, resource, event, trigger, payload):
        subnet_id = payload.resource_id
        context = payload.context

        try:
            dns_ports = self._get_tf_dns_for_subnet_in_neutron(context,
                                                               subnet_id)
            self._delete_ports_in_neutron(context, dns_ports)
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.exception(
                    "Cannot delete DNS port for subnet %s" % subnet_id)

    def before_delete_network(self, resource, event, trigger, payload=None):
        network_id = payload.resource_id
        context = payload.context

        try:
            dns_ports = self._get_tf_dns_for_network_in_neutron(context,
                                                                network_id)
            self._delete_ports_in_neutron(context, dns_ports)
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.exception(
                    "Cannot delete DNS port for network %s" % network_id)

    def abort_delete_subnet(self, resource, event, trigger, payload=None):
        subnet_id = payload.resource_id
        context = payload.context

        try:
            tf_subnet = self.tf_driver.get_subnet(context, subnet_id)
            self.add_dns_port_for_subnet(context, tf_subnet)
        except Exception:
            LOG.exception(
                "Cannot synchronize DNS port for subnet %s" % subnet_id)

    def abort_delete_network(self, resource, event, trigger, payload=None):
        network_id = payload.resource_id
        context = payload.context
        subnets = self._core_plugin.get_subnets(
            context, filters={'network_id': [network_id]})

        for subnet in subnets:
            try:
                tf_subnet = self.tf_driver.get_subnet(context, subnet['id'])
                self.add_dns_port_for_subnet(context, tf_subnet)
            except Exception:
                LOG.exception(
                    "Cannot synchronize DNS port for subnet %s" % subnet['id'])

    def subscribe(self):
        """Subscribe to the events related to subnet."""
        registry.subscribe(
            self.before_delete_subnet, resources.SUBNET,
            events.BEFORE_DELETE)
        registry.subscribe(
            self.before_delete_network, resources.NETWORK,
            events.BEFORE_DELETE)
        registry.subscribe(
            self.abort_delete_subnet, resources.SUBNET,
            events.ABORT_DELETE)
        registry.subscribe(
            self.abort_delete_network, resources.NETWORK,
            events.ABORT_DELETE)

    def add_dns_port_for_subnet(self, context, subnet):
        dns_address = subnet.get('dns_server_address')
        if not dns_address:
            return

        existed_ports = self._get_tf_dns_for_subnet_in_neutron(
            context, subnet['id'])
        for port in existed_ports:
            for fixed_ip in port.get('fixed_ips', []):
                if dns_address == fixed_ip.get('ip_address', None):
                    return

        self._create_tf_dns_in_neutron(context, subnet)

    def _create_tf_dns_in_neutron(self, context, subnet):
        port_data = {'tenant_id': subnet['tenant_id'],
                     'network_id': subnet['network_id'],
                     'fixed_ips': [
                         {'ip_address': subnet['dns_server_address']}],
                     'device_id': subnet['id'],
                     'device_owner': TF_DNS_DEVICE_OWNER,
                     'admin_state_up': True,
                     'name': 'tungstenfabric-dns-service'}
        try:
            self._core_plugin.create_port(context, {'port': port_data})
        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.exception("Failed to create DNS port for subnet"
                              "%s with address %s" % (
                                  subnet['id'], subnet['dns_server_address']))

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
