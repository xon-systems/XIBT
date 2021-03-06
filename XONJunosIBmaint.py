#!/usr/bin/env python3
#
# XON Junos Installation Base maintenance script.
#
# Run this script to fetch device info and
# upload to XON's Inventory manager.
#
# Options are parsed from the configuration file
# called XONJunosIBmaint.conf in the conf directory
#
# Usage:
# After modifying configuration file with
# appropriate values, simply run the script with no arguments
#
# ./XONJunosIBmaint.py
#
# Supports only Junos for the moment

import json
import logging
import logging.config
import os
import re
import glob
from subprocess import check_output, CalledProcessError, STDOUT
from collections import OrderedDict
from datetime import datetime


# The output directory needs to exist,
# this is where we are saving the results
if not os.path.exists("output"):
    os.makedirs("output")


def loadInputFile():
    """
    Read the general settings information
    :return: Dictionary with settings
    """
    try:
        with open('conf/XONJunosIBmaint.conf') as data_file:
            settings = json.load(data_file)
    except:
        msg = ("Loading and Verifying Device List: "
               "Unable to read input or parse file "
               "'XONJunosIBmaint.conf' responsible "
               "for specifying projects and their "
               "router.db locations")
        logging.error(msg)
        return {}

    return settings


def loadHosts(file_loc):
    """
    Read the host IP's from the router.db file

    :param file_loc: The location of the router.db file
    :return: list of all the IP addresses to query
    """
    ips = []
    try:
        with open(file_loc) as routerdb:
            for line in routerdb.readlines():
                ip = re.match('((\d{1,3}\.){3}\d{1,3}):juniper:up', line)
                if ip:
                    ips.append(ip.group(1))
    except:
        msg = ("Loading and Verifying Device List: "
               "Unable to read input or parse file "
               "'%s', the rancid router.db format "
               "file for this project" % (file_loc,))
        logging.error(msg)
        return []

    return ips


class FetchOutput:
    """
    Class to log into device with given method and
    grab and return output
    """

    def __init__(self, loginMethod, username=None, password=None):
        self.method = loginMethod
        self.username = username
        self.password = password

    def run(self, ip):
        filename = ip
        hostname = ""
        complete_output = ""
        if self.method == "jlogin":
            try:
                output = check_output(
                    ['jlogin', '-x',
                     'commands',
                     ip
                    ],
                    stderr=STDOUT)

                incmd = False
                got_output = False

                filename_search = re.search('@([^>]+)> show', output.decode())
                if not hostname and filename_search:
                    filename = hostname = filename_search.group(1)

                for line in output.decode().split('\n'):
                    cmd_start = re.search('%s> (show|request)' % (hostname,), line)
                    if cmd_start:
                        incmd = True
                        got_output = True
                    elif re.search('%s>' % (hostname,), line):
                        incmd = False
                    if incmd:
                        complete_output += line + '\n'

                if not got_output:
                    logging.error("Did not receive XML response from %s" % (ip,))
                    logging.error('Output was "%s"' % (output,))
                    return (filename, '')
                else:
                    return (filename, complete_output)
            except (OSError, CalledProcessError) as e:
                if hasattr(e, 'output'):
                    logging.error('jlogin returned with error code %s: "%s"' % (e.returncode, e.output))
                else:
                    logging.error('jlogin returned with error code %s: "%s"' % (e.args[0], e.args[1]))
                return (filename, '')
        elif self.method == "paramiko":
            try:
                ssh = paramiko.SSHClient()
                ssh.load_system_host_keys()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # First issuing 'show version' in order to obtain the
                # hostname so that we can use that as the file name
                ssh.connect(ip, port=22, username=self.username,
                            password=self.password, timeout=10)
                ssh_stdin, version, ssh_stderr = ssh.exec_command('show version')
                version = version.read().decode()
                hostname = ip
                try:
                    filename = re.search('Hostname: (.*)\n', version).group(1)
                    hostname = filename
                except:
                    pass
                # Finally executing commands
                with open("commands") as f:
                    commands = f.readlines()
                for c in commands:
                    ssh_stdin, out, ssh_stderr = ssh.exec_command(c)
                    complete_output += "user@" + hostname + "> " + c
                    complete_output += out.read().decode()
                    complete_output += '\n\n\n'
                ssh.close()
                return (filename, complete_output)
            except Exception as err:
                logging.error("Error parsing command output [%s]:%s" % (ip, err))
                return ('', '')
        else:
            logging.error("Invalid Login method in config file: %s"
                          % (self.method,))
            return ''


def goGetThem(p, ips):
    """
    The Function to connect to the network devices
    in order to
        capture the output of the commands in the file
        "commands"
        save it locally, and
        push it to XON API

    :param p: RANCID Project/group Name
    :param ips: List of IP addresses in this group
    """
    for ip in ips:
        logging.info("Connecting to: " + ip)
        filename, xml = fo.run(ip)
        if xml:
            with open("output/%s/%s.xml" % (p, filename), 'w') as f:
                f.write(xml)
            if 'auth' in globals():
                r = api.execute('POST','/some/path',data={'xml': xml},
                                                endpoint='someEndpoint')
                logging.info("I got back %s" % r.json)


# Main Program
if __name__ == '__main__':
    logging.config.fileConfig('conf/logging.conf')
    options = loadInputFile()
    loginMethod = options['login_method']
    if loginMethod == "paramiko":
        import paramiko

        fo = FetchOutput('paramiko',
                         username=options['ssh_username'],
                         password=options['ssh_password'])
    else:
        fo = FetchOutput(loginMethod)

    for p in options['groups']:
        logging.info("Starting with: %s" % (p,))
        if not os.path.exists("output/%s" % (p,)):
            os.makedirs("output/%s" % (p,))
        ips = loadHosts(options['groups'][p])
        goGetThem(p, ips)

    combined_fn = 'install_base_' + datetime.now().strftime("%Y_%m_%d")
    combined_fn += '.txt'

    for filename in glob.iglob('./output/**/*.xml', recursive=True):
        with open(filename) as f:
            hostname = os.path.basename(filename)
            with open('output/'+combined_fn, 'a') as c:
                c.write(f.read())
                c.write('\n')
