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
import sys

# Neworking settings for reciever and data storage

###########################
#  Output 1 and Output 2  #
###########################

# the order of the lists is "RAW1, FFT1, RAW2, FFT2"

# do not change
# raw1, fft1, raw2, fft2
labels = ["RAW_output1", "FFT_output1", "RAW_output2", "FFT_output2"]
src_ip = ["192.168.90.20", "192.168.90.21", "192.168.90.30", "192.168.90.31"]
src_port = [59000, 59001, 59000, 59001]
dst_port = [60000, 60001, 60000, 60001]
dst_mac = []
dst_ip = []
data_conf = {}

# dst_ip is genereated automatically
# dst_ip = ["192.168.90.100", "192.168.90.101", "192.168.90.100", "192.168.90.111"]

def is_nic_up(nic):
    addr = netifaces.ifaddresses(nic)
    return netifaces.AF_INET in addr

platform_system = pf.system()
if 'Darwin' in platform_system:
    network_faces = ["en7", "en7", "en8", "en8"]
else:
    node_name = pf.node()
    if node_name == 'lacebian1':
        # network_faces = ["ens1f1", "", "enp14s0", ""]
        #network_faces = ["ens1f1", "", "", ""]
        network_faces = ["enp10s0","", "",""]

        #network_faces = ["enp10s0", "enp10s0","enp10s0f1", "enp10s0f1"]
    elif node_name == "gqhp":
        network_faces = ["enp153s0f0", "enp153s0f0", "enp153s0f1", "enp153s0f1"]
    else:
       network_faces = ["enp119s0f0", "enp119s0f0","enp119s0f1", "enp119s0f1"]

for nic in network_faces:
    if nic =='':
        dst_mac.append("")
        dst_ip.append("")
    else:
        av_nics = netifaces.interfaces()
        if not is_nic_up(nic):
            os.system("sudo netctl restart " + nic)
            print("Warning: " + nic + "is not up")
            print("Bring up " + nic)

        print("Nic name: ", nic, " is ready")
        addrs = netifaces.ifaddresses(nic)
        dst_mac.append(addrs[netifaces.AF_LINK][0]['addr'])
        dst_ip.append(addrs[netifaces.AF_INET][0]['addr'])



data_conf['output_fft'] = True
if 'fft' in sys.argv[0]:
    data_conf['output_fft'] = True
    print("output FFT is True")
else:
    data_conf['output_fft'] = False
    print("output FFT is False")

loop_file= True
fft_method = 'numpy'
# max_workers = 8
# use data_conf to group all the parameters
data_conf['node_name'] = node_name
data_conf['network_faces'] = network_faces
data_conf['sample_rate'] = 480e6
data_conf['data_size'] = 8192
data_conf['save_hdf5'] = True
data_conf['save_lost'] = False


data_conf['voltage_scale_f'] = 0.5/2**15
data_conf['fft_npoint'] = 65536//16
data_conf['avg_n'] = 8
sample_rate_over_100 = 480000

if data_conf['output_fft']:
    data_conf['n_frames_per_loop'] = 8192*2
    data_conf['n_blocks_to_save']  = 1024
    data_conf['quantity'] = 'amplitude'
else:
    # How many udp packets of data received in one read loop
    data_conf['n_frames_per_loop'] = 8192*2
    # how many raw data read loops accumulated then save
    data_conf['n_blocks_to_save']  =1024
    data_conf['quantity'] = 'voltage'

###########################################################################
#                 parameters for save the fft of raw data                 #
###########################################################################

# the average time of spectrum
data_conf['avg_time'] = 1.0   #ms
fft_single_time = data_conf['fft_npoint'] / sample_rate_over_100
data_conf['fft_single_time'] = fft_single_time
data_conf['avg_time'] = data_conf['avg_n']*fft_single_time

# How many udp packets of data received in one read loop


# every *fft_npoint* will be grouped for FFT
# how many fft groups in one read loop
data_conf['n_fft_blocks_per_loop'] = \
        int(data_conf['data_size']* \
            data_conf['n_frames_per_loop']/data_conf['fft_npoint']/2)

# how many averageed fft groups in one read loop
data_conf['n_avg_fft_blocks_per_loop'] = \
        data_conf['n_fft_blocks_per_loop'] // data_conf['avg_n']

print("n_fft_blocks_per_loop", data_conf['n_fft_blocks_per_loop'])



# the size of socket buffer for recieving data
# maximum is 1610612736
if 'Darwin' in platform_system:
    rx_buffer = 7168000
else:
    rx_buffer = 1610612736
    # rx_buffer = 100000000


# the rx program runing forever ? file_stop_num < 0 or it will stop at saved a
# few files
# run_forever = True
data_conf['file_stop_num'] = 2

# default by hour
data_conf['split_by_min'] = False


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
