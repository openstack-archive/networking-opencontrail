#!/usr/bin/env python
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

import os
import requests
import sys
import uuid

from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneclient.v3 import client


def synchronize_project(contrail_api, project_id):
    url = '{}/project/{}'
    response = requests.get(url.format(contrail_api, project_id))
    message = 'project {}: {}'.format(project_id, response.status_code)
    print(message)


if len(sys.argv) > 1:
    controller_ip = sys.argv[1]
else:
    controller_ip = os.getenv('CONTROLLER_IP', 'localhost')

contrail_api = 'http://{}:8082'.format(controller_ip)
auth_url = 'http://{}/identity/v3'.format(controller_ip)

auth = identity.V3Password(auth_url=auth_url,
                           username='admin', password='admin',
                           project_name='demo',
                           project_domain_id='default',
                           user_domain_id='default')
sess = session.Session(auth=auth)

# Requesting contrail for keystone projects enforces contrail
# to synchronize them
keystone = client.Client(session=sess)
project_ids = [str(uuid.UUID(proj.id)) for proj in keystone.projects.list()]
[synchronize_project(contrail_api, p_id) for p_id in project_ids]
