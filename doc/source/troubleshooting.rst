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

#. DHCP scheduling in Neutron
    .. _dhcp-schedule-decription:

    Both Neutron and Tungsten Fabric have their own DHCP service. When network
    is managed by TF, only DHCP from TF works, but Neutron tries to
    assign any network to DHCP agents. DHCP tries to create one port per
    network and assign to it an IP from any subnet with enabled DHCP.

    This is the cause of two problems:

    * Default IP for DHCP port is usually allocated by TF for their
      own DHCP & DNS service.
    * The ``vnc_openstack`` module doesn't support updating Fixed IP for ports,
      so when DHCP agent tries to change subnets assigned to his ports, it
      fails.

    To resolve those problems, we can disable assigning DHCP agents in Neutron
    or prevent Neutron from adding network from TF to their DHCP agent (in this
    way, any not-TF network can by normally scheduled by agents). Agents'
    details can be found in `OpenStack documentation`_.

    .. _OpenStack documentation: https://docs.openstack.org/neutron/latest/admin/config-dhcp-ha.html

    Networking-opencontrail prepared a DHCP scheduler which prevents Neutron
    from adding DHCP agent to TF-based network and uses default
    (``WeightScheduler``) scheduler for other networks. It can be enabled
    in `neutron.conf`::

     network_scheduler_driver = networking_opencontrail.agents.dhcp_scheduler.TFIgnoreDHCPScheduler

