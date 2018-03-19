#!/bin/bash

echo "RUN: $0 with args $@"

OPENSTACK_IP="$1"
echo "OpenStack IP = $OPENSTACK_IP"

install_prereq()
{
	sudo yum remove -y docker docker-common docker-selinux docker-engine
	sudo yum install -y yum-utils device-mapper-persistent-data lvm2
	sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
	sudo yum -y install docker-ce
	sudo groupadd docker
	sudo usermod -aG docker $USER
	sudo service docker start

	sudo yum -y install epel-release
	sudo yum -y update
	sudo yum -y install python-pip docker-compose ansible
	sudo pip install docker-py docker-compose
}

install_contrail()
{
	# Dirty ugly workaround on contrail-ansible-deployer not using become in playbooks
	sudo mkdir -p /var/log/contrail
	sudo mkdir -p /etc/contrail
	sudo chmod 777 /var/log/contrail /etc/contrail
	# End of workaround

	cd
	git clone http://github.com/Juniper/contrail-ansible-deployer
	cd contrail-ansible-deployer
	cat > ./inventory/hosts << EOF
container_hosts:
  hosts:
    127.0.0.1:
EOF
	
	cat > inventory/group_vars/container_hosts.yml << EOF
contrail_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
  CONTRAIL_VERSION: ocata-master-17
  CONTROLLER_NODES: 127.0.0.1
  CLOUD_ORCHESTRATOR: openstack
  AUTH_MODE: keystone
  KEYSTONE_AUTH_ADMIN_PASSWORD: admin
  KEYSTONE_AUTH_HOST: $OPENSTACK_IP
  #RABBITMQ_NODE_PORT: 5673
  #PHYSICAL_INTERFACE: eth1
  #VROUTER_GATEWAY: 192.168.0.1
roles:
  127.0.0.1:
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

install_prereq
install_contrail

