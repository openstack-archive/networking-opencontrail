=====================
Setup development VMs
=====================

Playbooks are designed to setup two nodes using devstack. The first node
contains openstack with, among others, keystone, neutron
and neutron-opencontrail plugin as ML2 L3 driver. Second node contains
minimal version of openstack with enabled plugin for contrail built from
sources.

By default playbooks build contrail from sources. But to avoid long process of
building contrail and system related errors while installation,
a contrail-ansible-deployer can be used to setup contrail node from
nightly-build. Step by step instruction is presented below.

Using Ansible playbooks for both nodes
--------------------------------------

Initial steps
~~~~~~~~~~~~~

Before you run playbooks perform the following steps:

#. Prepare machines for Contrail node and OpenStack node. Recommended OS is Ubuntu 16.04

#. Make sure you have key-based SSH access to prepared nodes::

    ssh contrail-node
    ssh openstack-node

#. Install python on both nodes::

    sudo apt install python

#. Install Ansible::

    sudo apt install ansible

Configuring playbooks
~~~~~~~~~~~~~~~~~~~~~

Be sure to adjust configuration according to your setup before running
any playbook:

#. Define nodes by specifying SSH names of their machines in ``playbooks/hosts`` file::

    [contrail]
    contrail-node

    [openstack]
    openstack-node

#. Configure deployment by setting ``playbooks/group_vars/all.yml`` variables, for example::

    ---
    # Internal IP addresses of both nodes
    contrail_ip: 192.168.0.2
    openstack_ip: 192.168.0.3

    # Names of git branches
    openstack_branch: stable/ocata
    contrail_branch: R4.1

    kernel_version: 4.4.0-112

Setup OpenContrail & Devstack VMs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run ``main.yml`` playbook (it could take few hours to finish)::

     playbooks/main.yml


NOTICE
~~~~~~

If you are installing Openstack Ocata after successful deployment
be sure to issue command listed below on OpenStack
node, otherwise scheduling VM using Nova won't work.

.. code-block:: bash

     nova-manage cell_v2 simple_cell_setup

Contrail from nightly-builds
----------------------------

Let's assume there are two hosts:

+-----------+--------------+----------------+--------------+------------------------------------+
| Node      | OS           | Public ip      | Internal ip  | Notes                              |
+===========+==============+================+==============+====================================+
| openstack | Ubuntu 16.04 | N/A            | 192.168.0.3  | setup by playbooks                 |
+-----------+--------------+----------------+--------------+------------------------------------+
| contrail  | CentOS 7.4   | 10.100.0.2     | 192.168.0.2  | setup by contrail-ansible-deployer |
+-----------+--------------+----------------+--------------+------------------------------------+

Openstack node
~~~~~~~~~~~~~~

Configuring and running playbooks are similar:

#. ``playbooks/hosts`` file::

    [openstack]
    openstack-node

#. ``playbooks/group_vars/all.yml`` file::

    ---
    # Internal IP addresses of both nodes
    contrail_ip: 192.168.0.2
    openstack_ip: 192.168.0.3

    # Names of git branches
    openstack_branch: stable/ocata
    contrail_branch: R4.1

    kernel_version: 4.4.0-112

#. And finally only openstack host should be deployed::

    ./main.yml --limit=openstack

Contrail node
~~~~~~~~~~~~~

1. First, get contrail-ansible-deployer::

    git clone http://github.com/Juniper/contrail-ansible-deployer

2. Configure:

  * Hosts::

      cat ~/contrail-ansible-deployer/inventory/hosts

      container_hosts:
        hosts:
          10.100.0.2:
            ansible_ssh_user: centos


  * Containers:

    Currently, nightly-builds are available in docker hub's opencontrailnightly repo.
    At https://hub.docker.com/r/opencontrailnightly/contrail-agent-vrouter/tags/ can be viewed available contrail builds.
    One of the tag should be put in CONTRAIL_VERSION variable::

      cat ~/contrail-ansible-deployer/inventory/group_vars/container_hosts.yml

      contrail_configuration:
        CONTAINER_REGISTRY: opencontrailnightly
        CONTRAIL_VERSION: ocata-master-17
        CONTROLLER_NODES: 192.168.0.2
        CLOUD_ORCHESTRATOR: openstack
        AUTH_MODE: keystone
        KEYSTONE_AUTH_ADMIN_PASSWORD: admin
        KEYSTONE_AUTH_HOST: 192.168.0.3
        RABBITMQ_NODE_PORT: 5673
        PHYSICAL_INTERFACE: eth1
        VROUTER_GATEWAY: 192.168.0.1
      roles:
        10.100.0.2:
          configdb:
          config_database:
          config:
          control:
          webui:
          analytics:
          analyticsdb:
          analytics_database:
          vrouter:

3. Deploy Contrail::

    cd ~/contrail-ansible-deployer
    ansible-playbook -e '{"CREATE_CONTAINERS":true}' -i inventory/ playbooks/deploy.yml
