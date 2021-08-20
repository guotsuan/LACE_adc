#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
test DAC sampling
"""

import socket
import numpy as np
import sys
import time

def id_offset(t0, t1, cycle):
    return (np.int32(t1) - np.int32(t0)) % cycle


src_udp_ip = "192.168.90.20"
src_udp_port = 59000

udp_ip = "192.168.90.100"
udp_port = 60000

cycle = 49999

sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1073741824)
# err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144*8) 

sock.bind((udp_ip, udp_port))

count = 20000

payload_size = 8192
header_size = 28
header_id_size = 2
packet_size = payload_size + header_size

udp_packet = bytearray(count*packet_size)
udp_payload = bytearray(count*(packet_size - header_size))
udp_header_id = bytearray(count*2)

packet_buff = memoryview(udp_packet)
load_buff = memoryview(udp_payload)
header_buff = memoryview(udp_header_id)

pi1 = 0
pi2 = payload_size

hi1 = 0
hi2 = 2

count_down = count

while count_down:
    sock.recvfrom_into(packet_buff, packet_size)
    load_buff[pi1:pi2] = packet_buff[header_size:packet_size]
    header_buff[hi1:hi2] = packet_buff[4:6]
    packet_buff = packet_buff[packet_size:]

    pi1 += payload_size
    pi2 += payload_size
    hi1 += header_id_size
    hi2 += header_id_size
    count_down -= 1

sock.close()

start_time = time.time()
udp_payload = np.zeros((packet_size - header_size, count), dtype=np.int16)
udp_notcont = np.zeros(count, np.bool)

id_arr = np.int32(np.frombuffer(udp_header_id,dtype='>u2'))

id_offsets = np.diff(id_arr) % cycle

no_lost = False

if (np.sum(id_offsets) - count // 2) < 2:
    if np.sum(np.diff(id_offsets)) == 0:
        no_lost = True

udp_payload = np.frombuffer(load_buff, dtype='>i2')
    
print("--- %s seconds ---" % (time.time() - start_time))
sample_rate = 480e6
one_sample_size = 2 
size_of_data_per_sec = sample_rate * 2 
acq_data_size = count * payload_size 
duration  = acq_data_size / size_of_data_per_sec * 1.0

num_lost_p = np.count_nonzero(udp_notcont)

if no_lost:
    print(f'you have aquired {duration:.3f} sec, ' +
            f'{acq_data_size/1024/1204:.3f} MB of data')
idx = id_offsets > 1
num_lost_p = len(id_offsets[idx])
print(f"{num_lost_p} packet lost, {num_lost_p/count * 100}% of packets lost.")

print("--- %s seconds ---" % (time.time() - start_time))
