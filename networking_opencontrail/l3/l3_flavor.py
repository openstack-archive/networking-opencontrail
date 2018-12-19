from neutron.objects import router as l3_obj
from neutron.services.l3_router.service_providers import base
from neutron_lib import constants as q_const
from neutron_lib.callbacks import events
from neutron_lib.callbacks import priority_group
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
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
        if router_id is None:
            return False
        if not flavor_id:
            router = l3_obj.Router.get_object(context, id=router_id)
            flavor = self._flavor_plugin.get_flavor(context, router.flavor_id)
            flavor_id = flavor['id']

        provider = self._flavor_plugin.get_flavor_next_provider(
            context, flavor_id)[0]
        return str(provider['driver']) == self.provider

    def _update_floatingip_status(self, context, fip_dict):
        port_id = fip_dict.get('port_id')
        status = q_const.ACTIVE if port_id else q_const.DOWN
        l3_obj.FloatingIP.update_object(context, {'status': status},
                                        id=fip_dict['id'])

    @registry.receives(resources.ROUTER, [events.PRECOMMIT_CREATE])
    @log_helpers.log_method_call
    def router_create_post_commit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        flavor_id = kwargs['router']['flavor_id']
        router_dict = kwargs['router']
        router_dict['gw_port_id'] = kwargs['router_db'].gw_port_id
        router_id = kwargs['router_id']
        router_dict['id'] = router_id
        if not self._validate_l3_flavor(context, router_id, flavor_id):
            return
        self.driver.create_router(context, {'router': router_dict})

    @registry.receives(resources.ROUTER, [events.PRECOMMIT_UPDATE],
                       priority_group.PRIORITY_ROUTER_DRIVER)
    @log_helpers.log_method_call
    def router_update_post_commit(self, resource, event, trigger, **kwargs):
        # NOTE(manjeets) router update bypasses the driver controller
        # and argument type is different.
        payload = kwargs.get('payload', None)
        if payload:
            context = payload.context
            router_id = payload.states[0]['id']
            router_dict = payload.request_body
            gw_port_id = payload.states[0]['gw_port_id']
        else:
            # TODO(manjeets) Remove this shim once payload is fully adapted
            # https://bugs.launchpad.net/neutron/+bug/1747747
            context = kwargs['context']
            router_id = kwargs['router_db'].id
            router_dict = kwargs['router']
            gw_port_id = kwargs['router_db'].gw_port_id
        if not self._validate_l3_flavor(context, router_id):
            return
        if 'gw_port_id' not in router_dict:
                router_dict['gw_port_id'] = gw_port_id
        self.driver.update_router(context, router_id, {'router': router_dict})

    @registry.receives(resources.ROUTER, [events.PRECOMMIT_DELETE])
    @log_helpers.log_method_call
    def router_delete_post_commit(self, resource, event, trigger, **kwargs):
        router_id = kwargs['router_db'].id
        context = kwargs['context']
        if not self._validate_l3_flavor(context, router_id):
            return
        self.driver.delete_router(context, router_id)

    @registry.receives(resources.ROUTER_INTERFACE, [events.AFTER_CREATE])
    @log_helpers.log_method_call
    def router_interface_after_create(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        router_id = kwargs['router_id']
        interface_info = {'port_id': kwargs['port_id']}
        if not self._validate_l3_flavor(context, router_id):
            return
        self.driver.add_router_interface(context, router_id, interface_info)

    @registry.receives(resources.ROUTER_INTERFACE, [events.AFTER_DELETE])
    @log_helpers.log_method_call
    def router_interface_after_delete(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        router_id = kwargs['router_id']
        interface_info = kwargs['interface_info']
        if not self._validate_l3_flavor(context, router_id):
            return
        self.driver.remove_router_interface(context, router_id, interface_info)

    @registry.receives(resources.FLOATING_IP, [events.PRECOMMIT_CREATE])
    @log_helpers.log_method_call
    def floatingip_create_post_commit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        fip_dict = copy.deepcopy(kwargs['floatingip'])
        router_id = kwargs['floatingip_db'].router_id
        if not self._validate_l3_flavor(context, router_id):
            return
        fip_dict['id'] = kwargs['floatingip_id']
        self._update_floatingip_status(context, fip_dict)
        if fip_dict['floating_ip_address'] is None:
            fip_dict['floating_ip_address'] = \
                kwargs['floatingip_db'].floating_ip_address
        self.driver.create_floatingip(context, {'floatingip': fip_dict})

    @registry.receives(resources.FLOATING_IP, [events.PRECOMMIT_UPDATE])
    @log_helpers.log_method_call
    def floatingip_update_post_commit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        fip_dict = kwargs['floatingip']
        router_id = kwargs['floatingip_db'].router_id
        fip_dict['id'] = kwargs['floatingip_db'].id
        if not self._validate_l3_flavor(context, router_id):
            return
        self._update_floatingip_status(context, fip_dict)
        self.driver.update_floatingip(context, fip_dict['id'], {'floatingip': fip_dict})

    @registry.receives(resources.FLOATING_IP, [events.PRECOMMIT_DELETE])
    @log_helpers.log_method_call
    def floatingip_delete_post_commit(self, resource, event, trigger, **kwargs):
        context = kwargs['context']
        fip_data = l3_obj.FloatingIP.get_objects(
            context,
            floating_port_id=kwargs['port']['id'])[0]
        if not self._validate_l3_flavor(context, fip_data.router_id):
            return
        self.driver.delete_floatingip(context, fip_data.id)

    @registry.receives(resources.FLOATING_IP,
                       [events.BEFORE_CREATE, events.BEFORE_READ,
                        events.BEFORE_UPDATE, events.BEFORE_DELETE,
                        events.PRECOMMIT_CREATE, events.PRECOMMIT_UPDATE,
                        events.PRECOMMIT_DELETE,
                        events.PRECOMMIT_ADD_ASSOCIATION,
                        events.PRECOMMIT_DELETE_ASSOCIATIONS,
                        events.AFTER_CREATE, events.AFTER_READ,
                        events.AFTER_UPDATE, events.AFTER_DELETE, ])
    @registry.receives(resources.ROUTER_CONTROLLER,
                       [events.BEFORE_CREATE, events.BEFORE_READ,
                        events.BEFORE_UPDATE, events.BEFORE_DELETE,
                        events.PRECOMMIT_CREATE, events.PRECOMMIT_UPDATE,
                        events.PRECOMMIT_DELETE,
                        events.PRECOMMIT_ADD_ASSOCIATION,
                        events.PRECOMMIT_DELETE_ASSOCIATIONS,
                        events.AFTER_CREATE, events.AFTER_READ,
                        events.AFTER_UPDATE, events.AFTER_DELETE, ])
    @registry.receives(resources.ROUTER,
                       [events.BEFORE_CREATE, events.BEFORE_READ,
                        events.BEFORE_UPDATE, events.BEFORE_DELETE,
                        events.PRECOMMIT_CREATE, events.PRECOMMIT_UPDATE,
                        events.PRECOMMIT_DELETE,
                        events.PRECOMMIT_ADD_ASSOCIATION,
                        events.PRECOMMIT_DELETE_ASSOCIATIONS,
                        events.AFTER_CREATE, events.AFTER_READ,
                        events.AFTER_UPDATE, events.AFTER_DELETE, ])
    @registry.receives(resources.ROUTER_INTERFACE,
                       [events.BEFORE_CREATE, events.BEFORE_READ,
                        events.BEFORE_UPDATE, events.BEFORE_DELETE,
                        events.PRECOMMIT_CREATE, events.PRECOMMIT_UPDATE,
                        events.PRECOMMIT_DELETE,
                        events.PRECOMMIT_ADD_ASSOCIATION,
                        events.PRECOMMIT_DELETE_ASSOCIATIONS,
                        events.AFTER_CREATE, events.AFTER_READ,
                        events.AFTER_UPDATE, events.AFTER_DELETE, ])
    @registry.receives(resources.ROUTER_GATEWAY,
                       [events.BEFORE_CREATE, events.BEFORE_READ,
                        events.BEFORE_UPDATE, events.BEFORE_DELETE,
                        events.PRECOMMIT_CREATE, events.PRECOMMIT_UPDATE,
                        events.PRECOMMIT_DELETE,
                        events.PRECOMMIT_ADD_ASSOCIATION,
                        events.PRECOMMIT_DELETE_ASSOCIATIONS,
                        events.AFTER_CREATE, events.AFTER_READ,
                        events.AFTER_UPDATE, events.AFTER_DELETE, ])
    @log_helpers.log_method_call
    def catch_all(self, resource, event, trigger, **kwargs):
        # import pdb; pdb.set_trace()
        pass
