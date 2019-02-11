============
Contributing
============
.. include:: ../../CONTRIBUTING.rst

Development guide
-----------------
Useful resources:

* `Gerrit`_
* `Git`_

.. _Gerrit: https://review.openstack.org/#/q/project:openstack/networking-opencontrail
.. _Git: https://git.openstack.org/cgit/openstack/networking-opencontrail

Running unit tests (in project directory)::

    tox -e py36

Generating coverage reports::

    tox -e cover

Generating docs::

    tox -e docs

Setting up test environment
---------------------------
We have prepared ansible scripts for setup of test environment which you may find helpful.

Then follow the guide available in :doc:`installation/playbooks`
