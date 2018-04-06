=====================
Setup development VMs
=====================

Playbooks are designed to setup two nodes using devstack. The first node
contains Openstack with, among others, keystone, neutron
and neutron-opencontrail plugin as ML2 L3 driver.
Second node contains nightly-build contrail node.

Step by step instruction is presented below.


*************
Initial steps
*************

Before you run playbooks perform the following steps:

**1. Prepare machines for Contrail (CentOS) node and OpenStack (Ubuntu) node.**

**2. Make sure you have key-based SSH access to prepared nodes**

.. code-block:: console

    $ ssh contrail-node
    $ ssh openstack-node

**3. Install Ansible on your host**

.. code-block:: console

    $ sudo apt install ansible


*******************
Configure playbooks
*******************

Configuration require editing few files before running any playbook.

**1. Define nodes by specifying SSH names or IP of machines in ``playbooks/hosts``**

.. code-block:: console

    $ vim playbooks/hosts

Change ``contrail-node`` and ``openstack-node`` to public IP of your machines.

.. code-block:: text

    [contrail]
    10.100.0.2

    [openstack]
    10.100.0.3

**2. Change deployment variables in ``playbooks/group_vars/all.yml``**

.. code-block:: console

    $ vim playbooks/group_vars/all.yml

``contrail_ip`` and ``openstack_ip`` should be local IP addresses.

``openstack_branch`` and ``contrail_branch`` may be set to any valid
branches but it is highly recommended to use only stable branches.

Example config:

.. code-block:: yaml

    # [Required] IP address for OpenConrail VM.
    contrail_ip: 192.168.0.9
    # [Required] IP address for Openstack VM.
    openstack_ip: 192.168.0.8

    # [Required] Openstack branch used on VMs.
    openstack_branch: stable/ocata
    # [Required] OpenContrail branch to build on VM.
    contrail_branch: R4.1

    # [Required] Kernel version supported by OpenContrail branch.
    kernel_version: 4.4.0-112

**3. Enable networking-opencontrail plugin**

.. note:: Plugin branch should be the same as OpenStack.
          For example if openstack_branch is ``stable/ocata``
          plugin also should point to ``stable/ocata`` branch.

Update ``openstack_local.conf.j2`` template.

.. code-block:: console

    $ vim playbooks/roles/fetch_devstack/templates/openstack_local.conf.j2

.. warning:: If plugin is already defined,
             make sure URL and branch version is correct.

At the end of file add new line with ``enable_plugin`` directive.

.. code-block:: text

    enable_plugin networking-opencontrail https://github.com/openstack/networking-opencontrail stable/ocata


**********
Deployment
**********

Let's assume there are two hosts:

+-----------+--------------+----------------+--------------+------------------------------------+
| Node      | OS           | Public ip      | Internal ip  | Notes                              |
+===========+==============+================+==============+====================================+
| openstack | Ubuntu 16.04 | 10.100.0.3     | 192.168.0.3  | setup by playbooks                 |
+-----------+--------------+----------------+--------------+------------------------------------+
| contrail  | CentOS 7.4   | 10.100.0.2     | 192.168.0.2  | setup by contrail-ansible-deployer |
+-----------+--------------+----------------+--------------+------------------------------------+


Openstack node
==============

.. note:: Before openstack deployment make sure Playbooks are configured.

Run playbooks with command:

.. code-block:: console

    $ ./main.yml --limit=openstack

Or in case shebang has not been correctly recognized

.. code-block:: console

    $ ansible-playbook ./main.yml --limit=openstack


Contrail node
=============

**1. Clone Contrail Ansible Deployer from Github**

.. code-block:: console

    $ git clone http://github.com/Juniper/contrail-ansible-deployer

**2. Define contrail node by specifying SSH name or IP of machine in ``inventory/hosts``**

.. warning:: If file is not empty. Remove everything and start from scratch.

Edit hosts file

.. code-block:: console

    $ vim inventory/hosts

Copy and paste snippet and change IP to Contrail machine public IP

.. code-block:: text

    [container_hosts]
    10.100.0.2 ansible_user=centos

**3. Contrail nightly builds variables**

Currently, nightly-builds are available in docker hub's opencontrailnightly repo.
At https://hub.docker.com/r/opencontrailnightly/contrail-agent-vrouter/tags/
can be viewed available contrail builds.

* ``CONTRAIL_VERSION``: container tag for example ``latest``
* ``CONTROLLER_NODES``: internal IP of contrail node
* ``KEYSTONE_AUTH_HOST``: internal IP of openstack node
* roles ``<IP>``: public IP of contrail node

Example config:

.. code-block:: yaml

    contrail_configuration:
      CONTAINER_REGISTRY: opencontrailnightly
      CONTRAIL_VERSION: latest
      CONTROLLER_NODES: 192.168.0.2
      CLOUD_ORCHESTRATOR: openstack
      AUTH_MODE: keystone
      KEYSTONE_AUTH_ADMIN_PASSWORD: admin
      KEYSTONE_AUTH_HOST: 192.168.0.3
      RABBITMQ_NODE_PORT: 5673
      PHYSICAL_INTERFACE: eth1
      VROUTER_GATEWAY: 192.168.0.1
    roles:
      10.100.0.2: # contrail node IP
        configdb:
        config_database:
        config:
        control:
        webui:
        analytics:
        analyticsdb:

**4. Run ansible playbook**

.. code-block:: console

    $ ansible-playbook -e '{"CREATE_CONTAINERS":true}' -i inventory/ playbooks/deploy.yml
