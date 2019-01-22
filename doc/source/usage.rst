========
Usage
========

Using networking-opencontrail as an OpenStack Neutron plugin
============================================================

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
    type_drivers = local,vlan,gre
    tenant_network_types = local,vlan
    extension_drivers = port_security
    mechanism_drivers = opencontrail

#. Run again Neutron service. Make sure you include all config files: ::

    /usr/local/bin/neutron-server --config-file /etc/neutron/neutron.conf \
    --config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
    --config-file /etc/neutron/plugins/ml2/ml2_conf_opencontrail.ini


Manual configuration on Kolla deployment
----------------------------------------

Installation plugin on Kolla deployment for development version
does not much differ from normal installation.
There are only some minor differences like config file locations.

Assume that Kolla was deployed using this guide: `kolla_quickstart`_.

.. _kolla_quickstart: https://docs.openstack.org/kolla-ansible/queens/user/quickstart.html

#. Install plugin into neutron_server docker container::

    docker exec -it neutron_server git clone https://github.com/openstack/networking-opencontrail.git /tmp/networking-opencontrail
    docker exec -u 0 -it neutron_server bash -c 'cd /tmp/networking-opencontrail; python setup.py install'

#. Edit section ml2 in ``/etc/kolla/neutron-server/ml2_conf.ini``::

    [ml2]
    type_drivers = vlan,local,gre
    tenant_network_types = local
    mechanism_drivers = opencontrail
    extension_drivers = port_security

#. Edit section Default in ``/etc/kolla/neutron-server/neutron.conf``::

    [DEFAULT]
    core_plugin = ml2
    service_plugins = opencontrail-router

#. Add file ``/etc/kolla/neutron-server/ml2_conf_opencontrail.ini``::

    [APISERVER]
    api_server_ip = 192.168.0.2
    api_server_port = 8082

#. Edit ``/etc/kolla/neutron-server/config.json``:

    #. Add ``--config-file /etc/neutron/ml2_conf_opencontrail.ini`` at the end of neutron-server command
    #. Add ``ml2_conf_opencontrail.ini`` to config files ::

        "config_files": [
            {
                "source": "/var/lib/kolla/config_files/ml2_conf_opencontrail.ini",
                "dest": "/etc/neutron/ml2_conf_opencontrail.ini",
                "owner": "neutron",
                "perm": "0600"
            },

#. Restart neutron::

    docker restart neutron_server
