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
        self.ports_to_delete = set()
        self.ports_to_create = set()

    def start(self):
        super(ML2TFSynchronizer, self).start()
        LOG.info('ML2TFSynchronizer worker started')
        self.prepare_diff()
        # self.delete_resources_in_tf()
        # self.create_resources_in_tf()

    def stop(self):
        pass

    def wait(self):
        pass

    def reset(self):
        pass

    def prepare_diff(self):
        neutron_ports = self._core_plugin.get_ports(self._context)
        tf_ports = self.driver.get_ports(self._context, filters={})

        neutron_ports_ids = set([port['id'] for port in neutron_ports])
        tf_ports_ids = set([port['id'] for port in tf_ports])
        ports_ids_to_delete = tf_ports_ids - neutron_ports_ids
        ports_ids_to_create = neutron_ports_ids - tf_ports_ids
        self.ports_to_delete = [
            port for port in tf_ports if
            port['id'] in ports_ids_to_delete and
            port['device_owner'] not in self.device_types_to_omit
        ]
        self.ports_to_create = [
            port for port in neutron_ports if
            port['id'] in ports_ids_to_create and
            port['device_owner'] not in self.device_types_to_omit
        ]
        for port in self.ports_to_delete:
            LOG.debug(port)
        LOG.info('Ports in Neutron: %s', len(neutron_ports))
        LOG.info('Ports in TF: %s', len(tf_ports))
        LOG.info('Ports to delete in TF: %s', len(self.ports_to_delete))
        LOG.info('Ports to create in TF: %s', len(self.ports_to_create))

    def delete_resources_in_tf(self):
        for port in list(self.ports_to_delete):
            try:
                self.driver.delete_port(self._context, port['id'])
                self.ports_to_delete.remove(port)
            except Exception:
                LOG.exception('Delete Port Failed')

    def create_resources_in_tf(self):
        for port in list(self.ports_to_create):
            pass

    @property
    def _core_plugin(self):
        return directory.get_plugin()

    @property
    def _context(self):
        return context.get_admin_context().elevated()

    def _is_callback_to_omit(self, device_owner):
        # Operation on port should be not propagated to TungstenFabric when:
        # 1) device type have ports in Neutron, which are not necessary in TF
        # 2) port is created by plugin to be compatibility with TF

        if device_owner in OMIT_DEVICES_TYPES:
            LOG.debug("Port device is %s: omit callback to TungstenFabric" %
                      device_owner)
            return True
        return False
