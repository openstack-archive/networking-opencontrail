#!/bin/sh

echo "Integraion testing with opencontrail"

OPENSTACK_IP="$1"
CONTRAIL_IP="$2"
echo "Contrail is: $CONTRAIL_IP; OpenStack is: $OPENSTACK_IP;"

set -x 

cat /opt/stack/devstack/userrc_early
source /opt/stack/devstack/userrc_early

openstack project list
openstack network list
curl -sk "http://$CONTRAIL_IP:8082/virtual-networks"

openstack domain create spockdom
openstack project create --domain spockdom spockproj

Response=$(openstack network create -f shell --project=demo spock)
echo "Spock create response: $Response"
SpockID=$(echo "$Response" | sed -n '/^id/ s/^.*="\([^"]\+\)"/\1/; T; p;')
SpockContrail=$(curl -sk "http://$CONTRAIL_IP:8082/virtual-networks")
echo "$SpockContrail" | grep "$SpockID"
