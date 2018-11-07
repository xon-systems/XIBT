#!/usr/bin/env python3
#
# XON Device discover script.
#
# Run this script to discover Routers, and build a Rancid router.db
# file with the results.
#
# Usage:
#
# ./XONdeviceDiscover.py <ip|subnet/prefix> snmp-community router.db-file-location
#
# where:
#
# - <ip|subnet/prefix>: The first argument can either be a single IP adress, or a subnet)
# - snmp-community: SNMP v2 community string
# - router.db-file-location: the location of the output router.db file
#
# Supports only Junos for the moment

from __future__ import absolute_import, division, print_function
from builtins import *
from easysnmp import Session
import logging
import logging.config
import os.path
import pyipcalc
import sys
import re

# The output directory needs to exist
# this is where we are saving the log
if not os.path.exists("output"):
    os.makedirs("output")

next_ip = None
file_open = "a"


def getOptions():
    """
    Function to get some options from user

    """
    global file_open
    global next_ip
    global subnet
    ans1 = "x"
    ans2 = "x"
    print("Warning, the %s file exists already." % (sys.argv[3],))
    while ans1 != 'a' and ans1 != 'o' and ans1 != '':
        ans1 = input((" (o)verwrite or (a)ppend?\n(If you choose "
                      "append you have the option to choose wether"
                      " to continue where a previous scan left off)\n"
                      "Type o or a: (a) : ")).lower()
    if ans1 == 'a' or ans1 == '':
        while ans2 != 'y' and ans2 != 'n' and ans2 != '':
            ans2 = input(("Do you want to continue from"
                          " the last IP in the file?\n"
                          "(y)es or (n)o: (n): ")).lower()
        if ans2 == "y":
            next_ip = nextIP()
            if next_ip not in subnet:
                raise Exception(('The last ip is not '
                                 'in the current subnet'),
                                next_ip, subnet)
    else:
        file_open = 'w'

    try:
        f = open(sys.argv[3], file_open)
        f.close()
    except Exception as e:
        logging.error("Could not open file %s: %s" % (sys.argv[3], str(e)))
        sys.exit(0)


def nextIP():
    """
    Function to find the last detected IP
    From a previous scan so that the scan may
    Continue where it left off.
    :return: Last found IP as IPNetwork object, or None
    """

    with open(sys.argv[3]) as f:
        lines = f.readlines()
    last = re.match('(.*):juniper:up', lines[-1])
    if last and pyipcalc.validate_ip(last.group(1)):
        int_ip = pyipcalc.ip_to_int(last.group(1))
        next_ip = pyipcalc.int_to_ip(int_ip + 1)
        return pyipcalc.IPNetwork(next_ip)
    else:
        return None


def discover(subnet):
    """
    Function that discovers the devices in the subnet
    by doing SNMP get on the system description OID.
    Subnet obtained from system argument

    :param subnet: IPNetwork object
    :return: None

    """
    global file_open
    global next_ip

    # Fixing subnet if we need to continue
    # from a previous scan
    if next_ip:
        subnet = subnet[next_ip:]

    # Running through al the hosts in the subnet
    for ip in subnet:
        session = Session(hostname=ip.first(), community=sys.argv[2],
                          version=2, retries=1)
        try:
            sysdescription = session.get('1.3.6.1.2.1.1.1.0')
            if re.search('JUNOS ([^ ]+)', sysdescription.value):
                logging.info("Found Juniper at %s" % (ip.first(),))
                with open(sys.argv[3], 'a') as f:
                    f.write(ip.first() + ':juniper:up\n')
            else:
                logging.info("Skipping %s: Not Junos" % (ip.first(),))
        except Exception as e:
            logging.info('Skipping: %s: %s' % (ip.first(), str(e)))


# Main progaram
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('''XON Device discover script.

    Run this script to discover Routers, and build a Rancid router.db
    file with the results.

    Usage:

    ./XONdeviceDiscover.py <ip|subnet/prefix> snmp-community router.db-file-location

    where:

    - <ip|subnet/prefix>: The first argument can either be a single IP adress, or a subnet)
    - snmp-community: SNMP v2 community string
    - router.db-file-location: the location of the output router.db file
    ''')
    else:
        logging.config.fileConfig('conf/logging.conf')
        subnet = sys.argv[1]
        try:
            subnet = pyipcalc.IPNetwork(subnet)
        except:
            raise Exception('Ivalid IP', subnet)
        # Checking if the file already exists
        # If so we'll give option to overwrite or append
        # In case of Append can contine where we left off
        if os.path.isfile(sys.argv[3]):
            getOptions()

        discover(subnet)
