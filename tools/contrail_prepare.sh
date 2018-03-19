#!/bin/bash

echo "RUN: $0 with args $*"

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
	sudo yum -y install python-pip -compose ansible
	# Need docker python library in version 2.6.1 until https://github.com/ansible/awx/issues/1197 is fixed
	sudo pip install docker==2.6.1 docker-py docker-compose
	sudo pip install -U docker-compose

	# Dirty ugly workaround on contrail-ansible-deployer not using become in playbooks
	sudo mkdir -p /var/log/contrail
	sudo mkdir -p /etc/contrail
	sudo chmod 777 /var/log/contrail /etc/contrail
	# End of workaround
}

install_prereq

