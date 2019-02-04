========================================
Not scheduling DHCP agent to TF networks
========================================

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
way, any not-TF network can be normally scheduled by agents). Agents'
details can be found in `OpenStack documentation`_.

.. _OpenStack documentation: https://docs.openstack.org/neutron/latest/admin/config-dhcp-ha.html

Networking-opencontrail prepared a DHCP scheduler which prevents Neutron
from adding DHCP agent to TF-based network and uses default
(``WeightScheduler``) scheduler for other networks. It can be enabled
in `neutron.conf`::

    network_scheduler_driver = networking_opencontrail.agents.dhcp_scheduler.TFIgnoreDHCPScheduler
