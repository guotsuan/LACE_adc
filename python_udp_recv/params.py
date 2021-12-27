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
fft_data = True

if fft_data: 
    src_udp_ip = "192.168.90.21"
    src_udp_port = 59001

    udp_ip = "192.168.90.100"
    udp_port = 60001
    data_type = '>u4'
else:
    src_udp_ip = "192.168.90.20"
    src_udp_port = 59000

    udp_ip = "192.168.90.100"
    udp_port = 60000
    data_type = '>i2'


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
