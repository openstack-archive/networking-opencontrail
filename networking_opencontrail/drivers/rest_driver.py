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

import json
from networking_opencontrail.drivers.drv_opencontrail import\
    OpenContrailDrivers
from oslo_config import cfg
import requests


class ContrailRestApiDriver(OpenContrailDrivers):
    def __init__(self):
        super(ContrailRestApiDriver, self).__init__()

    def update_auth_token(self):
        headers = {'Content-type': 'application/json'}

        if self._ksinsecure:
            response = (
                requests.post(self._keystone_url,
                              data=self._authn_body,
                              headers=headers,
                              verify=False))
        elif not self._ksinsecure and self._use_ks_certs:
            response = (
                requests.post(self._keystone_url,
                              data=self._authn_body,
                              headers=headers,
                              verify=self._kscertbundle))
        else:
            response = (
                requests.post(self._keystone_url,
                              data=self._authn_body,
                              headers=headers))

        if response.status_code == requests.codes.ok:
            authn_content = json.loads(response.text)
            self._authn_token = authn_content['access']['token']['id']
        else:
            raise RuntimeError('Authentication Failure')

    def set_auth_token(self, headers=None, update_token=False):
        if headers is None:
            headers = {}

        if update_token:
            self.update_auth_token()

        if self._authn_token:
            headers['X-AUTH-TOKEN'] = self._authn_token

        return headers

    def get_contrail_url(self, resource):
        url = "%s://%s:%s/%s" % (self._apiserverconnect,
                                 cfg.CONF.APISERVER.api_server_ip,
                                 cfg.CONF.APISERVER.api_server_port,
                                 resource)
        return url

    def request_contrail(self, resource, type='GET', data=None, headers=None,
                         params=None, update_tokens=False):
        # Request parameters
        url = self.get_contrail_url(resource)
        headers = self.set_auth_token(headers, update_tokens)
        headers['Content-type'] = 'application/json'
        request = {
            'headers': headers,
            'data': data,
            'params': params,
        }

        # Set auth type
        if self._apiinsecure:
            request['verify'] = False
        elif not self._apiinsecure and self._use_api_certs:
            request['verify'] = self._apicertbundle

        # Perform request
        if type == 'GET':
            response = requests.get(url, **request)
        elif type == 'POST':
            response = requests.post(url, **request)
        elif type == 'PUT':
            response = requests.put(url, **request)
        elif type == 'DELETE':
            response = requests.delete(url, **request)
        else:
            raise RuntimeError('Unknown request type')

        # Parse response
        if (response.status_code == requests.codes.unauthorized and
                not update_tokens):
            return self.request_contrail(resource, type=type, data=data,
                                         headers=headers, params=params,
                                         update_tokens=True)

        try:
            content = json.loads(response.text)
            return response.status_code, content
        except ValueError:
            return response.status_code, {'message': response.content}

    def create_resource(self, res_type, res_data):
        res_type += 's'
        return self.request_contrail(res_type, type='POST', data=res_data)

    def get_resource(self, res_type, query, id):
        resource = "%s/%s" % (res_type, id)
        return self.request_contrail(resource, type='GET', params=query)

    def update_resource(self, res_type, id, res_data):
        resource = "%s/%s" % (res_type, id)
        return self.request_contrail(resource, type='PUT', data=res_data)

    def delete_resource(self, res_type, id):
        resource = "%s/%s" % (res_type, id)
        return self.request_contrail(resource, type='DELETE')

    def list_resource(self, res_type, query):
        res_type += 's'
        return self.request_contrail(res_type, type='GET', params=query)
