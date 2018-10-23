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

from networking_opencontrail.drivers.rest_driver import ContrailRestApiDriver


class TungstenFabricApiConnector(object):
    def __init__(self):
        self._rest_driver = ContrailRestApiDriver()

    def get_snat_ips(self, router_id):
        # (kamman) It only shows flow to get snat ip from TF,
        # real solution should be included in vnc_openstack

        # TF creates snat async, so max. 3 retry to try get it
        snat_ips = set()
        for _ in range(3):

            router = self._get_tf_router(router_id)
            # When router doesn't exist, there is no reason to wait for
            # complete service instance set up
            if not router:
                return []

            try:
                instance_ip_uuids = set(self._get_snat_ip_refs(router))
            except KeyError:
                # Snat interface is not yet ready
                import time
                time.sleep(1)
                continue

            snat_ips = set(
                self._get_tf_instance_ip(iip_id)['instance_ip_address']
                for iip_id in instance_ip_uuids)

        return list(snat_ips)

    def _get_snat_ip_refs(self, router):
        for service_ref in router['service_instance_refs']:
            if self._not_a_snat_service(service_ref):
                continue
            service = self._get_tf_service_instance(service_ref['uuid'])
            ip_refs = self._get_right_ip_refs_from_service(service)
            return [ip_ref['uuid'] for ip_ref in ip_refs]

    def _get_right_ip_refs_from_service(self, service):
        # Since ServiceInstance.right_ip_address is deprecated,
        # we need to get the value manually by traversing TF's data
        # structures.
        ip_refs = []
        for vm in self._get_vms_from_service_instances_back_refs(service):
            for vmi in self._get_vmis_from_virtual_machines_back_refs(vm):
                if self._service_interface_is_of_right_type:
                    ip_refs.extend(vmi['instance_ip_back_refs'])
        return ip_refs

    def _get_vms_from_service_instances_back_refs(self, service_instance):
        return self._get_resources_by_objects_refs(
            'virtual-machine', service_instance,
            'virtual_machine_back_refs')

    def _get_vmis_from_virtual_machines_back_refs(self, virtual_machine):
        return self._get_resources_by_objects_refs(
            'virtual-machine-interface', virtual_machine,
            'virtual_machine_interface_back_refs')

    def _get_resources_by_objects_refs(self, resource_type, obj, ref_type):
        resources = []
        for ref in obj[ref_type]:
            status_code, resource = self._rest_driver.get_resource(
                resource_type, None, ref)
            if status_code == 200:
                resources.append(resource[resource_type])
        return resources

    def _get_tf_service_instance(self, service_id):
        status_code, service = self._rest_driver.get_resource(
            'service-instance', None, service_id)
        if status_code == 200:
            return service['service-instance']
        return None

    def _get_tf_instance_ip(self, iip_id):
        status_code, instance_ip = self._rest_driver.get_resource(
            'instance-ip', None, iip_id)
        if status_code == 200:
            return instance_ip['instance-ip']
        return None

    def _get_tf_router(self, router_id):
        status_code, router = self._rest_driver.get_resource('logical-router',
                                                             None, router_id)
        if status_code == 200:
            return router['logical-router']
        return None

    @staticmethod
    def _not_a_snat_service(service_ref):
        return not any("snat_" in name for name in service_ref['to'])

    @staticmethod
    def _service_interface_is_of_right_type(vmi):
        return vmi.get('virtual_machine_interface_properties', {}
                       ).get('service_interface_type', '') == 'right'
