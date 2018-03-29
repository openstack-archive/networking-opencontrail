#!/bin/sh

CONTRAIL_IP="$1"
OPENSTACK_IP="$2"

uname -a
cat /etc/redhat-release
echo 'Test OK'
echo "Contrail is: $CONTRAIL_IP; OpenStack is: $OPENSTACK_IP;"

curl "http://$CONTRAIL_IP:8082/virtual-networks"

