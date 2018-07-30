# Copyright (c) 2016 OpenStack Foundation
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

import requests

from oslo_config import cfg

from networking_opencontrail.common import constants

vnc_opts = [
    cfg.StrOpt('api_server_ip',
               default=constants.VNC_API_DEFAULT_HOST,
               help='IP address to connect to VNC API'),
    cfg.IntOpt('api_server_port',
               default=constants.VNC_API_DEFAULT_PORT,
               help='Port to connect to VNC API'),
    cfg.StrOpt('api_server_base_url',
               default=constants.VNC_API_DEFAULT_BASE_URL,
               help='URL path to request VNC API'),
    cfg.BoolOpt('use_ssl',
                default=constants.VNC_API_DEFAULT_USE_SSL,
                help='Use SSL to connect with VNC API'),
    cfg.BoolOpt('insecure',
                default=constants.VNC_API_DEFAULT_INSECURE,
                help='Insecurely connect to VNC API'),
    cfg.StrOpt('certfile',
               help='Certificate file path to connect securely to VNC API'),
    cfg.StrOpt('keyfile',
               help='Key file path to connect securely to  VNC API'),
    cfg.StrOpt('cafile',
               help='CA file path to connect securely to VNC API'),
]


def register_vnc_api_options():
    """Register Contrail Neutron core plugin configuration flags"""
    cfg.CONF.register_opts(vnc_opts, 'APISERVER')


def vnc_api_is_authenticated():
    """Determines if the VNC API needs credentials.

    :returns: True if credentials are needed, False otherwise
    """
    url = "%s://%s:%s/aaa-mode" % (
        'https' if cfg.CONF.APISERVER.use_ssl else 'http',
        cfg.CONF.APISERVER.api_server_ip,
        cfg.CONF.APISERVER.api_server_port
    )
    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        return False
    elif response.status_code == requests.codes.unauthorized:
        return True
    else:
        response.raise_for_status()
