#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
Checking the status of the outputing network of the receiver
"""

from scapy.all import sniff
import sys
sys.path.append('../')
from python_udp_recv.params import *

import platform as pf
import netifaces as nics
import numpy as np

########################
#  General parameters  #
########################

timeout = 1

###################
#  Output 1 and 2  #
###################

# import from params.py

need_to_update_mac = [False] * 4
need_to_update_dst_ips = [False] * 4

seqs = range(4)

def check_output():
    print("Current Platform: ", pf.platform(), " Node name: ", pf.node())
    print("Will checking: ", network_faces, "\n")


    nic_of_system = nics.interfaces()

    for nic in network_faces:
        if nic not in nic_of_system and nic != '':
            print("network face: " + nic + "is not in the system, please check again...")
            print("exited....")
            sys.exit()


    for i,sip, sport, dip, dport, nic, dmac, lb in zip(seqs, src_ip, src_port, dst_ip,
            dst_port, network_faces, dst_mac, labels):

        print("Checking: ", bcolors.UNDERLINE + lb + bcolors.ENDC)
        if nic == '':
            print("Ignore the " + lb  + bcolors.OKGREEN + " ok....." + bcolors.ENDC)
            print("\n")
        else:
            if 'Darwin' in platform_system:
                # filter option does not working in mac M1
                p = sniff(count=1, iface=nic, timeout=timeout)
            else:
                p = sniff(count=1, iface=nic, filter="udp ",
                        timeout=timeout)
            if p:
                p.nsummary()
                ok = True
                p_dst_ip = p[0].sprintf("%-15s,IP.dst%")
                p_src_ip = p[0].sprintf("%-15s,IP.src%")
                p_dst_mac = p[0].sprintf("%-18s,Ether.dst%")
                p_proto = p[0].sprintf("%-8s,IP.proto%")

                if p_dst_ip.strip() != dip.strip():
                    print("destination IP in the packet is different with the parameter ")
                    print("In packet: ", p_dst_ip, "In file: ", dip +"\n")
                    ok=False
                    need_to_update_dst_ips[i] = True

                if p_src_ip.strip() != sip.strip():
                    print("source IP in the packet is different with the parameter")
                    print("In packet: ", p_src_ip, "In file: ", sip +"\n")
                    ok=False

                if p_dst_mac.strip() != dmac.strip():
                    print("destination MAC address in the packet is different with the parameter")
                    print("Run mac_addr_update.py for you to update the mac registered in the Receiver")
                    ok=False
                    need_to_update_mac[i] = True

                if p_proto.strip() != 'udp':
                    print("Protcol in the packet is not udp")
                    print("In packet: ", p_proto)
                    ok=False

                if ok:
                    print (lb + " seems " + bcolors.OKGREEN + "ok....." + bcolors.ENDC)
                else:
                    print (lb + bcolors.FAIL + " seems failed....." + bcolors.ENDC)

                print("\n")

            else:
                print("Connection to the RAW Output1 is broken....\n")

    return need_to_update_mac, need_to_update_dst_ips

def check_and_update():
    need_to_update_mac, need_to_update_dst_ips=check_output()

    seqs = range(4)
    status = []

    for i, m, p, dip, dmac in zip(seqs, need_to_update_mac, need_to_update_dst_ips,
            dst_ip, dst_mac):
        if m:
            # print("udpate mac port", i)
            status.append(update_mac_addr(dmac, i))
        if p:
            print("udpate dst_ip", i)
            status.append(update_dst_ip(dip, i))

    if len(status) != 0:
        if np.all(status):
            print("restart and check again!")
            restart_recv()
            check_output()
        else:
            print("mac or IP address update failed... Receiver will not reboot")

if __name__ == "__main__":
    from mac_add_update import update_mac_addr, update_dst_ip, restart_recv
    check_and_update()

else:

    from network_check.mac_add_update import update_mac_addr, update_dst_ip, restart_recv

