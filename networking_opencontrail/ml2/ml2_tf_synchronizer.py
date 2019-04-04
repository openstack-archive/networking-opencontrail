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

from neutron_lib.plugins import directory
from neutron_lib import context
from neutron_lib import worker
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ML2TFSynchronizer(worker.BaseWorker):
    def __init__(self, tf_driver, device_types_to_omit):
        super(ML2TFSynchronizer, self).__init__()
        self.driver = tf_driver
        self.device_types_to_omit = device_types_to_omit
        self._delete_methods = {
            'ports': self.driver.delete_port
        }
        self._create_methods = {
            'ports': self.driver.create_port
        }
        self._ignore_methods = {
            'ports': self._ignore_port
        }

    def start(self):
        super(ML2TFSynchronizer, self).start()
        LOG.info('ML2TFSynchronizer worker started')
        self._synchronize()

    def stop(self):
        pass

    def wait(self):
        pass

    def reset(self):
        pass

    def _synchronize(self):
        resources_to_create, resources_to_delete = self._calculate_diff()
        self._delete_resources(resources_to_delete)
        self._create_resources(resources_to_create)

    def _calculate_diff(self):
        tf_resources = self._get_tf_resources()
        neutron_resources = self._get_neutron_resources()
        resources_to_delete = {}
        resources_to_create = {}
        for res_type in tf_resources.keys():
            neutron_res_ids = set([res['id'] for res
                                   in neutron_resources[res_type]])
            tf_res_ids = set([res['id'] for res
                              in tf_resources[res_type]])

            res_ids_to_delete = tf_res_ids - neutron_res_ids
            res_ids_to_create = neutron_res_ids - tf_res_ids

            resources_to_delete.update({res_type: [
                res for res in tf_resources[res_type] if
                res['id'] in res_ids_to_delete
                and not self._ignore_methods[res_type](res)
            ]})
            resources_to_create.update({res_type: [
                res for res in neutron_resources[res_type] if
                res['id'] in res_ids_to_create
                and not self._ignore_methods[res_type](res)
            ]})

        LOG.info('Ports in Neutron: %s', len(neutron_resources['ports']))
        LOG.info('Ports in TF: %s', len(tf_resources['ports']))
        LOG.info('Ports to delete in TF: %s',
                 len(resources_to_delete['ports']))
        LOG.info('Ports to create in TF: %s',
                 len(resources_to_create['ports']))

        return resources_to_create, resources_to_delete

    def _get_tf_resources(self):
        return {
            'ports': self.driver.get_ports(self._context, filters={}),
        }

    def _get_neutron_resources(self):
        return {
            'ports': self._core_plugin.get_ports(self._context),
        }

    def _delete_resources(self, resources_to_delete):
        for res_type, res_list in resources_to_delete.items():
            delete_resource = self._delete_methods[res_type]
            for resource in list(res_list):
                try:
                    delete_resource(self._context, resource['id'])
                    res_list.remove(resource)
                except Exception:
                    LOG.exception('Delete Resource Failed')

    def _create_resources(self, resources_to_create):
        for res_type, res_list in resources_to_create.items():
            create_resource = self._create_methods[res_type]
            for resource in list(res_list):
                try:
                    create_resource(self._context, resource)
                    res_list.remove(resource)
                except Exception:
                    LOG.exception('Create Resource Failed')

    def _ignore_port(self, port):
        return (port['device_owner'] in self.device_types_to_omit or
                port['fq_name'][0] != 'default-domain' or
                '_snat_' in port['name'])

    @property
    def _core_plugin(self):
        return directory.get_plugin()

    @property
    def _context(self):
        return context.get_admin_context()
