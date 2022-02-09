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
import os

# Neworking settings for reciever and data storage

###########################
#  Output 1 and Output 2  #
###########################

# array in the order "RAW1, FFT1, RAW2, FFT2"

src_ip = ["192.168.90.20", "192.168.90.21", "192.168.90.30", "192.168.90.31"]

src_port = [59000, 59001, 59000, 59001]

dst_mac_list =  ["6c:b3:11:07:93:18", "6c:b3:11:07:93:1a"] 

dst_mac = ["24:5e:be:68:55:6e", "24:5e:be:68:55:6e", \
           "24:5e:be:59:8d:46", "24:5e:be:59:8d:46"]
# TWIN 10G SFP+ Sonnet
dst_mac =  ["6c:b3:11:07:93:18", "6c:b3:11:07:93:18", \
            "6c:b3:11:07:93:1a", "6c:b3:11:07:93:1a"] 

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
    else:
       network_faces = ["enp119s0f0", "enp119s0f0","enp119s0f1", "enp119s0f1"]

labels = ["RAW output1", "FFT output1", "RAW output2", "FFT output2"]

raw1 = 0
fft1 = 1
raw2 = 2
fft2 = 3

# raw1, fft1, raw2, fft2
output_type = raw1

src_udp_ip = src_ip[output_type]
src_udp_port = src_port[output_type]

udp_ip = dst_ip[output_type]
udp_port = dst_port[output_type]

if output_type % 2 == 0:
    data_type = '>i2'
    fft_data = False
else:
    data_type = '>u4'
    fft_data = True

save_per_file = 1000
loop_file=True
output_fft = True
udp_raw = False
save_hdf5 = False

# the size of socket buffer for recieving data
# maximum is 1610612736
if 'Darwin' in platform_system:
    rx_buffer = 7168000
else:
    rx_buffer = 1073741824

# How many packets of data accumulated before saving
counts_to_save = 1024

# the rx program runing forever ?
forever = True

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
