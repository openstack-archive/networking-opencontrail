=============================================
Setup development VMs using Ansible playbooks
=============================================

Initial steps
-------------

Before you run playbooks perform the following steps:

#. Prepare machines for Contrail node and OpenStack node

#. Make sure you have key-based SSH access to prepared nodes::

    ssh contrail-node
    ssh openstack-node

#. Install Ansible::

    sudo apt install ansible

Configuring playbooks
---------------------

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
    contrail_branch: R4.0

    kernel_version: 3.13.0-77

Setup OpenContrail & Devstack VMs
---------------------------------

Run ``main.yml`` playbook (it could take few hours to finish)::

     playbooks/main.yml


NOTICE
------

Use Ubuntu 14.04 and 16.04 for VMs. If you are installing Openstack Ocata
after succesfull deployment be sure to issue command listed below on OpenStack
node, otherwise scheduling VM using Nova won't work.

.. code-block:: bash

     nova-manage cell_v2 simple_cell_setup

