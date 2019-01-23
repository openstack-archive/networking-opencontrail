# Copyright (c) 2019 OpenStack Foundation
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

from neutron.objects import router as l3_obj
from neutron.services.l3_router.service_providers import base
from neutron_lib.callbacks import events
from neutron_lib.callbacks import priority_group
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import constants as q_const
from neutron_lib.plugins import constants as plugin_constants
from neutron_lib.plugins import directory
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

import networking_opencontrail.drivers.drv_opencontrail as driver

LOG = logging.getLogger(__name__)


@registry.has_registry_receivers
class TFL3ServiceProvider(base.L3ServiceProvider):
    @log_helpers.log_method_call
    def __init__(self, l3_plugin):
        super(TFL3ServiceProvider, self).__init__(l3_plugin)
        self.driver = driver.OpenContrailDrivers()
        self.provider = __name__ + "." + self.__class__.__name__

    @property
    def _flavor_plugin(self):
        try:
            return self._flavor_plugin_ref
        except AttributeError:
            self._flavor_plugin_ref = directory.get_plugin(
                plugin_constants.FLAVORS)
            return self._flavor_plugin_ref

    def _validate_l3_flavor(self, context, router_id, flavor_id=None):
        if router_id is None or flavor_id is q_const.ATTR_NOT_SPECIFIED:
            return False
        if not flavor_id:
            router = l3_obj.Router.get_object(context, id=router_id)
            if router.flavor_id is None:
                return False
            flavor_id = router.flavor_id
            # flavor = self._flavor_plugin.get_flavor(context,
            #                                         router.flavor_id)
            # flavor_id = flavor['id']

        provider = self._flavor_plugin.get_flavor_next_provider(
            context, flavor_id)[0]
        return str(provider['driver']) == self.provider

    def _update_floatingip_status(self, context, fip_dict):
        port_id = fip_dict.get('port_id')
        status = q_const.ACTIVE if port_id else q_const.DOWN
        l3_obj.FloatingIP.update_object(context, {'status': status},
                                        id=fip_dict['id'])

    @registry.receives(resources.ROUTER, [events.PRECOMMIT_CREATE],
                       priority_group.PRIORITY_ROUTER_DRIVER)
    @log_helpers.log_method_call
    def router_create_precommit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        router_dict = kwargs['router']
        flavor_id = router_dict['flavor_id']
        router_id = router_dict['id']
        router_dict['gw_port_id'] = kwargs['router_db'].gw_port_id
        if not self._validate_l3_flavor(context, router_id, flavor_id):
            return
        self.driver.create_router(context, {'router': router_dict})

    @registry.receives(resources.ROUTER, [events.PRECOMMIT_UPDATE],
                       priority_group.PRIORITY_ROUTER_DRIVER)
    @log_helpers.log_method_call
    def router_update_precommit(self, resource, event, trigger, payload=None):
        context = payload.context
        router_id = payload.resource_id
        router_dict = payload.request_body
        gw_port_id = payload.latest_state['gw_port_id']
        if not self._validate_l3_flavor(context, router_id):
            return
        if 'gw_port_id' not in router_dict:
            router_dict['gw_port_id'] = gw_port_id
        self.driver.update_router(context, router_id, {'router': router_dict})

    @registry.receives(resources.ROUTER, [events.PRECOMMIT_DELETE])
    @log_helpers.log_method_call
    def router_delete_precommit(self, resource, event, trigger, **kwargs):
        router_id = kwargs['router_id']
        context = kwargs['context']
        if not self._validate_l3_flavor(context, router_id):
            return
        self.driver.delete_router(context, router_id)

    @registry.receives(resources.ROUTER_INTERFACE, [events.AFTER_CREATE])
    @log_helpers.log_method_call
    def router_interface_aftercreate(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        router_id = kwargs['router_id']
        interface_info = {'port_id': kwargs['port_id']}
        if not self._validate_l3_flavor(context, router_id):
            return
        self.driver.add_router_interface(context, router_id, interface_info)

    @registry.receives(resources.ROUTER_INTERFACE, [events.AFTER_DELETE])
    @log_helpers.log_method_call
    def router_interface_afterdelete(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        router_id = kwargs['router_id']
        interface_info = kwargs['interface_info']
        if not self._validate_l3_flavor(context, router_id):
            return
        self.driver.remove_router_interface(context, router_id, interface_info)

    @registry.receives(resources.FLOATING_IP, [events.PRECOMMIT_CREATE])
    @log_helpers.log_method_call
    def floating_ip_create_precommit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        fip_dict = kwargs['floatingip']
        fip_dict['id'] = kwargs['floatingip_id']
        self._update_floatingip_status(context, fip_dict)
        if fip_dict['floating_ip_address'] is None:
            fip_dict['floating_ip_address'] = \
                kwargs['floatingip_db'].floating_ip_address
        self.driver.create_floatingip(context, {'floatingip': fip_dict})

    @registry.receives(resources.FLOATING_IP, [events.PRECOMMIT_UPDATE])
    @log_helpers.log_method_call
    def floating_ip_update_precommit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        fip_dict = kwargs['floatingip']['floatingip']
        fip_dict['id'] = kwargs['floating_ip_id']
        router_id = kwargs['floatingip_db'].router_id
        if not self._validate_l3_flavor(context, router_id):
            return
        self._update_floatingip_status(context, fip_dict)
        self.driver.update_floatingip(context, fip_dict['id'], {
                                      'floatingip': fip_dict})

    @registry.receives(resources.FLOATING_IP, [events.PRECOMMIT_DELETE])
    @log_helpers.log_method_call
    def floating_ip_delete_precommit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        fip_id = kwargs['port']['device_id']
        self.driver.delete_floatingip(context, fip_id)
