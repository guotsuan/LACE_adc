#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
Checking the whole system requirment
"""

import subprocess
import shlex
import getpass

from subprocess import Popen

from python_udp_recv.params import bcolors
from gps_and_oscillator.check_status import check_gps
from network_check.network_check import check_output

green_ok = bcolors.OKGREEN + " .....OK." + bcolors.ENDC
red_failed = bcolors.FAIL + " .....FAILED." + bcolors.ENDC

# Check the GPS and oscillator
check_gps()

# Check and correct kernel parameters
#
# rmem_max = 1610612736
# wmem_max = 1610612736
# netdev_max_backlog=65536

kp_set = True

kernels_params = ['rmem_max', 'wmem_max', 'netdev_max_backlog',
                  'optmem_max']
kernels_presults = ['1610612736', '1610612736', '300000', '1020000']

# special setting for net.ipv4.udp_mem

udp_mem= '"11416320 15221760 22832640"'
out = Popen("sudo sysctl -w net.ipv4.udp_mem"  + "=" + udp_mem, shell=True,
                    stdout=subprocess.PIPE)
print(out.stdout.read().strip().decode() + "   " + green_ok)

for kp, v in zip(kernels_params, kernels_presults):
    out = Popen("sysctl net.core." + kp, shell=True, stdout=subprocess.PIPE)
    result = out.stdout.read().strip().decode()
    result_s = result.split()
    if len(result_s) == 3:
        if result_s[2] == v:
            print(result + "   " + green_ok)
        else:
            print(result + "   " + red_failed)
            print("Correcting....")
            out = Popen("sudo sysctl -w net.core." + kp + "=" + v, shell=True,
                    stdout=subprocess.PIPE)

            print(out.stdout.read().strip().decode() + "   " + green_ok)



# Checking The Receiver output....
subprocess.call(shlex.split('sudo id -nu'))
print ("Checinkg output....\n")
check_output()

