=====================
Architecture overview
=====================

Networking-opencontrail uses three different APIs to integrate with Neutron:

* ML2 Mechanism Driver - to manage Network, Subnet and Port resources
* Neutron Callback System - to manage Security group and Security group rule resources
* Service Plugins - to manage Router, Router interface and Floating IP resources

The integration with Tungsten Fabric is done by vnc_openstack module.
