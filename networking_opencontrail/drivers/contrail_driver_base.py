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

from neutron.common import exceptions as neutron_exc
from neutron.db import quota_db  # noqa
from neutron.extensions import portbindings
from neutron.extensions import securitygroup
from neutron_lib.exceptions import allowedaddresspairs
from neutron_lib.exceptions import l3

from neutron_lib.api.definitions.portbindings import CAP_PORT_FILTER
from neutron_lib.constants import ATTR_NOT_SPECIFIED
from neutron_lib.constants import PORT_STATUS_ACTIVE
from neutron_lib import exceptions as neutron_lib_exc

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from networking_opencontrail.common import exceptions
from networking_opencontrail.common import utils

# Constant for max length of network interface names
# eg 'bridge' in the Network class or 'devname' in
# the VIF class
NIC_NAME_LEN = 14

LOG = logging.getLogger(__name__)

NEUTRON_CONTRAIL_PREFIX = 'NEUTRON'


def _raise_contrail_error(info, obj_name):
    exc_name = info.get('exception')
    if exc_name:
        if exc_name == 'BadRequest' and 'resource' not in info:
            info['resource'] = obj_name
        if exc_name == 'VirtualRouterNotFound':
            raise exceptions.HttpResponseError(info)
        if hasattr(l3, exc_name):
            raise getattr(l3, exc_name)(**info)
        if hasattr(securitygroup, exc_name):
            raise getattr(securitygroup, exc_name)(**info)
        if hasattr(allowedaddresspairs, exc_name):
            raise getattr(allowedaddresspairs, exc_name)(**info)
        if neutron_lib_exc and hasattr(neutron_lib_exc, exc_name):
            raise getattr(neutron_lib_exc, exc_name)(**info)
        # Few exceptions from neutron.common module are being moved
        # to neutron_lib.exceptions module leaving duplications.
        # Neutron_lib must have precedence over neutron.common.
        # That's why this check must be done at the very end.
        if hasattr(neutron_exc, exc_name):
            raise getattr(neutron_exc, exc_name)(**info)
    raise neutron_lib_exc.NeutronException(**info)


