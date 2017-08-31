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

#. Adjust ``/etc/neutron/plugins/ml2/ml2_conf_opencontrail.ini`` to meet
   your needs.
#. Edit ``/etc/neutron/plugins/ml2/ml2_conf.ini`` file:

   * Add ``opencontrail`` to ``mechanism_drivers`` list in ``ml2`` section
   * Add ``opencontrail-router`` to ``service_plugins`` list in ``DEFAULT`` section

   After editing file should look similarly to this::

    [DEFAULT]
    service_plugins = opencontrail-router

    [ml2]
    mechanism_drivers = opencontrail

#. Run again Neutron service. Make sure you include all config files: ::

    /usr/local/bin/neutron-server --config-file /etc/neutron/neutron.conf \
    --config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
    --config-file /etc/neutron/plugins/ml2/ml2_conf_opencontrail.ini

Support for BGPVPN extension
----------------------------

To enable support for BGPVPN extension:

#. Make sure `contrail-neutron-plugin <https://github.com/Juniper/contrail-neutron-plugin>`_
   with its dependencies (packages ``cfgm_common``, ``vnc_api``) is installed.

#. Make sure ``networking-bgpvpn`` is installed and enabled
   (see `official installation guide <https://docs.openstack.org/networking-bgpvpn/latest/install/index.html#installation>`_).

#. Enable Contrail plugin by editing Neutron config file::

      [service_providers]
      service_provider = BGPVPN:OpenContrail:networking_opencontrail.bgpvpn.bgpvpn.ContrailBGPVPNDriver:default

   .. note::
      Don't use `default plugin <https://docs.openstack.org/networking-bgpvpn/latest/user/drivers/opencontrail/index.html>`_
      supplied with networking-bgpvpn because it misses functionality for handling routers.
