====================================================
Synchronize Neutron with IP allocated for SNAT in TF
====================================================

When router with external gateway is created (or external gateway is connected
to existing router), Tungsten Fabric create a SNAT service which need two
virtual machine interfaces: one is with an internal IP used by vrouter and
is called as ``left IP``, second is with an IP in given external network,
called as ``right IP``. This right IP should be propagated to Neutron to
prevent allocating it to other resources.

This service and both IPs are created asynchronous, so they are not included
in response from Tungsten Fabric. Also ``vnc_opentack`` has no callback to get
this information.

.. figure:: snat_synchronize.png
    :width: 100%
    :alt: Diagram of creating router and allocating IP for SNAT service

As showed on diagram, plugin get right IP from REST API, the full set of
requests are showed below. Because SNAT service is created asynchronous,
plugin makes a few retries with small waiting time to get right IP.
After three retries there is no more attempt, TF probably not created SNAT.

.. figure:: snat_get_ip_callbacks.png
    :width: 100%
    :alt: Diagram of callbacks needed to get right SNAT IP from Tungsten Fabric

Tungsten Fabric doesn't include SNAT IPs in any specific place, to get it
plugin have to make set of REST callbacks which are determined by structure
of connections between TF objects as on picture below. Plugin get list of
uuids form every step and search for objects related to SNAT.

.. figure:: snat_service_classes.png
    :width: 100%
    :alt: Diagram of connections between Logical Router and IP for SNAT