class OpenContrailDriversBase(object):

    def _parse_class_args(self):
        """Parse the contrailplugin.ini file.

        Opencontrail supports extension such as ipam, policy, these extensions
        can be configured in the plugin configuration file as shown below.
        Plugin then loads the specified extensions.
        contrail_extensions=ipam:<classpath>,policy:<classpath>
        """

        contrail_extensions = cfg.CONF.APISERVER.contrail_extensions
        # If multiple class specified for same extension, last one will win
        # according to DictOpt behavior
        for ext_name, ext_class in contrail_extensions.items():
            try:
                if not ext_class or ext_class == 'None':
                    self.supported_extension_aliases.append(ext_name)
                    continue
                ext_class = importutils.import_class(ext_class)
                ext_instance = ext_class()
                ext_instance.set_core(self)
                for method in dir(ext_instance):
                    for prefix in ['get', 'update', 'delete', 'create']:
                        if method.startswith('%s_' % prefix):
                            setattr(self, method,
                                    ext_instance.__getattribute__(method))
                self.supported_extension_aliases.append(ext_name)
            except Exception:
                LOG.exception("Contrail Backend Error")
                # Converting contrail backend error to Neutron Exception
                raise exceptions.InvalidContrailExtensionError(
                    ext_name=ext_name, ext_class=ext_class)
        self._build_auth_details()

    def _build_auth_details(self):
        pass

    def __init__(self):
        super(OpenContrailDriversBase, self).__init__()
        utils.register_vnc_api_options()

    def _create_resource(self, res_type, context, res_data):
        pass

    def _get_resource(self, res_type, context, id, fields):
        pass

    def _update_resource(self, res_type, context, id, res_data):
        pass

    def _delete_resource(self, res_type, context, id):
        pass

    def _list_resource(self, res_type, context, filters, fields):
        pass

    def _count_resource(self, res_type, context, filters):
        pass

    def _get_network(self, context, id, fields=None):
        return self._get_resource('network', context, id, fields)

    def create_network(self, context, network):
        """Creates a new Virtual Network."""
        return self._create_resource('network', context, network)

    def get_network(self, context, network_id, fields=None):
        """Get the attributes of a particular Virtual Network."""

        return self._get_network(context, network_id, fields)

    def update_network(self, context, network_id, network):
        """Updates the attributes of a particular Virtual Network."""

        return self._update_resource('network', context, network_id,
                                     network)

    def delete_network(self, context, network_id):
        """Creates a new Virtual Network.

        Deletes the network with the specified network identifier
        belonging to the specified tenant.
        """

        self._delete_resource('network', context, network_id)

    def get_networks(self, context, filters=None, fields=None):
        """Gets the list of Virtual Networks."""

        return self._list_resource('network', context, filters,
                                   fields)

    def get_networks_count(self, context, filters=None):
        """Gets the count of Virtual Network."""

        networks_count = self._count_resource('network', context, filters)
        return networks_count['count']

    def create_subnet(self, context, subnet):
        """Creates a new subnet, and assigns it a symbolic name."""

        if subnet['subnet']['host_routes'] != ATTR_NOT_SPECIFIED:
            if (len(subnet['subnet']['host_routes']) >
               cfg.CONF.max_subnet_host_routes):
                raise neutron_lib_exc.HostRoutesExhausted(
                    subnet_id=subnet['subnet'].get('id', _('new subnet')),
                    quota=cfg.CONF.max_subnet_host_routes)

        return self._create_resource('subnet', context, subnet)

    def _get_subnet(self, context, subnet_id, fields=None):
        return self._get_resource('subnet', context, subnet_id, fields)

    def get_subnet(self, context, subnet_id, fields=None):
        """Gets the attributes of a particular subnet."""

        return self._get_subnet(context, subnet_id, fields)

    def update_subnet(self, context, subnet_id, subnet):
        """Updates the attributes of a particular subnet."""

        return self._update_resource('subnet', context, subnet_id, subnet)

    def delete_subnet(self, context, subnet_id):
        """Delete a subnet.

        Deletes the subnet with the specified subnet identifier
        belonging to the specified tenant.
        """

        self._delete_resource('subnet', context, subnet_id)

    def get_subnets(self, context, filters=None, fields=None):
        """Gets the list of subnets."""

        return self._list_resource('subnet', context, filters, fields)

    def get_subnets_count(self, context, filters=None):
        """Gets the count of subnets."""

        subnets_count = self._count_resource('subnet', context, filters)
        return subnets_count['count']

    def _make_port_dict(self, port, fields=None):
        """filters attributes of a port based on fields."""

        if portbindings.VIF_TYPE in port and \
            port[portbindings.VIF_TYPE] == portbindings.VIF_TYPE_VHOST_USER:
            vhostuser = True
        else:
            vhostuser = False

        if not fields:
            port.update(self.base_binding_dict)
        else:
            for key in self.base_binding_dict:
                if key in fields:
                    port[key] = self.base_binding_dict[key]

        # Update bindings for vhostuser vif support
        if vhostuser:
            self._update_vhostuser_cfg_for_port(port)

        return port

    def _get_port(self, context, id, fields=None):
        return self._get_resource('port', context, id, fields)

    def _update_ips_for_port(self, context, network_id, port_id, original_ips,
                             new_ips):
        """Add or remove IPs from the port."""
        # These ips are still on the port and haven't been removed
        prev_ips = []

        # Remove all of the intersecting elements
        for original_ip in original_ips[:]:
            for new_ip in new_ips[:]:
                if ('ip_address' in new_ip
                        and original_ip['ip_address'] == new_ip['ip_address']):
                    original_ips.remove(original_ip)
                    new_ips.remove(new_ip)
                    prev_ips.append(original_ip)

        return new_ips, prev_ips

    def create_port(self, context, port):
        """Creates a port on the specified Virtual Network."""

        if (port['port'].get('port_security_enabled') is False
                and port['port'].get('allowed_address_pairs') == []):
            del port['port']['allowed_address_pairs']

        if (port.get('data')
                and not port['data'].get('resource', {}).get('tenant_id')
                and context['tenant_id']):
            port['data']['resource']['tenant_id'] = context['tenant_id']
        elif (port.get('port')
              and not port.get('port', {}).get('tenant_id')
              and context.tenant_id):
            port['port']['tenant_id'] = context.tenant_id

        port = self._create_resource('port', context, port)

        return port

    def get_port(self, context, port_id, fields=None):
        """Gets the attributes of a particular port."""

        return self._get_port(context, port_id, fields)

    def update_port(self, context, port_id, port):
        """Updates a port.

        Updates the attributes of a port on the specified Virtual
        Network.
        """
        original = self._get_port(context, port_id)
        if 'fixed_ips' in port['port']:
            _, prev_ips = self._update_ips_for_port(
                context, original['network_id'], port_id,
                original['fixed_ips'], port['port']['fixed_ips'])
            
            # (kamil.mankowski) New fixed ips are still in dict after
            # _update_ips_for_port. This reinsert previous ips on front
            # of list, so order is previous ips, new added ips. 
            port['port']['fixed_ips'][0:0] = prev_ips

        if 'binding:host_id' in port['port']:
            original['binding:host_id'] = port['port']['binding:host_id']

        if (port['port'].get('port_security_enabled') is False
                and port['port'].get('allowed_address_pairs') == []):
            del port['port']['allowed_address_pairs']

        return self._update_resource('port', context, port_id, port)

    def delete_port(self, context, port_id):
        """Deletes a port.

        Deletes a port on a specified Virtual Network,
        if the port contains a remote interface attachment,
        the remote interface is first un-plugged and then the port
        is deleted.
        """

        self._delete_resource('port', context, port_id)

    def bind_port(self, context):
        """Attempt to bind a port.

        :param context: PortContext instance describing the port

        Called inside transaction context on session, prior to
        create_port_precommit or update_port_precommit, to
        attempt to establish a port binding. If the driver is able to
        bind the port, it calls context.set_binding with the binding
        details.
        """

        port = {'port': context.current}
        port_id = context.current['id']

        self.update_port(context, port_id, port)

        vif_type = 'vrouter'
        vif_details = {CAP_PORT_FILTER: True}
        port_status = port.get('status', PORT_STATUS_ACTIVE)

        for segment in context.segments_to_bind:
            context.set_binding(segment['id'], vif_type,
                                vif_details, port_status)

    def get_ports(self, context, filters=None, fields=None):
        """Gets all ports.

        Retrieves all port identifiers belonging to the
        specified Virtual Network with the specfied filter.
        """

        return self._list_resource('port', context, filters, fields)

    def get_ports_count(self, context, filters=None):
        """Gets the count of ports."""

        ports_count = self._count_resource('port', context, filters)
        return ports_count['count']

    # Router API handlers
    def create_router(self, context, router):
        """Creates a router.

        Creates a new Logical Router, and assigns it
        a symbolic name.
        """

        return self._create_resource('router', context, router)

    def get_router(self, context, router_id, fields=None):
        """Gets the attributes of a router."""

        return self._get_resource('router', context, router_id, fields)

    def update_router(self, context, router_id, router):
        """Updates the attributes of a router."""

        return self._update_resource('router', context, router_id, router)

    def delete_router(self, context, router_id):
        """Deletes a router."""

        self._delete_resource('router', context, router_id)

    def get_routers(self, context, filters=None, fields=None):
        """Retrieves all router identifiers."""

        return self._list_resource('router', context, filters, fields)

    def get_routers_count(self, context, filters=None):
        """Gets the count of routers."""

        routers_count = self._count_resource('router', context, filters)
        return routers_count['count']

    def add_router_interface(self, context, router_id, interface_info):
        pass

    def remove_router_interface(self, context, router_id, interface_info):
        pass

    # Floating IP handlers
    def create_floatingip(self, context, floatingip):
        """Creates a floating IP.

        Creates a new floating IP, and assigns it a symbolic name.
        """

        return self._create_resource('floatingip', context, floatingip)

    def get_floatingip(self, context, ip_id, fields=None):
        """Gets the attributes of a floating IP."""

        return self._get_resource('floatingip', context, ip_id, fields)

    def update_floatingip(self, context, ip_id, floatingip):
        """Updates the attributes of a floating IP."""

        return self._update_resource('floatingip', context, ip_id,
                                     floatingip)

    def delete_floatingip(self, context, ip_id):
        """Deletes a floating IP."""

        self._delete_resource('floatingip', context, ip_id)

    # Route table handlers
    def create_route_table(self, context, table):
        """Creates a route table."""

        return self._create_resource('route_table', context, table)

    def get_route_table(self, context, table_id, fields=None):
        """Gets the attributes of a route table."""

        return self._get_resource('route_table', context, table_id, fields)

    def update_route_table(self, context, table_id, table):
        """Updates the attributes of a route table."""

        return self._update_resource('route_table', context, table_id,
                                     table)

    def delete_route_table(self, context, table_id):
        """Deletes a route table."""

        self._delete_resource('route_table', context, table_id)

    def get_route_tables(self, context, filters=None, fields=None):
        """Retrieves all route tables identifiers."""

        return self._list_resource('route_table', context, filters, fields)

    def get_route_tables_count(self, context, filters=None):
        """Gets the count of route tables."""

        route_tables_count = self._count_resource('route_table', context,
                                                  filters)
        return route_tables_count['count']

    # NAT instance handlers
    def create_nat_instance(self, context, instance):
        """Creates a NAT instance."""

        return self._create_resource('nat_instance', context, instance)

    def get_nat_instance(self, context, instance_id, fields=None):
        """Gets the attributes of a NAT instance."""

        return self._get_resource('nat_instance', context, instance_id,
                                  fields)

    def update_nat_instance(self, context, instance_id, instance):
        """Updates the attributes of a NAT instance."""

        return self._update_resource('nat_instance', context, instance_id,
                                     instance)

    def delete_nat_instance(self, context, instance_id):
        """Deletes a NAT instance."""

        self._delete_resource('nat_instance', context, instance_id)

    def get_nat_instances(self, context, filters=None, fields=None):
        """Retrieves all NAT instances identifiers."""

        return self._list_resource('nat_instance', context, filters, fields)

    def get_nat_instances_count(self, context, filters=None):
        """Gets the count of NAT instances."""

        nat_instances_count = self._count_resource('nat_instance', context,
                                                   filters)
        return nat_instances_count['count']

    # Security Group handlers
    def create_security_group(self, context, security_group):
        """Creates a Security Group."""

        return self._create_resource('security_group', context,
                                     security_group)

    def get_security_group(self, context, sg_id, fields=None, tenant_id=None):
        """Gets the attributes of a security group."""

        return self._get_resource('security_group', context, sg_id, fields)

    def update_security_group(self, context, sg_id, security_group):
        """Updates the attributes of a security group."""

        return self._update_resource('security_group', context, sg_id,
                                     security_group)

    def delete_security_group(self, context, sg_id):
        """Deletes a security group."""

        self._delete_resource('security_group', context, sg_id)

    def get_security_groups(self, context, filters=None, fields=None,
                            sorts=None, limit=None, marker=None,
                            page_reverse=False):
        """Retrieves all security group identifiers."""

        return self._list_resource('security_group', context,
                                   filters, fields)

    def get_security_groups_count(self, context, filters=None):
        """Gets the count of security groups."""

        groups_count = self._count_resource('security_group', context,
                                            filters)
        return groups_count['count']

    def get_security_group_rules_count(self, context, filters=None):
        """Gets the count of security group rules."""

        rules_count = self._count_resource('security_group_rule', context,
                                           filters)
        return rules_count['count']

    def create_security_group_rule(self, context, security_group_rule):
        """Creates a security group rule."""

        return self._create_resource('security_group_rule', context,
                                     security_group_rule)

    def delete_security_group_rule(self, context, sg_rule_id):
        """Deletes a security group rule."""

        self._delete_resource('security_group_rule', context, sg_rule_id)

    def get_security_group_rule(self, context, sg_rule_id, fields=None):
        """Gets the attributes of a security group rule."""

        return self._get_resource('security_group_rule', context,
                                  sg_rule_id, fields)

    def get_security_group_rules(self, context, filters=None, fields=None,
                                 sorts=None, limit=None, marker=None,
                                 page_reverse=False):
        """Retrieves all security group rules."""

        return self._list_resource('security_group_rule', context,
                                   filters, fields)
