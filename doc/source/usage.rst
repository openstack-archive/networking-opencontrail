========
Usage
========

Using networking-opencontrail in a project
==========================================

To use networking-opencontrail in a project::

    import networking_opencontrail

Using networking-opencontrail as an OpenStack ML2 driver
========================================================

When installed via DevStack
---------------------------

Installing networking-opencontrail as a DevStack plugin (see
:doc:`devstack`) does not require any further configuration changes.

Manual configuration
--------------------

#. Install plugin::

    pip install networking-opencontrail

#. Adjust ``/etc/neutron/plugins/ml2/ml2_conf_opencontrail.ini``
   to meet the example::

    [APISERVER]
    api_server_port = 8082
    api_server_ip = 192.168.0.2

#. Adjust ``/etc/neutron/neutron.conf`` to meet the example.

   * Ensure you have ``ml2`` core plugin enabled
   * Add ``opencontrail-router`` to ``service_plugins`` list.

   Example::

    [DEFAULT]
    core_plugin = ml2
    service_plugins = opencontrail-router

#. Edit ``/etc/neutron/plugins/ml2/ml2_conf.ini`` file:

   * Add ``opencontrail`` to ``mechanism_drivers`` list in ``ml2`` section.

   After editing file should look similarly to this::

    [ml2]
    type_drivers = local,vlan
    tenant_network_types = local,vlan
    extension_drivers = port_security
    mechanism_drivers = opencontrail

#. Run again Neutron service. Make sure you include all config files: ::

    /usr/local/bin/neutron-server --config-file /etc/neutron/neutron.conf \
    --config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
    --config-file /etc/neutron/plugins/ml2/ml2_conf_opencontrail.ini
