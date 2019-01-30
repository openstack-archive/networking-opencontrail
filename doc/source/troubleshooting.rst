===============
Troubleshooting
===============


#. ``BadRequest: Bad virtual_network request: physical network must be configured.``

   Please ensure that you create local or vlan network.

   The origin of the problem is in incompatibility of some network types between OpenStack and Tungsten Fabric.
   Tungsten Fabric's vnc_openstack module supports only vlan and local networks,
   because it needs physical network and segmentation id both to be provided (vlan) or both to be empty (local).

   Choosing these two networks that are compatible with Tungsten Fabric can be enforced by ml2 config.
   File /etc/neutron/plugins/ml2/ml2_conf.ini should contain similar line (for full example of ml2 configuration see :doc:`devstack`)::

    [ml2]
    tenant_network_types = local,vlan

