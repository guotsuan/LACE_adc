#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
the parameters for recv.py
"""

# Neworking settings for reciever and data storage

###########################
#  Output 1 and Output 2  #
###########################

src_ip = ["192.168.90.20", "192.168.90.21", "192.168.90.30", "192.168.90.31"]

src_port = [59000, 59001, 59000, 59001]

dst_mac = ["24:5e:be:59:8d:46", "24:5e:be:59:8d:46", "14:02:ec:76:60:45", \
        "14:02:ec:76:60:45"]

dst_port = [60000, 60001, 60000, 60001]

dst_ip = ["192.168.90.100", "192.168.90.100", "192.168.90.101", "192.168.90.101"]

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
rx_buffer = 1073741824

# How many packets of data accumulated before saving
counts_to_save = 1000

# the rx program runing forever ?
forever = True
