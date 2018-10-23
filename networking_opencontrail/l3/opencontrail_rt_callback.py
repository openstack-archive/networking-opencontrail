# Copyright (c) 2017 OpenStack Foundation
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
from copy import deepcopy

from neutron.db import common_db_mixin
from neutron.db import extraroute_db
from neutron.db import l3_agentschedulers_db
from neutron.db import l3_dvr_db
from neutron.db import l3_gwmode_db
from neutron_lib import constants as const
from neutron_lib.db import api as db_api
from neutron_lib.plugins import constants as plugin_const
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import excutils

import networking_opencontrail.drivers.drv_opencontrail as driver
import networking_opencontrail.l3.tungstenfabric_api as tf_api

LOG = logging.getLogger(__name__)

TF_SNAT_DEVICE_OWNER = 'tf-compatibility:snat'


class OpenContrailRouterHandler(common_db_mixin.CommonDbMixin,
                                extraroute_db.ExtraRoute_db_mixin,
                                l3_dvr_db.L3_NAT_with_dvr_db_mixin,
                                l3_gwmode_db.L3_NAT_db_mixin,
                                l3_agentschedulers_db.L3AgentSchedulerDbMixin):
    """Router Handler for OpenContrail networking.

    Registers for the notification of router updates.
    """
    supported_extension_aliases = ["dvr", "router", "ext-gw-mode",
                                   "extraroute"]

    def __init__(self):
        super(OpenContrailRouterHandler, self).__init__()
        self.driver = driver.OpenContrailDrivers()
        self.tf_connector = tf_api.TungstenFabricApiConnector()

    def get_plugin_type(self):
        return plugin_const.L3

    def get_plugin_description(self):
        """Returns string description of the plugin."""
        return ("L3 Router Service Plugin for basic L3 forwarding "
                "using OpenContrail.")

    @log_helpers.log_method_call
    def create_router(self, context, router):
        """Create Router callback handler for OpenContrail networking.

        Invokes back-end driver to create router in OpenContrail.
        """
        created_router = {}
        try:
            created_router = self.driver.create_router(context, router)

            gw_fixed_ips = self._get_gw_fixed_ips(router)
            if gw_fixed_ips:
                created_router["external_gateway_info"][
                    "external_fixed_ips"] = gw_fixed_ips

            self._sync_snat_interfaces(context, created_router['id'],
                                       created_router)

            session = db_api.get_writer_session()
            with session.begin(subtransactions=True):
                super(OpenContrailRouterHandler,
                      self).create_router(context, {'router': created_router})
        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to create a router %(id)s: %(err)s",
                          {"id": created_router.get('id', ''), "err": e})
                try:
                    if created_router:
                        tf_router = self.driver.delete_router(
                            context, created_router['id'])
                        self._sync_snat_interfaces(
                            context, tf_router['id'], tf_router)
                except Exception:
                    LOG.exception("Failed to rollback creation router %s",
                                  created_router.get('id', ''))

        return created_router

    @log_helpers.log_method_call
    def delete_router(self, context, router_id):
        """Delete Router callback handler for OpenContrail networking.

        Invokes back-end driver to delete router from OpenContrail.
        """
        session = db_api.get_writer_session()
        with session.begin(subtransactions=True):
            super(OpenContrailRouterHandler, self).delete_router(context,
                                                                 router_id)

            try:
                self.driver.delete_router(context, router_id)
                self._sync_snat_interfaces(context, router_id)
            except Exception as e:
                LOG.error("Failed to delete router %(id)s: %(err)s",
                          {"id": router_id, "err": e})

    @log_helpers.log_method_call
    def update_router(self, context, router_id, router):
        """Update Router callback handler for OpenContrail networking.

        Invokes back-end driver to update router in OpenContrail.
        """
        if 'name' in router['router']:
            LOG.warning("OpenContrail doesn't allow for changing router "
                        "%(id)s name to %(name)s",
                        {"id": router_id, "name": router['router']['name']})
        prev_router = None
        tf_router = None
        router_dict = None
        try:
            prev_router = self.driver.get_router(context, router_id)

            router_data = self._prepare_updated_router(router, prev_router)

            tf_router = self.driver.update_router(context, router_id,
                                                  router_data)
            self._sync_snat_interfaces(context, router_id, tf_router)

            session = db_api.get_writer_session()
            with session.begin(subtransactions=True):
                router_dict = super(OpenContrailRouterHandler,
                                    self).update_router(context, router_id,
                                                        router)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to update router %(id)s: %(err)s",
                          {"id": router_id, "err": e})
                try:
                    if prev_router and tf_router:
                        tf_router = self.driver.update_router(
                            context, router_id, {'router': prev_router})
                        self._sync_snat_interfaces(
                            context, router_id, tf_router)
                except Exception:
                    LOG.exception("Failed to rollback update router %s",
                                  router_id)

        return router_dict

    @log_helpers.log_method_call
    def add_router_interface(self, context, router_id, interface_info):
        """Add Router Interface callback handler for OpenContrail.

        Invokes back-end driver to add router interface in OpenContrail.
        """
        session = db_api.get_writer_session()
        with session.begin(subtransactions=True):
            new_router = super(
                OpenContrailRouterHandler, self).add_router_interface(
                    context, router_id, interface_info)

        try:
            interface_info = dict(new_router)
            del interface_info['subnet_id']
            self.driver.add_router_interface(context, router_id,
                                             interface_info)
        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error("Failed to add interface to router %(id)s: "
                          "%(err)s", {"id": router_id, "err": e})
                try:
                    self.remove_router_interface(context, router_id,
                                                 interface_info)
                except Exception:
                    LOG.exception("Failed to delete interface of router %s",
                                  router_id)

        return new_router

    @log_helpers.log_method_call
    def remove_router_interface(self, context, router_id, interface_info):
        """Remove router interface callback handler for OpenContrail.

        Invokes back-end driver to remove router interface from OpenContrail.
        """
        session = db_api.get_writer_session()
        with session.begin(subtransactions=True):
            new_router = super(
                OpenContrailRouterHandler, self).remove_router_interface(
                    context, router_id, interface_info)

        try:
            self.driver.remove_router_interface(context, router_id,
                                                interface_info)
        except Exception as e:
            LOG.error("Failed to remove router %(id)s interface: "
                      "%(err)s", {"id": router_id, "err": e})

        return new_router

    @log_helpers.log_method_call
    def create_floatingip(self, context, floatingip,
                          initial_status=const.FLOATINGIP_STATUS_ACTIVE):
        fip = floatingip['floatingip']

        if fip.get('port_id') is None:
            initial_status = const.FLOATINGIP_STATUS_DOWN

        session = db_api.get_writer_session()
        with session.begin(subtransactions=True):
            try:
                fip_dict = super(
                    OpenContrailRouterHandler, self).create_floatingip(
                    context, floatingip, initial_status)
            except Exception as e:
                LOG.error("Failed to create floating ip %(fip)s: "
                          "%(err)s", {"fip": fip, "err": e})
                raise

        try:
            self.driver.create_floatingip(context,
                                          {'floatingip': fip_dict})
            return fip_dict
        except Exception as e:
            LOG.error("Failed to create floating ip %(fip)s: "
                      "%(err)s", {"fip": fip, "err": e})
            with session.begin(subtransactions=True):
                super(OpenContrailRouterHandler, self).delete_floatingip(
                    context, fip_dict['id'])
            raise

    @log_helpers.log_method_call
    def update_floatingip(self, context, floatingip_id, floatingip):
        session = db_api.get_writer_session()

        with session.begin(subtransactions=True):
            try:
                old_fip = super(
                    OpenContrailRouterHandler, self).get_floatingip(
                    context, floatingip_id)

                fip_dict = super(
                    OpenContrailRouterHandler, self).update_floatingip(
                    context, floatingip_id, floatingip)
            except Exception as e:
                LOG.error("Failed to update floating ip %(id)s: "
                          "%(err)s", {"id": floatingip_id, "err": e})
                raise

        # Update status based on association
        if fip_dict.get('port_id') is None:
            fip_dict['status'] = const.FLOATINGIP_STATUS_DOWN
        else:
            fip_dict['status'] = const.FLOATINGIP_STATUS_ACTIVE

        try:
            with session.begin(subtransactions=True):
                self.update_floatingip_status(context, floatingip_id,
                                              fip_dict['status'])

            self.driver.update_floatingip(context, floatingip_id,
                                          {'floatingip': fip_dict})
            return fip_dict
        except Exception as e:
            LOG.error("Failed to update floating ip status %(id)s: "
                      "%(err)s", {"id": floatingip_id, "err": e})

            with session.begin(subtransactions=True):
                try:
                    super(OpenContrailRouterHandler, self).update_floatingip(
                        context, floatingip_id, {'floatingip': old_fip})
                except Exception as e:
                    LOG.error("Failed to repair floating ip %(id)s: "
                              "%(err)s", {"id": floatingip_id, "err": e})
                    raise

                try:
                    self.update_floatingip_status(context, floatingip_id,
                                                  old_fip['status'])
                except Exception as e:
                    LOG.error("Failed to repair floating ip status %(id)s: "
                              "%(err)s", {"id": floatingip_id, "err": e})
                    raise
            raise

    @log_helpers.log_method_call
    def delete_floatingip(self, context, floatingip_id):
        session = db_api.get_writer_session()

        with session.begin(subtransactions=True):
            try:
                old_fip = super(
                    OpenContrailRouterHandler, self).get_floatingip(
                    context, floatingip_id)

                super(OpenContrailRouterHandler,
                      self).delete_floatingip(context, floatingip_id)
            except Exception as e:
                LOG.error("Failed to delete floating ip %(id)s: "
                          "%(err)s", {"id": floatingip_id, "err": e})
                raise

        try:
            self.driver.delete_floatingip(context, floatingip_id)
        except Exception as e:
            LOG.error("Failed to delete floating ip %(id)s: "
                      "%(err)s", {"id": floatingip_id, "err": e})

            try:
                with session.begin(subtransactions=True):
                    super(OpenContrailRouterHandler,
                          self).create_floatingip(context,
                                                  {'floatingip': old_fip},
                                                  old_fip['status'])
            except Exception as e:
                LOG.error("Failed to undelete floating ip %(id)s: "
                          "%(err)s", {"id": floatingip_id, "err": e})
                raise

            raise

    @log_helpers.log_method_call
    def disassociate_floatingips(self, context, port_id, do_notify=True):
        session = db_api.get_writer_session()

        try:
            with session.begin(subtransactions=True):
                filters = {'port_id': [port_id]}
                fip_dicts = self.get_floatingips(context,
                                                 filters=filters)
                router_ids = super(OpenContrailRouterHandler,
                                   self).disassociate_floatingips(context,
                                                                  port_id,
                                                                  do_notify)
                for fip_dict in fip_dicts:
                    fip_dict = self.get_floatingip(context, fip_dict['id'])
                    fip_dict['status'] = const.FLOATINGIP_STATUS_DOWN
                    self.update_floatingip_status(context, fip_dict['id'],
                                                  fip_dict['status'])
                    self.driver.update_floatingip(context, fip_dict['id'],
                                                  {'floatingip': fip_dict})
            return router_ids
        except Exception as e:
            LOG.error("Failed to disassociate floating ips on port %(id)s: "
                      "%(err)s", {"id": port_id, "err": e})
            raise

    def _get_gw_fixed_ips(self, router):
        external_gw = router["router"].get("external_gateway_info", None)
        if external_gw and "external_fixed_ips" in external_gw:
            return list(external_gw['external_fixed_ips'])
        return None

    def _prepare_updated_router(self, router, prev_router):
        router_data = deepcopy(router)
        for key in prev_router:
            if key not in router_data['router']:
                router_data['router'][key] = prev_router[key]
        return router_data

    def _sync_snat_interfaces(self, context, router_id, router=None):
        neutron_interfaces = self._snat_interfaces_in_neutron(context,
                                                              router_id)
        new_snat_ips = []
        if (router and 'external_gateway_info' in router and
                router['external_gateway_info']):
            new_snat_ips = self.tf_connector.get_snat_ips(context, router_id)

        deleted_interfaces = []
        for interface in neutron_interfaces:
            # This interaces were created by plugin with only one IP
            ip_address = interface['fixed_ips'][0]['ip_address']
            if ip_address not in new_snat_ips:
                deleted_interfaces.append(interface)
            else:
                new_snat_ips.remove(ip_address)

        for interface in deleted_interfaces:
            self._delete_snat_interface_in_neutron(context, interface)

        for new_ip in new_snat_ips:
            self._create_snat_interface_in_neutron(
                context, router['external_gateway_info'],
                router_id, new_ip)

    def _create_snat_interface_in_neutron(self, context, external_gateway_info,
                                          router_id, snat_ip):
        port_data = {'tenant_id': context.tenant_id,
                     'network_id': external_gateway_info['network_id'],
                     'fixed_ips': [{'ip_address': snat_ip}],
                     'device_id': router_id,
                     'device_owner': TF_SNAT_DEVICE_OWNER,
                     'admin_state_up': True,
                     'name': 'tungstenfabric-snat-interface'
                     }
        port = super(OpenContrailRouterHandler, self)._core_plugin.create_port(
            context.elevated(), {'port': port_data})

        return port

    def _snat_interfaces_in_neutron(self, context, router_id):
        ports = super(OpenContrailRouterHandler, self)._core_plugin.get_ports(
            context, filters={'device_id': [router_id],
                              'device_owner': [TF_SNAT_DEVICE_OWNER]})
        return ports

    def _delete_snat_interface_in_neutron(self, context, snat_interface):
        super(OpenContrailRouterHandler, self)._core_plugin.delete_port(
            context, snat_interface['id'])
