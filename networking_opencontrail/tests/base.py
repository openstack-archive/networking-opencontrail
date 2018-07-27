# -*- coding: utf-8 -*-

# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import os

from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron
from oslotest import base
from keystoneclient.v3 import client
import requests
import uuid


class TestCase(base.BaseTestCase):
    """Test case base class for all unit tests."""


class IntegrationTestCase(base.BaseTestCase):
    """Base test case for all integration tests."""

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        controller_ip = os.getenv('CONTROLLER_IP', 'localhost')

        self.contrail_api = 'http://{}:8082'.format(controller_ip)
        self.auth_url = 'http://{}/identity/v3'.format(controller_ip)

        auth = identity.V3Password(auth_url=self.auth_url,
                                   username='admin', password='admin',
                                   project_name='demo',
                                   project_domain_id='default',
                                   user_domain_id='default')
        sess = session.Session(auth=auth)
        self.neutron = neutron.Client(session=sess)

        keystone = client.Client(session=sess)
        projs = [str(uuid.UUID(proj.id)) for proj in keystone.projects.list()]
        print([requests.get('http://{}:8082/project/{}'.format(controller_ip, id)) for id in projs]) 
