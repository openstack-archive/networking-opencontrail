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

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.services.common import utils as bgpvpn_utils
from networking_opencontrail.bgpvpn.api_bridge import ContrailBgpvpnApiBridge
from networking_opencontrail.drivers.drv_opencontrail import\
    OpenContrailDrivers

CONTRAIL_BGPVPN_DRIVER_NAME = 'OpenContrailBGPVPN'


class ContrailBGPVPNDriver(object):
    def __init__(self, service_plugin):
        super(ContrailBGPVPNDriver, self).__init__(service_plugin)
        self.client = ContrailBgpvpnApiBridge()
        self.neutron_client = OpenContrailDrivers()

    def _add_ref(self, object, bgpvpn_id):
        refs = object.get(['bgpvpn_refs']) or []
        refs.append({
            'uuid': bgpvpn_id,
            'href': "/bgpvpn/%s" % bgpvpn_id,
            'to': [
                'default-domain',
                self.client.get_tenant_name(object['tenant_id']),
                object['name']
            ],
        })
        object['bgpvpn_refs'] = refs

    def _delete_ref(self, object, bgpvpn_id):
        object['bgpvpn_refs'] = [ref for ref in object['bgpvpn_refs']
                                 if ref['uuid'] != bgpvpn_id]
        return object

    def create_bgpvpn(self, context, bgpvpn):
        # Does not support to set route distinguisher
        if 'route_distinguishers' in bgpvpn and bgpvpn['route_distinguishers']:
            raise bgpvpn_ext.BGPVPNRDNotSupported(
                driver=CONTRAIL_BGPVPN_DRIVER_NAME)

        bgpvpn['id'] = self.client.create_bgpvpn(bgpvpn)
        return bgpvpn

    def get_bgpvpns(self, context, filters=None, fields=None):
        bgpvpns = []

        for bgpvpn in self.client.get_bgpvpns(
                fields=fields,
                filters=filters,
                detail=True):
            if bgpvpn_utils.filter_resource(bgpvpn, filters):
                bgpvpns.append(bgpvpn)

        return bgpvpns

    def get_bgpvpn(self, context, id, fields=None):
        try:
            bgpvpn = self.client.get_bgpvpn(id, fields=fields)
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=id)
        return bgpvpn

    def update_bgpvpn(self, context, id, bgpvpn):
        if 'route_distinguishers' in bgpvpn:
            raise bgpvpn_ext.BGPVPNRDNotSupported(
                driver=CONTRAIL_BGPVPN_DRIVER_NAME)

        try:
            self.client.get_bgpvpn(id)
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=id)

        self.client.update_bgpvpn(id, bgpvpn)

        return bgpvpn

    def delete_bgpvpn(self, context, id):
        try:
            bgpvpn = self.client.get_bgpvpn(id, fields=[
                'virtual_network_back_refs', 'logical_router_back_refs'])
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=id)

        for ref in bgpvpn['virtual_network_back_refs']:
            self.delete_net_assoc(context, {'network_id': ref['uuid']}, id)

        self.client.delete_bgpvpn(id)

    def create_net_assoc(self, context, bgpvpn_id, network_association):
        try:
            bgpvpn = self.client.get_bgpvpn(id)
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        net_id = network_association['network_id']

        network = self.neutron_client.get_network(context, net_id)
        self._add_ref(network, bgpvpn['id'])
        self.neutron_client.update_network(context, net_id, network)

        # Use the network ID as association id
        network_association['id'] = net_id
        network_association['bgpvpn_id'] = bgpvpn_id
        network_association.pop('project_id', None)
        return bgpvpn_utils.make_net_assoc_dict(**network_association)

    def get_net_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        try:
            bgpvpn = self.client.get_bgpvpn(bgpvpn_id,
                                            fields=[
                                                'virtual_network_back_refs',
                                            ])
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        if assoc_id not in bgpvpn.get('networks', []):
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)
        return bgpvpn_utils.make_net_assoc_dict(
            assoc_id,
            bgpvpn['tenant_id'],
            bgpvpn_id,
            assoc_id)

    def get_net_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        try:
            bgpvpn = self.client.get_bgpvpn(bgpvpn_id, fields=[
                'virtual_network_back_refs'
            ])
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        bgpvpn_net_assocs = []
        for vn_ref in bgpvpn.get('networks', []):
            bgpvpn_net_assoc = bgpvpn_utils.make_net_assoc_dict(
                vn_ref,
                bgpvpn['tenant_id'],
                bgpvpn_id,
                vn_ref,
                fields,
            )
            if bgpvpn_utils.filter_resource(bgpvpn_net_assoc, filters):
                bgpvpn_net_assocs.append(bgpvpn_net_assoc)
        return bgpvpn_net_assocs

    def delete_net_assoc(self, context, assoc_id, bgpvpn_id):
        try:
            bgpvpn = self.client.get_bgpvpn(bgpvpn_id)
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        vn_obj = self.neutron_client.get_network(context, assoc_id)
        vn_obj = self._delete_ref(vn_obj, bgpvpn_id)
        self.neutron_client.update_network(context, assoc_id, vn_obj)

        return bgpvpn_utils.make_net_assoc_dict(
            assoc_id,
            bgpvpn['tenant_id'],
            bgpvpn_id,
            assoc_id,
        )

    def create_router_assoc(self, context, bgpvpn_id, router_association):
        try:
            bgpvpn = self.client.get_bgpvpn(bgpvpn_id)
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        router_id = router_association['router_id']
        router = self.neutron_client.get_router(context, router_id)
        self._add_ref(router, bgpvpn['id'])
        self.neutron_client.update_router(context, router_id, router)

        # Use the router ID as association id
        router_association['id'] = router_id
        router_association['bgpvpn_id'] = bgpvpn_id
        router_association.pop('project_id', None)
        return bgpvpn_utils.make_router_assoc_dict(**router_association)

    def get_router_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        try:
            bgpvpn = self.client.get_bgpvpn(bgpvpn_id, fields=[
                'logical_router_back_refs'
            ])
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        if assoc_id not in bgpvpn.get('routers', []):
            raise bgpvpn_ext.BGPVPNRouterAssocNotFound(id=assoc_id,
                                                       bgpvpn_id=bgpvpn_id)

        return bgpvpn_utils.make_router_assoc_dict(
            assoc_id,
            bgpvpn['tenant_id'],
            bgpvpn_id,
            assoc_id)

    def get_router_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        try:
            bgpvpn = self.client.get_bgpvpn(bgpvpn_id, fields=[
                'logical_router_back_refs'
            ])
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        bgpvpn_router_assocs = []
        for lr_ref in bgpvpn.get('routers', []):
            bgpvpn_router_assoc = bgpvpn_utils.make_router_assoc_dict(
                lr_ref['uuid'],
                bgpvpn['tenant_id'],
                bgpvpn_id,
                lr_ref['uuid'],
                fields,
            )

            if bgpvpn_utils.filter_resource(bgpvpn_router_assoc, filters):
                bgpvpn_router_assocs.append(bgpvpn_router_assoc)

        return bgpvpn_router_assocs

    def delete_router_assoc(self, context, assoc_id, bgpvpn_id):
        try:
            bgpvpn = self.client.get_bgpvpn(bgpvpn_id)
        except Exception:
            raise bgpvpn_ext.BGPVPNNotFound(id=bgpvpn_id)

        lr_obj = self.neutron_client.get_router(context, assoc_id)
        lr_obj = self._delete_ref(lr_obj, bgpvpn_id)
        self.neutron_client.update_router(context, assoc_id, lr_obj)

        return bgpvpn_utils.make_router_assoc_dict(
            assoc_id,
            bgpvpn['tenant_id'],
            bgpvpn_id,
            assoc_id,
        )
