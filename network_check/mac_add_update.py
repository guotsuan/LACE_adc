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

# mac for receiving output1 and output2
new_rec_mac = ["24:5e:be:59:8d:46", "24:5e:be:59:8d:47"]

update_ok = True
for i, new_mac in enumerate(new_rec_mac):

    # update dest_mac0
    mac_sendin = "0x" + new_mac.replace(":", "")[4:]
    cmd = "ssh rec \"sed -i '/\\s port" + str(i) \
        + "_dst_mac0/c\\    port0_dst_mac0=" + mac_sendin \
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

    # update dest_mac0
    mac_sendin = "0x" + new_mac.replace(":", "")[0:4]
    cmd = "ssh rec \"sed -i '/\\s port" + str(i) \
        + "_dst_mac0/c\\    port0_dst_mac0=" + mac_sendin \
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
    cmd = "ssh rec \" python zrf8_init.py\""
    errors= os.system(cmd)
    if errors:
        print("Restart Receiver failed....")
        print("Errors: ", errors)
    else:
        print("Restart Restart sucessfully....")

else:
    print("Update failed....please check and try again. Exited with failure...")
