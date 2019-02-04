======================
 Enabling in Devstack
======================

#. Download Devstack::

     git clone https://git.openstack.org/openstack-dev/devstack
     cd devstack

#. Copy the sample local.conf, if you already do not have local.conf::

     cp samples/local.conf .

#. In the local.conf add several lines as follows::

    [[local|localrc]]
    # (skipping already present lines...)

    # Enable ML2 plugin
    enable_plugin networking-opencontrail https://git.openstack.org/openstack/networking-opencontrail
    Q_PLUGIN=ml2
    ML2_L3_PLUGIN=opencontrail-router
    NEUTRON_CREATE_INITIAL_NETWORKS=False
    Q_USE_SECGROUP=True

    # Specify the Contrail API Server IP address and the port number
    OPENCONTRAIL_APISERVER_IP=192.168.0.16
    OPENCONTRAIL_APISERVER_PORT=8082

    # Configure ML2 plugin
    PHYSICAL_NETWORK=public
    TENANT_VLAN_RANGE=1:4094
    [[post-config|$NEUTRON_CORE_PLUGIN_CONF]]
    [ml2]
    type_drivers = local,vlan,gre
    tenant_network_types = local,vlan
    mechanism_drivers = opencontrail

    [[post-config|$NEUTRON_CONF]]
    [DEFAULT]
    network_scheduler_driver = networking_opencontrail.agents.dhcp_scheduler.TFIgnoreDHCPScheduler


#. Optionally, if you need to use secure SSL connection, specify additional
   configuration variables as below::

     > cat local.conf
     [[local|localrc]]
     OPENCONTRAIL_USE_SSL=True
     OPENCONTRAIL_INSECURE=False  # use https
     OPENCONTRAIL_CERT_FILE=<certificates file>
     OPENCONTRAIL_KEY_FILE=<Key file>
     OPENCONTRAIL_CA_FILE=<ca file>

#. run ``stack.sh``
