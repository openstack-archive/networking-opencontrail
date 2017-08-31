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

.. note::
   BGPVPN extension is supported only on Contrail 4.0 or higher.

To enable support for BGPVPN extension:

#. Install dependencies - ``cfgm_common`` and ``vnc_api``. They can be obtained from Contrail node::

    scp -r contrail-node:/opt/stack/contrail/build/production/config/common ~/
    scp -r contrail-node:/opt/stack/contrail/build/production/api-lib ~/
    sudo pip install ~/api-lib ~/common

#. Install `contrail-neutron-plugin <https://github.com/Juniper/contrail-neutron-plugin>`_ package::

    git clone https://github.com/Juniper/contrail-neutron-plugin.git
    sudo pip install contrail-neutron-plugin

#. Make sure ``networking-bgpvpn`` is installed and enabled
   (see `official installation guide <https://docs.openstack.org/networking-bgpvpn/latest/install/index.html#installation>`_).

#. Enable Contrail extension driver by editing Neutron config file (i.e. ``/etc/neutron/plugins/ml2/ml2_conf.ini``)::

      [service_providers]
      service_provider = BGPVPN:OpenContrail:networking_opencontrail.bgpvpn.bgpvpn.ContrailBGPVPNDriver:default

#. Restart ``neutron-server``.

   .. warning::
      Don't use `default plugin <https://docs.openstack.org/networking-bgpvpn/latest/user/drivers/opencontrail/index.html>`_
      supplied with networking-bgpvpn, it is incomplete and misses some functionality.
