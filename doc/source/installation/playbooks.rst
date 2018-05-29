=====================
Setup development VMs
=====================

Playbooks are designed to setup two nodes. The first node
contains Openstack with, among others, keystone, neutron
and neutron-opencontrail plugin as ML2 L3 driver.
Second node contains nightly-build contrail node.

Step by step instruction is presented below.


*************
Initial steps
*************

Before you run playbooks perform the following steps:

**1. Prepare machines for Contrail and OpenStack nodes.**

Let's assume there are two hosts:

+-----------+--------------+--------------------------+------------+-------------+------------------------------------+
| Node      | OS           | Recommended requirements | Public IP  | Internal IP | Notes                              |
+===========+==============+==========================+============+=============+====================================+
| openstack | Ubuntu 16.04 | RAM: 8 GB                | 10.100.0.3 | 192.168.0.3 | devstack (controller node)         |
+-----------+--------------+--------------------------+------------+-------------+------------------------------------+
| contrail  | CentOS 7.4   | RAM: 16 GB               | 10.100.0.2 | 192.168.0.2 | devstack (compute node) + contrail |
+-----------+--------------+--------------------------+------------+-------------+------------------------------------+

**2. Make sure you have key-based SSH access to prepared nodes**

.. code-block:: console

    $ ssh 10.100.0.2
    $ ssh 10.100.0.3

**3. Install Ansible on your host**

It is required to install Ansible in version 2.5 or higher.

.. code-block:: console

    $ sudo add-apt-repository ppa:ansible/ansible
    $ sudo apt update
    $ sudo apt install python-netaddr ansible


*******************
Configure playbooks
*******************

Configuration require editing few files before running any playbook.

**1. Define nodes by specifying SSH names or IP of machines in ``playbooks/hosts``**

Change ``contrail-node`` and ``openstack-node`` to public IP of your machines.

.. code-block:: text

    [contrail]
    10.100.0.2

    [openstack]
    10.100.0.3

**2. Change deployment variables in ``playbooks/group_vars/all.yml``**

``contrail_ip`` and ``openstack_ip`` should be internal IP addresses.
``contrail_gateway`` should be gateway address of the contrail_ip.
``contrail_interface`` should be interface name that has bound contrail ip.

``openstack_branch`` should be set to ``stable/ocata``

.. code-block:: yaml

    # IP address for OpenConrail.
    contrail_ip: 192.168.0.2

    # Gateway address for OpenConrail.
    contrail_gateway: 192.168.0.1

    # Interface name for OpenConrail.
    contrail_interface: eth0


    # IP address for Openstack VM.
    openstack_ip: 192.168.0.3

    # Openstack branch used on VMs.
    openstack_branch: stable/ocata

**********
Deployment
**********

Run playbooks
=============

.. note:: Before openstack deployment make sure Playbooks are configured.

Execute ``playbooks/main.yml`` file.
Make sure you are in playbooks directory before executing playbook.
This will make Ansible to use local ``hosts`` file instead of system broad defined hosts.

.. code-block:: console

    $ cd playbooks
    $ ./main.yml

This playbooks can last 1 hour or more.

Please be patient while executing roles with ``stack.sh``. Real time logs from these operations can be viewed on each host by following command:
``less -R /opt/stack/logs/stack.sh.log``

*****
Usage
*****

Access web interface
====================

http://10.100.0.3/ - devstack's horizon
https://10.100.0.2:8143/ - OpenContrail UI

Create example VM
=================

After successful deployment, it could be possible to create sample Virtual Machine.
It is important to create new security group, because the default is not synchronized correctly between contrail and devstack.

These commands should be ran on one of the nodes (both are connected to one neutron):

.. code-block:: console

    source ~/devstack/openrc admin demo
    openstack network create --provider-network-type vlan --provider-segment 3 --provider-physical-network vhost net
    openstack security group create --project demo secgroup
    openstack security group rule create --ingress --protocol icmp secgroup
    openstack security group rule create --ingress --protocol tcp secgroup
    openstack subnet create --network net --subnet-range 192.168.1.0/24 --dhcp subnet
    openstack server create  --flavor cirros256 --image cirros-0.3.4-x86_64-uec --nic net-id=net --security-group secgroup instance

Created VM could be accessed by VNC (through horizon):

1. Go to horizon's list of VMs
  http://10.100.0.3/dashboard/project/instances/
2. Enter into the VM's console

If you are using public IP that is different from internal IP (as in the example), you should do additional steps:
2a. Open console in new window by clicking on link "Click here to show only console"
2b. Console will open using wrong IP. Change IP from 192.168.0.3 to 10.100.0.3.

3. You will see black console. Press enter to attach. Default login/password is ``cirros/cubswin:)``
