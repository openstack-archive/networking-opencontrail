#!/bin/bash

echo "RUN: $0 with args $*"

CONTRAIL_IP="$1"
OPENSTACK_IP="$2"
echo "Contrail host IP = $CONTRAIL_IP"
echo "Contrail host IP = $OPENSTACK_IP"

install_contrail()
{
	cd
	git clone http://github.com/Juniper/contrail-ansible-deployer
	cd contrail-ansible-deployer
	cat > ./inventory/hosts << EOF
container_hosts:
  hosts:
    $CONTRAIL_IP:
EOF
	
	cat > inventory/group_vars/container_hosts.yml << EOF
contrail_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
  CONTRAIL_VERSION: ocata-master-17
  CONTROLLER_NODES: $CONTRAIL_IP
  CLOUD_ORCHESTRATOR: openstack
  AUTH_MODE: keystone
  KEYSTONE_AUTH_ADMIN_PASSWORD: admin
  KEYSTONE_AUTH_HOST: $OPENSTACK_IP
roles:
  $CONTRAIL_IP:
    configdb:
    config_database:
    config:
    control:
    webui:
    analytics:
    analyticsdb:
    analytics_database:
    vrouter:
EOF
	
	ansible-playbook -e '{"CREATE_CONTAINERS":true}' -i inventory/ playbooks/deploy.yml
}

install_prereq()
{
	sudo yum -y install ansible
}

install_prereq
install_contrail

