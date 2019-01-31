=====================
Architecture overview
=====================

Networking-opencontrail is plugin for Neutron containing a set of drivers
to be responsible for syncing all changes done in Neutron with Tungsten Fabric.

The plugin is built on top of the ML2 Mechanism Driver, which allows
to integrate Neutron with different network backends like Tungsten Fabric or OVS simultaneously.

Networking-opencontrail is an alternative for `Contrail neutron plugin`_,
which is less elastic and uses deprecated solution to integrate with Neutron.

Networking-opencontrail uses three different APIs to integrate with Neutron:

* ML2 Mechanism Driver - to manage Network, Subnet and Port resources
* Neutron Callback System - to manage Security group and Security group rule resources
* Service Plugins - to manage Router, Router interface and Floating IP resources

The integration with Tungsten Fabric is done by using the same API as Contrail neutron plugin,
and it utilizes `vnc_openstack module`_.

.. _Contrail neutron plugin: https://github.com/Juniper/contrail-neutron-plugin
.. _vnc_openstack module: https://github.com/Juniper/contrail-controller/tree/master/src/config/vnc_openstack

Networking-opencontrail architecture internals
----------------------------------------------

In general, all resources are synchronized using the common pattern.
Due to architecture of Neutron, the synchronization is done only in one direction - from Neutron to Tungsten Fabric.
Each resource has its handler for create, update or delete (there is no need for read operations).
The handler receives the context and resource data and pushes those data to Tungsten Fabric.

The main difference between Contrail neutron plugin and the networking-opencontrail
is that using the plugin, the Neutron rely on its own database, and Tungsten Fabric
only receives events about changes in Neutron database. The Tungsten Fabric database is not
read by Neutron any more.

One of the consequence of that fact is that resources in Neutron and Tungsten Fabric
must have the same uuid to match the resources each other while updating and deleting.

ML2 Mechanism Driver
~~~~~~~~~~~~~~~~~~~~
This is the main part of the driver, which is responsible for pushing changes of
**Networks**, **Subnets** and **Ports** to Tungsten Fabric.

The ML2 Mechanism Driver allows to override methods for precommit and postcommit phases of each resource modification.
Accordingly to the ML2 documentation, all calls to the external service (Tungsten Fabric API) are in the postcommit phase.

The precommit phase is reserved to quick calls due to opened transaction in Neutron.

Mechanism Drivers API is pretty well documented on `OpenStack page`_ and `Neutron wiki`_.

.. _OpenStack page: https://docs.openstack.org/neutron/latest/admin/config-ml2.html
.. _Neutron wiki: https://wiki.openstack.org/wiki/Neutron/ML2#Mechanism_Drivers

Neutron Callback System
~~~~~~~~~~~~~~~~~~~~~~~
Mechanism driver doesn't have hooks for security groups. We use Neutron callback system
to get notifications about changes made to **Security groups** and **Security group rules**.

The handlers for these resources are binded to callback events in
``networking_opencontrail.ml2.opencontrail_sg_callback.OpenContrailSecurityGroupHandler#subscribe``

Due to fact that both Neutron and Tungsten Fabric tries to create security group
named ``default``, the security group in Tungsten Fabric is renamed by plugin to ``default-openstack``
while creating. Then both security groups (``default`` in Neutron and
``default-openstack`` in Tungsten Fabric) have the same uuid.

Service Plugins
~~~~~~~~~~~~~~~
Hooks for **Routers**, **Router interfaces** and **Floating IPs** are provided by distinct
subsystem called service plugins. The driver is strongly inspired by the OpenDaylight one.

The driver overrides some methods from L3_NAT_db_mixin, therefore unlike other handlers,
it not only push data to Tungsten Fabric, but also executes methods from parent class
to create resources in Neutron.

The router plugin is also responsible for syncing Floating IPs.
The Neutron design of Floating IPs assumes that there is also corresponding Port in a Subnet.
It leads to conflict in Tungsten Fabric, because there is not possible to
create Port and Floating IP with the same IP. Therefore the networking-opencontrail
does not push the Floating IP's Port resource to the Tungsten Fabric.

Connectivity with Tungsten Fabric
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The component responsible for communicating with Tungsten Fabric is divided into two classes:

* OpenContrailDriversBase - it is responsible for preparing requests to Tungsten Fabric REST API
  and contains methods for all available operations. These methods call placeholders for backend interfaces.
* OpenContrailDrivers - it inherits OpenContrailDriversBase and overrides empty
  methods for pushing request to Tungsten Fabric API server. If you want to communicate with Tungsten Fabric you will use this class.

Methods for all available operations implemented in OpenContrailDriversBase have names based on the following pattern:

    * create_X
    * get_X
    * update_X
    * delete_X
    * get_Xs
    * get_Xs_count

where X might be substituted with:

    * network
    * subnet
    * router
    * floatingip
    * port
    * security_group
    * security_group_rule
    * route_table
    * nat_instance

They are simply wrappers for backend requests implemented in OpenContrailDrivers.
It should be noted that OpenContrailDrivers class appends "/neutron" suffix to an URL.
This URL points to vnc_openstack server, so the OpenContrailDrivers can't be used to
communicate with the ordinary REST API.

Vnc_openstack is module designed to perform a translation of Neutron data structures
to Tungsten Fabric representation. When request gets to Tungsten Fabric side
it's likely to be executed by the vnc_openstack first, and then translated to Tungsten Fabric VNC API.
