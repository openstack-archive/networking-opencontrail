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
import requests
import uuid

from random import randint
from time import time as now

from keystoneauth1 import identity
from keystoneauth1 import session
from keystoneclient.v3 import client as keystone
from neutronclient.v2_0 import client as neutron
from oslotest import base


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
        self.keystone = keystone.Client(session=sess)

        # Create keystone project and make TF synchronize it
        self.project = self._create_keystone_project_for_test()
        self.tf_get_resource('project', self.project.id)

        self.neutronCleanupQueue = []

    def tearDown(self):
        super(IntegrationTestCase, self).tearDown()
        for resource, f_delete in reversed(self.neutronCleanupQueue):
            f_delete(resource['id'])
        self.project.delete()
        self._cleanup_tf_project()

    def tf_request_resource(self, resource_name, id):
        return requests.get(
            '{}/{}/{}'.format(
                self.contrail_api, resource_name, uuid.UUID(id)))

    def tf_get_resource(self, resource_name, id):
        response = self.tf_request_resource(resource_name=resource_name, id=id)
        self.assertIn(response.status_code, {200, 301, 302, 303, 304})
        ret = response.json()
        self.assertIsNotNone(ret.get(resource_name))
        return ret.get(resource_name)

    def tf_delete_resource(self, resource, id):
        return requests.delete(
            '{}/{}/{}'.format(
                self.contrail_api, resource, uuid.UUID(id)))

    def _cleanup_tf_project(self):
        # Need to clean up default-openstack Security Group before we can
        # delete the project from TF completely
        # TODO(artur.debski) check to do this properly

        tf_project = self.tf_get_resource('project', self.project.id)
        # TODO(maciej.jagiello) debug sg not removed when deleting project
        for sg in tf_project.get('security_groups', []):
            if 'default-openstack' in sg['to']:
                requests.delete(sg['href'])
                break
        self.tf_delete_resource('project', self.project.id)

    def _create_keystone_project_for_test(self):
        proj_name = self.__class__.__name__ + '-' + \
            str(int(now())) + '-' + \
            '{0:9}'.format(randint(100000000, 999999999))
        project = self.keystone.projects.create(
            name=proj_name, domain='default', description='', enabled=True)
        return project

    def _add_neutron_resource_to_cleanup(self, resource, f_cleanup):
        self.neutronCleanupQueue.append((resource, f_cleanup))

    def _remove_neutron_resource_from_cleanup(self, resource_tuple):
        self.neutronCleanupQueue.remove(resource_tuple)

    def q_create_resource(self, body):
        res_name = list(body)[0]
        f_create = getattr(self.neutron, 'create_' + res_name)
        f_delete = getattr(self.neutron, 'delete_' + res_name)

        resource = f_create(body)
        self._add_neutron_resource_to_cleanup(resource[res_name], f_delete)
        return resource

    def q_update_resource(self, resource, body):
        res_name = list(body)[0]
        f_update = getattr(self.neutron, 'update_' + res_name)
        updated_resource = f_update(resource['id'], body)
        return updated_resource

    def q_delete_resource(self, resource):
        match = [res for res in self.neutronCleanupQueue if resource in res]
        if match:
            match[0][1](match[0][0]['id'])
            self._remove_neutron_resource_from_cleanup(match[0])

    def q_create_network(self, name, **kwargs):
        network = {}
        network.update(kwargs)
        network['name'] = name
        network['project_id'] = self.project.id
        network_body = {}
        network_body['network'] = network
        return self.q_create_resource(network_body)

    def q_create_subnet(self, name, network_id, ip_version, cidr, **kwargs):
        subnet = {}
        subnet.update(kwargs)
        subnet['name'] = name
        subnet['network_id'] = network_id
        subnet['ip_version'] = ip_version
        subnet['cidr'] = cidr
        subnet_body = {}
        subnet_body['subnet'] = subnet
        return self.q_create_resource(subnet_body)

    def q_update_subnet(self, subnet, **kwargs):
        subnet_body = {'subnet': {}}
        subnet_body['subnet'].update(kwargs)
        return self.q_update_resource(subnet['subnet'], subnet_body)

    def q_delete_subnet(self, subnet):
        self.q_delete_resource(subnet['subnet'])

    def q_create_floating_ip(self, floating_network_id, **kwargs):
        floating_ip = {}
        floating_ip.update(kwargs)
        floating_ip['tenant_id'] = self.project.id
        floating_ip['project_id'] = self.project.id
        floating_ip['floating_network_id'] = floating_network_id
        floating_ip_body = {}
        floating_ip_body['floatingip'] = floating_ip
        return self.q_create_resource(floating_ip_body)

    def q_delete_floating_ip(self, floating_ip):
        self.q_delete_resource(floating_ip['floatingip'])

    def q_create_port(self, name, network_id, **kwargs):
        port = {}
        port.update(kwargs)
        port['name'] = name
        port['network_id'] = network_id
        port_body = {}
        port_body['port'] = port
        return self.q_create_resource(port_body)

    def q_delete_port(self, port):
        self.q_delete_resource(port['port'])

    def q_update_port(self, port, **kwargs):
        port_body = {'port': {}}
        port_body['port'].update(kwargs)
        return self.q_update_resource(port['port'], port_body)

    def q_create_security_group(self, name, **kwargs):
        security_group = {}
        security_group.update(kwargs)
        security_group['name'] = name
        security_group['project_id'] = self.project.id
        security_group_body = {}
        security_group_body['security_group'] = security_group
        return self.q_create_resource(security_group_body)

    def q_delete_security_group(self, security_group):
        self.q_delete_resource(security_group['security_group'])

    def q_update_security_group(self, security_group, **kwargs):
        security_group_body = {'security_group': {}}
        security_group_body['security_group'].update(kwargs)
        return self.q_update_resource(security_group['security_group'],
                                      security_group_body)

    def q_create_security_group_rule(self, security_group_id, **kwargs):
        security_group_rule = {}
        security_group_rule.update(kwargs)
        security_group_rule['security_group_id'] = security_group_id
        security_group_rule_body = {}
        security_group_rule_body['security_group_rule'] = security_group_rule
        return self.q_create_resource(security_group_rule_body)

    def q_delete_security_group_rule(self, rule):
        self.q_delete_resource(rule['security_group_rule'])
