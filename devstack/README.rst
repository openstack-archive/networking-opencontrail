======================
 Enabling in Devstack
======================

1. Download DevStack::

     git clone https://git.openstack.org/openstack-dev/devstack
     cd devstack

2. Copy the sample local.conf, if you already do not have local.conf::

     cp devstack/samples/local.conf local.conf

3. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin networking-opencontrail http://git.openstack.org/openstack/networking-opencontrail

4. Specify the Contrail API Server IP address and the port number::

     > cat local.conf
     [[local|localrc]]
     OPENCONTRAIL_APISERVER_IP=<ip address>
     OPENCONTRAIL_APISERVER_PORT=<port-number>

5. Optionally, if you need to use secure SSL connection, specify additional
   configuration variables as below::

     > cat local.conf
     [[local|localrc]]
     OPENCONTRAIL_USE_SSL=True
     OPENCONTRAIL_INSECURE=False  # use https
     OPENCONTRAIL_CERT_FILE=<certificates file>
     OPENCONTRAIL_KEY_FILE=<Key file>
     OPENCONTRAIL_CA_FILE=<ca file>

6. run ``stack.sh``
