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
from python_udp_recv.params import *
import platform as pf

########################
#  General parameters  #
########################

timeout = 1

###################
#  Output 1 and 2  #
###################

# import from params.py


def check_output():
    print("Current Platform: ", pf.platform(), " Node name: ", pf.node())
    print("Will checking: ", network_faces +"\n")


    for sip, sport, dip, dport, nic, dmac, lb in zip(src_ip, src_port, dst_ip,
            dst_port, network_faces, dst_mac, labels):

        print("Checking: ", bcolors.UNDERLINE + lb + bcolors.ENDC)
        if 'Darwin' in platform_system:
            # filter option does not working in mac M1
            p = sniff(count=1, iface=nic, timeout=timeout)
        else:
            p = sniff(count=1, iface=nic, filter="udp and host " + sip ,
                    timeout=timeout)
        if p:
            p.nsummary()
            ok = True
            p_dst_ip = p[0].sprintf("%-15s,IP.dst%")
            p_src_ip = p[0].sprintf("%-15s,IP.src%")
            p_dst_mac = p[0].sprintf("%-18s,Ether.dst%")
            p_proto = p[0].sprintf("%-8s,IP.proto%")

            if p_dst_ip.strip() != dip.strip():
                print("destination IP in the packet is different with the parameter")
                ok=False

            if p_src_ip.strip() != sip.strip():
                print("source IP in the packet is different with the parameter")
                print("In packet: ", p_src_ip, "In file: ", sip)
                ok=False

            if p_dst_mac.strip() != dmac.strip():
                print("destination MAC address in the packet is different with the parameter")
                ok=False

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


if __name__ == "__main__":
    check_output()

