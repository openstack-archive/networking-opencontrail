==============================
Installation and configuration
==============================

Installation of package depends on the environment you are running. The most general way to install package is::

    $ pip install \
      -c https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt \
      -e git+https://git.openstack.org/openstack/networking-opencontrail#egg=networking-opencontrail


DevStack environment
--------------------

Installing networking-opencontrail as a DevStack plugin (see devstack README:
:doc:`devstack`) does not require any further configuration changes.

Manual configuration
--------------------

#. Assume you installed the plugin as described at the beginning of the chapter using ``pip``

#. Adjust ``/etc/neutron/neutron.conf`` to meet the example.

   * Ensure you have ``ml2`` core plugin enabled.
   * Add ``opencontrail-router`` to ``service_plugins`` list.
   * Select ``network_scheduler_driver`` due to manage DHCP agent scheduling.
     More description in :ref:`troubleshooting <dhcp-schedule-decription>`.

   Example::

    [DEFAULT]
    core_plugin = ml2
    service_plugins = opencontrail-router
    network_scheduler_driver = networking_opencontrail.agents.dhcp_scheduler.TFIgnoreDHCPScheduler

#. Edit ``/etc/neutron/plugins/ml2/ml2_conf.ini`` file:

   * Add ``opencontrail`` to ``mechanism_drivers`` list in ``ml2`` section.

   After editing file should look similarly to this::

    [ml2]
    type_drivers = local,vlan,gre
    tenant_network_types = local,vlan
    mechanism_drivers = opencontrail

#. Create a new file ``/etc/neutron/plugins/ml2/ml2_conf_opencontrail.ini``
   and write an IP and a port of the Tungsten Fabric REST API to meet the example::

    [APISERVER]
    api_server_ip = 192.168.0.2
    api_server_port = 8082

#. Make sure you include all config files in the Neutron server parameters::

    /usr/local/bin/neutron-server --config-file /etc/neutron/neutron.conf \
    --config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
    --config-file /etc/neutron/plugins/ml2/ml2_conf_opencontrail.ini

#. Restart neutron-server


Manual configuration on a Kolla deployment
------------------------------------------

Installation the plugin on a Kolla deployment for a development version
does not much differ from manual installation.
There are only some minor differences like config file locations.

Assume that the Kolla was deployed using this guide: `kolla_quickstart`_.

.. _kolla_quickstart: https://docs.openstack.org/kolla-ansible/queens/user/quickstart.html

#. Install plugin into neutron_server docker container::

    docker exec -it neutron_server git clone https://github.com/openstack/networking-opencontrail.git /tmp/networking-opencontrail
    docker exec -u 0 -it neutron_server bash -c 'cd /tmp/networking-opencontrail; python setup.py install'

#. Edit section Default in ``/etc/kolla/neutron-server/neutron.conf``::

    [DEFAULT]
    core_plugin = ml2
    service_plugins = opencontrail-router

#. Edit section ml2 in ``/etc/kolla/neutron-server/ml2_conf.ini``::

    [ml2]
    type_drivers = vlan,local,gre
    tenant_network_types = local,vlan
    mechanism_drivers = opencontrail

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
