# Copyright 2017 Juniper Networks. All rights reserved.
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

from neutron_plugin_contrail.common import utils
from neutron_plugin_contrail.plugins.opencontrail.networking_bgpvpn.contrail\
    import ContrailBGPVPNDriver as Driver


class ContrailBGPVPNDriver(Driver):
    def __init__(self, service_plugin):
        utils.register_vnc_api_options()
        super(ContrailBGPVPNDriver, self).__init__(service_plugin)
