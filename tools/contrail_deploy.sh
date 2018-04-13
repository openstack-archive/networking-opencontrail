#!/bin/bash

echo "RUN: $0 with args $*"

CONTRAIL_IP="$1"
OPENSTACK_IP="$2"
echo "Contrail host IP = $CONTRAIL_IP"
echo "Contrail host IP = $OPENSTACK_IP"

ip route get 8.8.8.8
ping -c 4 "$CONTRAIL_IP"
echo "HOME is $PWD - $HOME"
uanme -a
id

install_contrail()
{
	cd
	git clone http://github.com/Juniper/contrail-ansible-deployer
	cd contrail-ansible-deployer

	cat > ./inventory/hosts << EOF
[container_hosts]
$CONTRAIL_IP
EOF

	cat > ./config/instances.yaml << EOF
instances:
  ins1:
    provider: bms
    ip: $CONTRAIL_IP
    roles:
      configdb:
	 config_database:
	 config:
	 control:
	 webui:
	 analytics:
	 analyticsdb:
	 analytics_database:
	 vrouter:
      openstack_compute:

global_configuration:
  CONTAINER_REGISTRY: opencontrailnightly

contrail_configuration:
  CONTRAIL_VERSION: latest
  CONTROLLER_NODES: $CONTRAIL_IP
  AUTH_MODE: keystone
  KEYSTONE_AUTH_ADMIN_PASSWORD: admin
  KEYSTONE_AUTH_HOST: $OPENSTACK_IP
  CONTROL_NODES: $CONTRAIL_IP
  ANALYTICSDB_NODES: $CONTRAIL_IP
  WEBUI_NODES: $CONTRAIL_IP
  ANALYTICS_NODES: $CONTRAIL_IP
  CONFIGDB_NODES: $CONTRAIL_IP
  CONFIG_NODES: $CONTRAIL_IP
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
ln -sf ./instances.yaml ./config/instances.yml

	cat > ansible.cfg << EOF
[defaults]
log_path=/tmp/ansible.log
host_key_checking = False
jinja2_extensions=jinja2.ext.do
EOF

	echo "Start ANSIBLE deployment"
	echo '-> Hosts file:'
	cat ./inventory/hosts
	echo '-> instances.yaml file:'
	cat ./config/instances.yaml

	echo '-> Run ansible (provision_instances)...'
	ansible-playbook -e skip_openstack=true -i inventory/ playbooks/provision_instances.yml

	[ $? -ne 0 ] && { echo "-> Provision instances fail, aborting - will not install contrail"; exit 2; }
	echo '-> Run ansible (install_contrail)...'
	ansible-playbook -e skip_openstack=true -e '{"CREATE_CONTAINERS":true}' -e orchestrator=none -i inventory/ playbooks/install_contrail.yml
	echo '-> DONE!'
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
