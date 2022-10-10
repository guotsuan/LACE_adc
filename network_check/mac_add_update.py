#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
Try to update the destination mac address remotely

"""

import os
import sys
sys.path.append('../')
from recv_python.params import dst_mac

# mac for receiving output1 and output2
new_rec_mac = dst_mac

ssh_cmd = "sshpass -p root ssh  -oHostKeyAlgorithms\=\+ssh-rsa root\@192.168.1.188"

def restart_recv():
    print("Restat Receiver, pleaset wait for a few secs.......")
    cmd = ssh_cmd + " \" python zrf8_init.py\""
    errors= os.system(cmd)
    if errors:
        print("Restart Receiver failed....")
        print("Errors: ", errors)
    else:
        print("Restart Restart sucessfully....")


def update_mac_addr(new_mac, pn):
    # pn is 0 , 1, 2, 3

    i = pn

    mac_sendin = "0x" + new_mac.replace(":", "")[4:]
    cmd = ssh_cmd + " \"sed -i '/\\s port" + str(i) \
        + "_dst_mac0/c\\    port" + str(i) + "_dst_mac0=" + mac_sendin \
                + "' py2drv.py\""


    errors= os.system(cmd)
    if errors:
        print("Updating Mac Address: " + new_rec_mac[0] + " part1: " +
                mac_sendin + " failed\n")
        print("Errors: ", errors)
        update_ok = False
    else:
        print(new_rec_mac[0] + " part1: " + mac_sendin +
                " was sucessfully Updated\n")

    # update dest_mac1, mac part1
    mac_sendin = "0x" + new_mac.replace(":", "")[0:4]
    cmd = ssh_cmd + " \"sed -i '/\\s port" + str(i) \
        + "_dst_mac1/c\\    port" + str(i) + "_dst_mac1=" + mac_sendin \
                + "' py2drv.py\""
    errors= os.system(cmd)

    if errors:
        print("Updating Mac Address part2 : " + new_rec_mac[0] +  " part1: " +
               mac_sendin +  " failed\n")
        print("Errors: ", errors)
        return False
    else:
        print(new_rec_mac[0] + " part2: " + mac_sendin +
                " was sucessfully Updated\n")

        return True

def update_dst_ip(new_dst_ip, pn):
    # pn is 0 , 1, 2, 3

    i = pn
    dst_ip_sendin = '0x'
    for x in new_dst_ip.split("."):
        dst_ip_sendin += hex(int(x))[2:].upper()

    cmd = ssh_cmd +  " \"sed -i '/\\s port" + str(i) \
        + "_dst_ip/c\\    port" + str(i) + "_dst_ip=" + dst_ip_sendin \
                + "' py2drv.py\""

    errors= os.system(cmd)
    if errors:
        print("Updating Destination IP Address: " + new_dst_ip + " failed\n")
        print("Errors: ", errors)
        return False
    else:
        print("New destination ip: " + new_dst_ip + " :" + dst_ip_sendin +
                " was sucessfully Updated\n")
        return True

def update_all_macs():
    update_ok = True
    for i, new_mac in enumerate(new_rec_mac):

        # update dest_mac0, mac port0
        mac_sendin = "0x" + new_mac.replace(":", "")[4:]
        cmd = ssh_cmd + " \"sed -i '/\\s port" + str(i) \
            + "_dst_mac0/c\\    port" + str(i) + "_dst_mac0=" + mac_sendin \
                    + "' py2drv.py\""


        errors= os.system(cmd)
        if errors:
            print("Updating Mac Address: " + new_rec_mac[0] + " part1: " +
                    mac_sendin + " failed\n")
            print("Errors: ", errors)
            update_ok = False
        else:
            print(new_rec_mac[0] + " part1: " + mac_sendin +
                    " was sucessfully Updated\n")

        # update dest_mac1, mac part1
        mac_sendin = "0x" + new_mac.replace(":", "")[0:4]
        cmd = ssh_cmd + " \"sed -i '/\\s port" + str(i) \
            + "_dst_mac1/c\\    port" + str(i) + "_dst_mac1=" + mac_sendin \
                    + "' py2drv.py\""
        errors= os.system(cmd)

        if errors:
            print("Updating Mac Address part2 : " + new_rec_mac[0] +  " part1: " +
                   mac_sendin +  " failed\n")
            print("Errors: ", errors)
            update_ok = False
        else:
            print(new_rec_mac[0] + " part2: " + mac_sendin +
                    " was sucessfully Updated\n")

    if update_ok:
        print("Restat Receiver, pleaset wait for a few secs.......")
        cmd = ssh_cmd + " \" python zrf8_init.py\""
        errors= os.system(cmd)
        if errors:
            print("Restart Receiver failed....")
            print("Errors: ", errors)
        else:
            print("Restart Restart sucessfully....")

    else:
        print("Update failed....please check and try again. Exited with failure...")

if __name__ == "__main__":
    print("How can I help you")
    update_all_macs()
    #update_dst_ip("192.168.90.100", 0)
