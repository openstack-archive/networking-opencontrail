#!/bin/sh

echo "Integraion testing with opencontrail"

OPENSTACK_IP="$1"
CONTRAIL_IP="$2"
echo "Contrail is: $CONTRAIL_IP; OpenStack is: $OPENSTACK_IP;"

pgrep keystone
echo "Port 5000"
curl http://127.0.0.1:5000
curl http://127.0.0.1:35357

export OS_USERNAME=admin
export OS_PASSWORD=admin
export OS_PROJECT_NAME=admin
export OS_PROJECT_DOMAIN_ID=default
export OS_USER_DOMAIN_ID=default
export OS_IDENTITY_API_VERSION=3
export OS_AUTH_URL=http://127.0.0.1:5000/identity

openstack network list
curl "http://$CONTRAIL_IP:8082/virtual-networks"

SpockID=$(openstack network create --project=demo spock | sed -n '/^id/ s/^.*="\([^"]\+\)"/\1/; T; p;')
curl "http://$CONTRAIL_IP:8082/virtual-networks" | grep "$SpockID"
