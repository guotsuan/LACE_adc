#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright ÃÂÃÂ© 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
the parameters for recv.py
"""
import platform as pf
import netifaces
import os

# Neworking settings for reciever and data storage

###########################
#  Output 1 and Output 2  #
###########################

# the order of the lists is "RAW1, FFT1, RAW2, FFT2"

scale_fs = [0.5/2**15, 1.0, 0.5/2**15, 1.0]

src_ip = ["192.168.90.20", "192.168.90.21", "192.168.90.30", "192.168.90.31"]

src_port = [59000, 59001, 59000, 59001]


dst_port = [60000, 60001, 60000, 60001]

dst_ip = ["192.168.90.100", "192.168.90.100", "192.168.90.101", "192.168.90.101"]

platform_system = pf.system()
if 'Darwin' in platform_system:
    network_faces = ["en7", "en7", "en8", "en8"]
else:
    node_name = pf.node()
    if node_name == 'lacebian1':
        network_faces = ["enp10s0f0", "enp10s0f0","enp10s0f1", "enp10s0f1"]
        #network_faces = ["enp10s0", "enp10s0","enp10s0f1", "enp10s0f1"]
    elif node_name == "gqhp":
        network_faces = ["enp153s0f0", "enp153s0f0", "enp153s0f1", "enp153s0f1"]
    else:
       network_faces = ["enp119s0f0", "enp119s0f0","enp119s0f1", "enp119s0f1"]

dst_mac = [] 
for nic in network_faces:
    addrs = netifaces.ifaddresses(nic)
    dst_mac.append(addrs[netifaces.AF_LINK][0]['addr'])

#print("get MAC address for NICs:")
#print(dst_mac, "\n")

# mac address are no longer need to specify
# dst_mac

# do not change
labels = ["RAW_output1", "FFT_output1", "RAW_output2", "FFT_output2"]

raw1 = 0
fft1 = 1
raw2 = 2
fft2 = 3

# raw1, fft1, raw2, fft2
output_type = raw1


loop_file=False
output_fft = True
udp_raw = False
save_hdf5 = True

# the size of socket buffer for recieving data
# maximum is 1610612736
if 'Darwin' in platform_system:
    rx_buffer = 7168000
else:
    rx_buffer = 1610612736

# How many packets of data accumulated before saving
counts_to_save = 2048

# the rx program runing forever ? file_stop_num < 0 or it will stop at saved a
# few files
# run_forever = True
# file_stop_num = 50
file_stop_num = -1
save_lost = True
# default by hour
split_by_min = True 


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
