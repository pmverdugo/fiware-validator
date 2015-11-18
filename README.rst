
FI-Ware Validator
======================

An OpenStack validator for testing deployment artifacts implemented as
a service with an OpenStack-native Rest API

Getting Started
---------------

To run the code you can clone the git repo with:

::

    git clone git@github.com:ging/fi-ware-validator.git

Installing Dependencies
-----------------------

To install package dependencies you must run:

::

    pip install -r requirements.txt

API Definition
--------------

The API definition can be found at http://docs.chefvalidatorapi.apiary.io/#

External Dependencies
---------------------

The system deployment depends on several external services for successful completion.
The dependency list reads as follows:

- OpenStack Keystone server:
    Used for issuing user tokens for several OpenStack services
- Docker daemon:
    Used to deploy the test images

License
-------

Apache License Version 2.0 http://www.apache.org/licenses/LICENSE-2.0
