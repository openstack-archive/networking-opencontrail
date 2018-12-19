===============
Flavors support
===============

Networking-opencontrail supports use of flavors in Neutron. It allows to
use multiple L3 backends, so it's possible to configure multiple compute
hosts with different drivers.

Configuration
=============

Enable flavor
-------------

To enable flavor support, in ``neutron.conf`` service plugin should be set
to default and service providers should be added.

Service plugin::

    service_plugins = neutron.services.l3_router.l3_router_plugin.L3RouterPlugin

Service providers should be added at the end of file::

    [service_providers]
    service_provider = L3_ROUTER_NAT:TF:networking_opencontrail.l3.l3_flavor.TFL3ServiceProvider

Registry flavor
---------------

Flavor, and profile for them, must be created and connected in neutron by CLI.
In OpenStack console::

    openstack network flavor profile create --driver networking_opencontrail.l3.l3_flavor.TFL3ServiceProvider
    openstack network flavor create --service-type L3_ROUTER_NAT tf
    openstack network flavor add profile tf <flavorprofileid>

Where ``tf`` is an arbitrary name and ``<flavorprofileid>`` should be replaced
with an uuid from flavor profile create output.

Usage
=====

Flavor can be selected only from CLI. When you create router from horizon,
it uses a default driver.

To create a router with `tf`-named flavor::

    neutron router-create router_name --flavor tf

Now router should be created and can be managed like any other router, also
from horizon.

References
==========
* `Neutron flavor specification <https://specs.openstack.org/openstack/neutron-specs/specs/newton/multi-l3-backends.html>`_
