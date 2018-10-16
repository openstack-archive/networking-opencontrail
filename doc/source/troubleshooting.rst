===============
Troubleshooting
===============


#. ``BadRequest: Bad virtual_network request: physical network must be configured.``

   Please ensure that you create local or vlan network. File /etc/neutron/plugins/ml2/ml2_conf.ini should contain similar line (for full example of ml2 configuration see :doc:`devstack`)::

    [ml2]
    tenant_network_types = local,vlan

