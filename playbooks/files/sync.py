#!/usr/bin/env python

import sys
import os
import requests
import uuid
from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneclient.v3 import client

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
url = '{}/project/{}'

[requests.get(url.format(contrail_api, p_id)) for p_id in project_ids]
