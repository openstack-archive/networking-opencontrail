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
from neutron.scheduler.dhcp_agent_scheduler import base_scheduler

from networking_opencontrail.drivers.rest_driver import ContrailRestApiDriver


LOG = logging.getLogger(__name__)


class TFIgnoreDHCPScheduler(base_scheduler.BaseWeightScheduler,
                            dhcp_agent_scheduler.AutoScheduler):
    """Scheduler which prevent from assigning DHCP agent to TF-Network.

    If resource (network) is managed by Tungsten Fabric, do not schedule
    any DHCP agent from Neutron. In other way, use default scheduler.
    """

    def __init__(self):
        super(TFIgnoreDHCPScheduler, self).__init__(TFDHCPFilter())


class TFDHCPFilter(dhcp_agent_scheduler.DhcpFilter):
    """Resource filter for DHCP agent and TF-Network.

    This filter prevent from return any DHCP agent to TF-Network
    (filter_agents) and doesn't allow to bind any of them to TF-Network (bind).
    """
    def __init__(self):
        self.tf_rest_driver = ContrailRestApiDriver()
        super(TFDHCPFilter, self).__init__()

    def bind(self, context, agents, network_id):
        if self._check_network_exists_in_tf(network_id):
            LOG.info("Network %s is managed by Tungsten Fabric:"
                     " do not bind any DHCP agent." % network_id)
            return

        super(TFDHCPFilter, self).bind(context, agents, network_id)

    def filter_agents(self, plugin, context, network):
        network_id = network['id']

        agents_dict = super(TFDHCPFilter, self).filter_agents(
            plugin, context, network)

        if self._check_network_exists_in_tf(network_id):
            LOG.info("Network %s is managed by Tungsten Fabric:"
                     " do not return any DHCP agent." % network_id)
            return {'n_agents': 0, 'hostable_agents': [],
                    'hosted_agents': agents_dict['hosted_agents']}

        return agents_dict

    def _check_network_exists_in_tf(self, network_id):
        status_code, response = self.tf_rest_driver.get_resource(
            'virtual-network', None, network_id)

        if status_code == http_status.ok:
            return True
        if status_code == http_status.not_found:
            return False

        LOG.error("Tried to check if network %s exists in Tungsten Fabric, but"
                  " response is %s, %s." % (network_id, status_code, response))
        raise TFResponseNotExpectedError


class TFResponseNotExpectedError(Exception):
    pass
