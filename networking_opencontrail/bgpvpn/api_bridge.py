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

from networking_bgpvpn.neutron.services.common import utils as bgpvpn_utils
from networking_opencontrail.drivers.rest_driver import ContrailRestApiDriver
import requests


class ContrailBgpvpnApiBridge(object):
    def __init__(self):
        self.client = ContrailRestApiDriver()

    def _clear_none_fields(self, kv_dict):
        new_dict = {k: v for (k, v) in kv_dict if v is not None}
        return new_dict

    @staticmethod
    def _project_id_vnc_to_neutron(proj_id):
        return proj_id.replace("-", "")

    @staticmethod
    def _get_route_target_list(rt_list):
        if rt_list is not None:
            return [rt[7:] for rt in rt_list.get_route_target()]
        return []

    @staticmethod
    def _get_refs(refs):
        if refs is not None:
            return [ref['uuid'] for ref in refs]
        return []

    @staticmethod
    def convert_target_to_contrail(target):
        if target is None:
            return None

        return ['target:' + rt for rt in target]

    def get_tenant_name(self, tenant_id):
        return 'tenant_name'  # TODO()

    def convert_bgpvpn_to_contrail(self, bgpvpn):
        data = {
            'fq_name': [
                'default-domain',
                self.get_tenant_name(bgpvpn['tenant_id']),
                bgpvpn.get('name')
            ],
            'parent_type': 'project',

            # Optional fields
            'bgpvpn_type': bgpvpn.get('type'),
            'display_name': bgpvpn.get('name'),

            'route_target_list': self.convert_target_to_contrail(
                bgpvpn.get('route_targets')),
            'import_route_target_list': self.convert_target_to_contrail(
                bgpvpn.get('import_targets')),
            'export_route_target_list': self.convert_target_to_contrail(
                bgpvpn.get('export_targets')),
        }

        data = self._clear_none_fields(data)
        return data

    def convert_contrail_to_bgpvpn(self, contrail, fields=None):
        id = contrail['uuid']
        tenant = self._project_id_vnc_to_neutron(contrail['parent_uuid'])

        bgpvpn_dict = {
            'id': id,
            'tenant_id': self._project_id_vnc_to_neutron(tenant),
            'name': contrail.get('display_name'),
            'type': contrail.get('bgpvpn_type'),
            'route_targets': self.convert_target_to_contrail(
                contrail.get('route_target_list')),
            'import_targets': self.convert_target_to_contrail(
                contrail.get('import_route_target_list')),
            'export_targets': self.convert_target_to_contrail(
                contrail.get('export_route_target_list')),
            'route_distinguishers': [],

            'networks': self._get_refs(
                contrail.get('virtual_network_back_refs')),
            'routers': self._get_refs(
                contrail.get('logical_router_back_refs')),
        }

        return bgpvpn_utils.make_bgpvpn_dict(bgpvpn_dict, fields=fields)

    @staticmethod
    def raise_if_error(status_code, response):
        if status_code != requests.codes.ok:
            message = response.get('message', '')
            raise Exception(message)

    def create_bgpvpn(self, bgpvpn):
        data = self.convert_bgpvpn_to_contrail(bgpvpn)

        (status, response) = self.client.create_resource('bgpvpn', data)
        self.raise_if_error(status, response)

        return response.get('uuid')

    def get_bgpvpn(self, id, fields=None, exclude_back_refs=None,
                   exclude_children=None, exclude_hrefs=None):
        query = {
            'fields': fields,
            'exclude_back_refs': exclude_back_refs,
            'exclude_children': exclude_children,
            'exclude_hrefs': exclude_hrefs,
        }

        query = self._clear_none_fields(query)
        (status, response) = self.client.get_resource('bgpvpn', query, id)
        self.raise_if_error(status, response)

        bgpvpn = self.convert_contrail_to_bgpvpn(response)
        return bgpvpn

    def update_bgpvpn(self, id, bgpvpn):
        data = self.convert_bgpvpn_to_contrail(bgpvpn)

        del data['fq_name']
        del data['parent_type']

        if bgpvpn.get('bgpvpn_type') is not None:
            del data['bgpvpn_type']

        (status, response) = self.client.update_resource('bgpvpn', id, data)
        self.raise_if_error(status, response)

        return response.get('uuid')

    def delete_bgpvpn(self, id):
        (status, response) = self.client.delete_resource('bgpvpn', id)
        self.raise_if_error(status, response)
        return response.get('uuid')

    def get_bgpvpns(self, detail=None, fields=None, filters=None, count=None,
                    exclude_hrefs=None, shared=None, parent_type=None,
                    parent_fq_name_str=None, parent_id=None,
                    back_ref_id=None, obj_uuids=None):
        query = {
            'detail': detail,
            'fields': fields,
            'filters': filters,
            'count': count,
            'exclude_hrefs': exclude_hrefs,
            'shared': shared,
            'parent_type': parent_type,
            'parent_fq_name_str': parent_fq_name_str,
            'parent_id': parent_id,
            'back_ref_id': back_ref_id,
            'obj_uuids': obj_uuids,
        }

        query = self._clear_none_fields(query)

        (status, response) = self.client.list_resource('bgpvpn', query)
        self.raise_if_error(status, response)

        return [i.get('uuid') for i in response]
