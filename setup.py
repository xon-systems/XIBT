#!/usr/bin/env python3
#
# Setup script for XON Junos Installation Base maintenance script.
#
# Run this script to prompt questions
# and auto configure the conf file for
# the XIBT maintenance script

import json
import os
import sys
from collections import OrderedDict

# We don't know if system is using Python 2 or 3, so
try:
    input = raw_input
except NameError:
    pass

def gatherInfo():
    """
    Gathers information that is required in config file
    from the user.
    Such as:
       Ask user which SSH option they are opting for.
         jlogin uses .cloginrc file to obtain user login creds,
         but netmiko requires user to provde login details.
       Asks for router.db location

    :return: Dictionary with answers.
    """
    options = {}
    ans = ''
    print("The XON Junos Installation Base maintenance script will log into")
    print("network devices in order to gather inventory information.")
    print("It can do this in one of two ways:")
    print("1. Use jlogin that comes with the RANCID installation")
    print("2. SSH into the device directly from this machine\n")
    print("Note: jlogin is required when connecting via a jumphost\n")
    print("Which option do you prefer?")
    print("1. Use jlogin - I have RANCID installed on this machine")
    print("2. SSH directly - I have have no use for a jumphost")
    while ans != '1' and ans != '2':
        ans = input("Please select: 1 or 2: ")
        if ans != '1' and ans != '2':
            print("Please make a valid selection")
            print("Either type '1' or '2'")
    options['method'] = ans
    if ans == '2':
        print("In this case we need the ssh username and password.")
        print("This will be stored in ./conf/XONJunosIBmaint.conf,")
        print("so make sure that file is readable only by you.")
        creds = []
        creds.append(input("SSH login username: "))
        creds.append(input("SSH login password: "))
        options['creds'] = creds
    print('')
    options['groups'] = {}
    print("You now have the oppertunity to supply one")
    print("or more 'groups' of devices. Each group will")
    print("have its own RANCID-like router.db file")
    print("(You may even use existing RANCID router.db files)")
    group = input("What is the name of your first group? ")
    if group == '':
        group = "Junipers"
    print("What is the location for this group's router.db file?")
    print("(Default is ./conf/router.db)")
    print("(will be created if it does not exist)")
    options['groups'][group] = input(
        "router.db file location for %s: " % (group,))
    if options['groups'][group] == '':
        options['groups'][group] = os.getcwd() + '/conf/router.db'
    ans = input("Would you like to add more groups? [y/N]: ")
    if ans.lower() == 'y':
        print("To finish, just press Enter on group name")
        while group != '':
            group = input("Name of the next group: ")
            if group:
                options['groups'][group] = input(
                    "router.db file location for %s: " % (group,))
    return options

def verifyOption(option):
    """
    If jlogin was chosen, we will make sure we
    can find it
    :param option: '1' for jlogin, '2' for paramiko
    :return: True if we found jlogin or using paramiko
    """
    if option == '1':
        haveJlogin = False
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            jlogin_loc = os.path.join(path, "jlogin")
            if os.path.isfile(jlogin_loc) and os.access(jlogin_loc, os.X_OK):
                haveJlogin = True
                break
        if haveJlogin:
            return True
        else:
            return False
    else:
        try:
            import paramiko
        except ModuleNotFoundError:
            print("You have selected to ssh direct,"
                  " but don't have paramiko installed")
            print("Attempting to install it now")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", 'paramiko'])

        return True

def updateConfFile(options):
    """
    Updating the config file with the selected options
    :param options: The options dict

    """

    # Grab existing config first
    with open('conf/XONJunosIBmaint.conf') as f:
        conf = json.load(f, object_pairs_hook=OrderedDict)

    # Next add what we got
    if options['method'] == '1':
        conf['login_method'] = 'jlogin'
    else:
        conf['login_method'] = 'paramiko'
    if 'groups' not in conf:
        conf['groups'] = {}
    for group in options['groups']:
        conf['groups'][group] = options['groups'][group]
    if 'creds' in options:
        conf['ssh_username'] = options['creds'][0]
        conf['ssh_password'] = options['creds'][1]

    # Remove default conf if unwanted
    if 'Junipers' in conf['groups'] and 'Junipers' not in options['groups']:
        print("\nIt looks like you did not create a group called Junipers")
        print("There is one by default in the config file,")
        print("just as an example, pointing to %s" %  conf['groups']['Junipers'])
        ans = 'dummy'
        while ans != 'k' and ans != 'd' and ans != '':
            ans = input("(k)eep or (d)elete it? (k/D): ").lower()
            if ans != 'k' and ans != 'd' and ans != '':
                print("Please make a valid selection")

        if ans != 'k':
            del conf['groups']['Junipers']

    # Finally write it to the file
    with open('conf/XONJunosIBmaint.conf','w') as f:
        json.dump(conf, f, indent=4)

if __name__ == '__main__':
    options = gatherInfo()
    choice = options['method']
    goAhead = verifyOption(choice)
    # If we have chosen jlogin, and it was found,
    # or we are using paramiko, we can update the config file
    if goAhead:
        updateConfFile(options)
    else:
        print("Sorry, we did not find jlogin in your PATH")
        print("Please make sure that RANCID is installed, and")
        print("this user has jlogin executable in the PATH")
        print("We are leaving your conf/XONJunosIBmaint.conf unchanged")
