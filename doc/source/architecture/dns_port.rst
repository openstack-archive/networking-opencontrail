===================================================
Synchronize Neutron with IP allocated for DNS in TF
===================================================

On creating subnet, Tungsten Fabric creates also a service which is used for
DNS and DHCP. This service use an IP in given subnet (typically this is
``x.x.x.2``), so it's allocated in TF and no other resource can use it.

To prevent from use this IP in OpenStack, plugin creates a port in Neutron
which is not propagated to Tungsten Fabric.

.. image:: creating_dns_port.png
