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
import pyipcalc
import sys
import re

junos_routers = []


def discover():
    """
    Function that discovers the devices in the subnet
    by doing SNMP get on the system description OID.

    Takes no arguments, subnet obtained from system argument
    """
    subnet = sys.argv[1]
    # If IPv4 and no mask, we assume host
    if '.' in subnet and '/' not in subnet:
        subnet += '/32'
    # If IPv6 and no mask, we assume host
    elif ':' in subnet and '/' not in subnet:
        subnet += '/128'
    # Rudementary check for Valid IP - has to at least have . or :
    elif ':' not in subnet and '.' not in subnet:
        raise Exception('Ivalid IP', subnet)
    subnet = pyipcalc.IPNetwork(subnet)
    # Running through al the hosts in the subnet
    for ip in subnet:
        session = Session(hostname=ip.first(), community=sys.argv[2], version=2)
        try:
            sysdescription = session.get('1.3.6.1.2.1.1.1.0')
            if re.search('JUNOS ([^ ]+)', sysdescription.value):
                junos_routers.append(ip.first())
            else:
                print('Skipping', ip.first(), ':', "Not Junos")
        except Exception as e:
            print('Skipping', ip.first(), ':', str(e))
    if junos_routers:
        f = open(sys.argv[3], 'w')
        for r in junos_routers:
            f.write(r + ':juniper:up\n')
        f.close()

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
        ans = input("Warning, this will overwrite the current %s file. Proceed? (y/N):" % (sys.argv[3],))
        if ans.lower() == 'y':
            discover()
