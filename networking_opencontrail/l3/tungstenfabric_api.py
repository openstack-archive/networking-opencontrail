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

from oslo_config import cfg
import requests

import networking_opencontrail.drivers.drv_opencontrail as driver


class TungstenFabricApiConnector(object):
    def __init__(self):
        if cfg.CONF.APISERVER.use_ssl:
            self._apiserverconnect = driver._DEFAULT_SECURE_SERVER_CONNECT
        else:
            self._apiserverconnect = driver._DEFAULT_SERVER_CONNECT

    def _get_from_tf_api(self, url_path):
        url = "%s://%s:%s%s" % (self._apiserverconnect,
                                cfg.CONF.APISERVER.api_server_ip,
                                cfg.CONF.APISERVER.api_server_port,
                                url_path)

        response = requests.get(url)

        try:
            return response.json()
        except ValueError:
            raise Exception("ERROR on decode: %s" % response.content)

    def _get_tf_resource(self, resource_type, resource_id):
        url_path = "/%s/%s" % (resource_type, resource_id)
        try:
            return self._get_from_tf_api(url_path)[resource_type]
        except ValueError:
            return {}

    def get_snat_ips(self, context, router_id):
        # (kamman) It only shows flow to get snat ip from TF,
        # real solution should be included in vnc_openstack

        # TF creates snat async, so max. 3 retry to try get it
        snat_ips = set()
        for _ in range(3):
            instance_ips = set()
            router = self._get_tf_resource('logical-router', router_id)

            # When router not exist, there is no reason to wait for
            # complete service instance set up
            if not router:
                return []

            try:
                for service_ref in router['service_instance_refs']:
                    if not any("snat_" in name for name in service_ref['to']):
                        continue
                    service_id = service_ref['uuid']
                    service = self._get_tf_resource('service-instance',
                                                    service_id)
                    for vm_ref in service['virtual_machine_back_refs']:
                        vm = self._get_tf_resource('virtual-machine',
                                                   vm_ref['uuid'])
                        for vmi_r in vm['virtual_machine_interface_back_refs']:
                            vmi = self._get_tf_resource(
                                'virtual-machine-interface', vmi_r['uuid'])
                            if vmi.get('virtual_machine_interface_properties',
                                       {}).get('service_interface_type',
                                               '') == 'right':
                                for ip_ref in vmi['instance_ip_back_refs']:
                                    instance_ips.add(ip_ref['uuid'])
            except KeyError:
                # Snat interface is not yet ready
                import time
                time.sleep(1)
                continue

            for iip_id in instance_ips:
                iip = self._get_tf_resource('instance-ip', iip_id)
                snat_ips.add(iip['instance_ip_address'])

        return list(snat_ips)
