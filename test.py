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

sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1073741824)

# sock.setsockopt(socket.SO_NO_CHECK,1)


sock.bind((udp_ip, udp_port))

# sock.connect((src_udp_ip, src_udp_port))
# data, addr=sock.recvfrom(8000)

pyload_size = 8192
header_size = 28
count = 20000

packet_size = pyload_size + header_size
udp_p = bytearray(count*packet_size)
mem_buff = memoryview(udp_p)

count_down = count
while count_down:

    sock.recvfrom_into(mem_buff, packet_size)
    count_down -= 1
    mem_buff = mem_buff[packet_size:]

sock.close()

start_time = time.time()
udp_payload = np.zeros((packet_size - header_size, count), dtype=np.int16)
udp_notcont = np.zeros(count, np.bool)

token0 = int.from_bytes(udp_p[4:6], 'big',signed=False)
token1 = int.from_bytes(udp_p[packet_size+4:packet_size + 6], 'big',
        signed=False)

cycle = 49999
# maxid = 0


if id_offset(token0, token1, cycle):
    same_id_before = 0
else:
    same_id_before = 1

for i in range(count):
    block_i = i*packet_size
    h1 = block_i + 4
    h2 = block_i + 6
    token1 = int.from_bytes(udp_p[h1:h2], 'big', signed=False)

    diff = id_offset(token0, token1, cycle)

    if same_id_before:
        if diff > 1:
            udp_notcont[i] = True
            print("warning: packet lose", i, token0, token1)

        same_id_before = 0
    else:
        if diff > 0:
            udp_notcont[i] = True
            print("warning: packet lose", i, token0, token1)

        same_id_before = 1

    token0 = token1

    p1 = block_i + 28
    p2 = block_i + packet_size
    udp_payload[:, i] = mem_buff[p1:p2]
    
print("--- %s seconds ---" % (time.time() - start_time))
sample_rate = 480e6
one_sample_size = 2 
size_of_data_per_sec = sample_rate * 2 
acq_data_size = count * pyload_size 
duration  = acq_data_size / size_of_data_per_sec * 1.0

num_lost_p = np.count_nonzero(udp_notcont)

print(f'you have aquired {duration:.3f} \
        sec of data: {acq_data_size/1024/1204:.3f}  MB')

print(num_lost_p, " packet lost", num_lost_p/count * 100, " % lost ")

