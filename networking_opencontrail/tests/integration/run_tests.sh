#!/bin/sh

echo "Integraion testing with opencontrail"

OPENSTACK_IP="$1"
CONTRAIL_IP="$2"
echo "Contrail is: $CONTRAIL_IP; OpenStack is: $OPENSTACK_IP;"

OpenStackCmd()
{
	openstack --os-username=admin --os-password=admin --os-project-name=admin --os-auth-url=http://127.0.0.1:5000/identity "$@"
}

OpenStackCmd network list
OpenStackCmd software config list
curl "http://$CONTRAIL_IP:8082/virtual-networks"

SpockID=$(OpenStackCmd network create --project=demo spock | sed -n '/^id/ s/^.*="\([^"]\+\)"/\1/; T; p;')
curl "http://$CONTRAIL_IP:8082/virtual-networks" | grep "$SpockID"
