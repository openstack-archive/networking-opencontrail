# -*- coding: utf-8 -*-
# Copyright (c) 2018 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import requests

from networking_opencontrail.tests.base import IntegrationTestCase


class TestManageNetwork(IntegrationTestCase):
    def test_create_vlan_network(self):
        """Create vlan network using openstack CLI.

        Check if network exists in OpenContrail and all properties are
        the same as used in create command call.
        """
        try:
          ps = requests.get('{}/projects'.format(self.contrail_api)) 
          print(ps.text)
        except:
          pass
        network = self.neutron.create_network({
            'network': {
                'name': 'test_public_1',
                'provider:network_type': 'vlan',
                'provider:segmentation_id': 10,
                'provider:physical_network': 'public',
                'admin_state_up': True,
            },
        })
        print(network) 
        print(dir(network)) 
        url = '{}/virtual-network/{}'.format(self.contrail_api, network['id'])
        res = requests.get(url)
        self.assertTrue(res.status_code in [200, 301, 302, 303, 304])

        result = res.json().get('virtual-network')
        self.assertDictEqual(
            result['provider_properties'],
            {'segmentation_id': network['provider:segmentation_id'],
             'physical_network': network['provider:physical_network']})
