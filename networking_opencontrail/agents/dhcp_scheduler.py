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

from oslo_log import log as logging
from requests import codes as http_status

from neutron.scheduler import dhcp_agent_scheduler

from networking_opencontrail.drivers.rest_driver import ContrailRestApiDriver


LOG = logging.getLogger(__name__)


class TFIgnoreDHCPScheduler(dhcp_agent_scheduler.ChanceScheduler):
    """Scheduler which prevent from assigning DHCP agent to TF-Network.

    If resource (network) is managed by Tungsten Fabric, do not schedule
    any DHCP agent from Neutron. In other way, use dafault scheduler.
    """

    def __init__(self):
        super(TFIgnoreDHCPScheduler, self).__init__()
        self.tf_rest_driver = ContrailRestApiDriver()

    def schedule(self, plugin, context, resource):
        network_id = resource.get('id', '')

        if self._check_network_exist_in_tf(network_id):
            LOG.debug("Network %s is managed by Tungsten Fabric:"
                      " not schedule any DHCP agent." % network_id)
            return []

        return super(TFIgnoreDHCPScheduler, self).schedule(
            plugin, context, resource)

    def _check_network_exist_in_tf(self, network_id):
        status_code, response = self.tf_rest_driver.get_resource(
            'virtual-network', None, network_id)

        if status_code == http_status.ok:
            return True
        if status_code == http_status.not_found:
            return False

        LOG.error("Try to check if network %s exist in Tungsten Fabric, but"
                  " response is %s, %s." % (network_id, status_code, response))
        raise TFResponseNotExpected


class TFResponseNotExpected(Exception):
    pass
