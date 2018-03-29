#!/bin/sh

CONTRAIL_IP="$1"
OPENSTACK_IP="$2"
LOG_DIR="$3"

uname -a
cat /etc/redhat-release
cat /etc/os-release
echo 'Test OK'
echo "Contrail is: $CONTRAIL_IP; OpenStack is: $OPENSTACK_IP;"

openstack --os-username=admin --os-password=admin --os-project-name=admin --os-auth-url=http://127.0.0.1:5000/identity network list
openstack --os-username=admin --os-password=admin --os-project-name=admin --os-auth-url=http://127.0.0.1:5000/identity software config list
curl "http://$CONTRAIL_IP:8082/virtual-networks"

echo 'Neutron logs:'
cat "$LOG_DIR/q-svc.log"
echo 'END OF => Neutron logs'

