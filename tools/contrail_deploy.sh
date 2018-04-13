#!/bin/bash

echo "RUN: $0 with args $*"

CONTRAIL_IP="$1"
OPENSTACK_IP="$2"
echo "Contrail host IP = $CONTRAIL_IP"
echo "Contrail host IP = $OPENSTACK_IP"

ip route get 8.8.8.8
ping -c 4 "$CONTRAIL_IP"

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
	cat > ./inventory/hosts << EOF
[container_hosts]
$CONTRAIL_IP
EOF

	cat > ./inventory/group_vars/container_hosts.yml << EOF
contrail_configuration:
  CONTAINER_REGISTRY: opencontrailnightly
  CONTRAIL_VERSION: latest
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

	cat > ansible.cfg << EOF
[defaults]
log_path=/tmp/ansible.log
host_key_checking = False
jinja2_extensions=jinja2.ext.do
EOF

	echo "Start ANSIBLE deployment"
	echo '-> Hosts file:'
	cat ./inventory/hosts
	echo '-> container_hosts.yml file:'
	cat ./inventory/group_vars/container_hosts.yml

	#ansible-playbook -e '{"CREATE_CONTAINERS":true}' -i inventory/ playbooks/deploy.yml

	echo '-> Run ansible...'
	ansible-playbook -e skip_openstack=true -i inventory/ playbooks/provision_instances.yml
	[ $? -ne 0 ] && exit 2
	ansible-playbook -e skip_openstack=true -e '{"CREATE_CONTAINERS":true}' -e orchestrator=none -i inventory/ playbooks/install_contrail.yml
}

install_prereq()
{
	sudo add-apt-repository ppa:ansible/ansible
	sudo apt-get update
	sudo apt-get -y install ansible

	echo "Ansible version:"
	ansible-playbook --version

	sudo pip install -U docker docker-compose
}

install_prereq
install_contrail

echo 'Contrail networks:'
curl "http://$CONTRAIL_IP:8082/virtual-networks"
