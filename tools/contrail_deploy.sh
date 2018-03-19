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
	sudo pip install docker-py
}

install_contrail()
{
	cd
	git clone http://github.com/Juniper/contrail-ansible-deployer
	cd contrail-ansible-deployer
	cat > ./inventory/hosts << EOF
container_hosts:
  hosts:
    127.0.0.1:
EOF
	
}

install_prereq
install_contrail

cat contrail-ansible-deployer/inventory/group_vars/container_hosts.yml

