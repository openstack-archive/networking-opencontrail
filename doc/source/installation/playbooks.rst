=============================================
Setup development VMs using Ansible playbooks
=============================================

Variables used by configuration templates are stored in ``group_vars``
directory so be sure to adjust it according to your setup before running
any playbook. It uses also ``hosts`` for nodes definition so be sure to
reedit this as well.

Initial steps required by both VMs
----------------------------------

Make sure you have access via ssh to all nodes listed in ``playbooks/hosts``
file

Setup OpenContrail & Devstack VMs
---------------------------------

Run ``main.yml`` playbook (it could take few hours to finish)::

     ./main.yml


NOTICE
------

Use Ubuntu 14.04 and 16.04 for VMs. If you are installing Openstack Ocata
after succesfull deployment be sure to issue command listed below on OpenStack
node, otherwise scheduling VM using Nova won't work.

.. code-block:: bash

     nova-manage cell_v2 simple_cell_setup

