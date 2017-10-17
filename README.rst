======================================================
XON Juniper Installation Base (JIB) Maintenance script
======================================================

Overview
========
This tool is used by XON Systems and its customers
to keep an up-to-date inventory of its
Juniper customer install base. Add the maintenance script to a
periodic cron job in order to automatically keep an updated inventory.

Components
==========
These are some of the main scripts used in this tool.

*XONJunosIBmaint.py* - the main JIB maintenance script. It:
* logs into Juniper devices
* grabs the output of "show chassis hardware"
* saves the results locally, and
* submits it to XON systems via secure API.

*conf/XONJunosIBmaint.conf* - the main options file. Here you specify things such as:
* Login method
* API username/password
* inventory file location
* Device login credentials (if required)

*conf/logging.conf* - Options file for logging.

*setup.py* - Installation script. Running this script will prompt
a series of questions, and the answers will be used to automatically
populate the *conf/XONJunosIBmaint.conf* file. Also checks if required
dependancies are installed.

*router.db* file - a file in the `RANCID router.db <http://www.shrubbery.net/rancid/man/router.db.5.html>`_
format used as the source of IP addresses to log into.

*XONdeviceDiscover.py* - A script that can populate the *router.db* file based
on Junipers discovered in an IP address range via SNMPv2.

Dependencies
============
This script requires Python to be installed. Most modern Linux distributions
come with Python already installed.

It also requires the python module *tachyonic_client*, which is the REST client
used to make the API calls to the XON Inventory system. Install with:

.. code:: bash

    $ git clone https://github.com/TachyonicProject/tachyonic_client.git

Once you have cloned the repo or downloaded a tarball from GitHub, you
can install tachyonic_client like this:

.. code:: bash

    $ cd tachyonic_client
    $ pip install .

Next, you require API login details from XON systems. To obtain this, email support at xon.co.za.

If you would like to auto-create the router.db file with the *XONdeviceDiscover.py*, you need it's dependancies:

.. code:: bash

    $ sudo apt-get install libsnmp-dev
    $ sudo pip install easysnmp
    $ sudo pip install pyipcalc

Installation
============

Clone from github:

.. code:: bash

    $ git clone https://github.com/XON-systems/xibt.git

Then ``cd`` into the XONjib directory and either run ``./setup.py``, or manually
update ``conf/XONJunosIBmaint.conf`` with the appropriate values.


Options
=======

The XON Junos Installation Base maintenance script will log into network devices
using SSH in order to gather inventory information.
It can do this in one of two ways:
# Use jlogin that comes with the `RANCID <http://www.shrubbery.net/rancid`_ installation
# SSH into the device directly from the local machine

jlogin is required when connecting via a jumphost, then one can make use of the
SSH config file for port forwarding.

Use jlogin if there is already a RANCID installation on the same machine,
or if you require jumphost functionality
Use *SSH directly* option if you can't install RANCID or do not require
jumphost functionality

The options in the ``conf/XONJunosIBmaint.conf`` file for ``login_method`` are correspondingly:

* jlogin
  or
* paramiko

Usage
=====

Auto create router.db file
--------------------------

To generate the router.db file automatically, run the ``XONdeviceDiscover.py`` script:

.. code:: bash

    $./XONdeviceDiscover.py <ip|subnet/prefix> snmp-community router.db-file-location

    where:

    - <ip|subnet/prefix>: The first argument can either be a single IP adress, or a subnet)
    - snmp-community: SNMP v2 community string
    - router.db-file-location: the location of the output router.db file

Auto populate configuration file
--------------------------------
To Answer questions regarding your installation, and have the configuration file auto-populated
based on your answers, run ``./setup.py`` with no arguments:

.. code::bash

    $ ./setup.py
    In order to make use of the XON Juniper Install Base
    script, you require API login details from XON Systems
    If you do not have these already, please email
    support@xon.co.za in order to obtain it.
    API login username: obtainThisFromXON
    API login password: obtainThisFromXON
    API login domain id: obtainThisFromXON

    The XON Junos Installation Base maintenance script will log into
    network devices in order to gather inventory information.
    It can do this in one of two ways:
    1. Use jlogin that comes with the RANCID installation
    2. SSH into the device directly from this machine

    Note: jlogin is required when connecting via a jumphost

    Which option do you prefer?
    1. Use jlogin - I have RANCID installed on this machine
    2. SSH directly - I have have no use for a jumphost
    Please select: 1 or 2: 1

    You now have the opportunity to supply one
    or more 'groups' of devices. Each group will
    have its own RANCID-like router.db file
    (You may even use existing RANCID router.db files)
    What is the name of your first group? Junipers
    What is the location for this group's router.db file?
    (Default is ./conf/router.db)
    (will be created if it does not exist)
    router.db file location for Junipers: ./conf/router.db
    Would you like to add more groups? [y/N]:N

Run the script manually to see if it works
------------------------------------------

Simply run the script with no command line arguments:

.. code:: bash

    $ ./XONJunosIBmaint.py
    $

You should see a new directory called ``output``. In it, will be one directory for each
group configured in the config file. Inside those directorries, should be XML files for
each of the devices in the router.db file.

Also check the file ``output/output.log`` for any errors or notifications.

Cron the script to be run periodically
--------------------------------------
The optimal frequency of course depends on the rate at which you deploy new hardware.
For most people once per month is good enough.

.. code:: bash

    $ crontab -e


.. code:: bash

    0 0 0 * * /path/to/XONdirectFetcher.py