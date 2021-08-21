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
import h5py as h5


src_udp_ip = "192.168.90.20"
src_udp_port = 59000

udp_ip = "192.168.90.100"
udp_port = 60000

cycle = 49999

sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1073741824)
# err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
if err:
    raise ValueError("set socket error")

sock.bind((udp_ip, udp_port))

count = 10000

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


s_time = time.time()

packet_buff_head = packet_buff

file_count = 10

id_head_before = 0
id_tail_before = 0

# Drop the fist data frame to avoid unstable
sock.recv(packet_size)
i = 0
while True:

    pi1 = 0
    pi2 = payload_size

    hi1 = 0
    hi2 = 2

    count_down = count
    packet_buff = packet_buff_head
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

    start_time = time.time()

    id_arr = np.int32(np.frombuffer(udp_header_id,dtype='>u2'))
    if i > 0:
        if id_arr[0] - id_tail_before > 1:
            print("block is not connected", id_tail_before, id_arr[0])
            print("program last ", time.time() - s_time)
            raise ValueError("block is not connected")

    id_head_before = id_arr[0]
    id_tail_before = id_arr[-1]

    id_offsets = np.diff(id_arr) % cycle

    no_lost = False

    if (np.sum(id_offsets) - count // 2) < 2:
        if np.sum(np.diff(id_offsets)) == 0:
            no_lost = True

    udp_payload_arr = np.frombuffer(load_buff, dtype='>i2')
        
    sample_rate = 480e6
    one_sample_size = 2 
    size_of_data_per_sec = sample_rate * 2 
    acq_data_size = count * payload_size 
    duration  = acq_data_size / size_of_data_per_sec * 1.0


    if no_lost:
        print(f'you have aquired {duration:.3f} sec, ' +
                f'{acq_data_size/1024/1204:.3f} MB of data')
    else:
        print("program last ", time.time() - s_time)
        raise ValueError("sampleing is not continues")


    idx = id_offsets > 1
    num_lost_p = len(id_offsets[idx])
    print(f"{num_lost_p} packet lost, {num_lost_p/count * 100}% of packets lost.")

    
    # print("--- %s seconds ---" % (time.time() - start_time))
    
    # fout = 'out_' + str(i)
    # fout=h5.File(fout, 'w')
    # fout.create_dataset('voltage', data=udp_payload_arr)
    # fout.close()

    # time.sleep(0.08)

    if i == 0:
        i += 1
    # print("--- %s seconds ---" % (time.time() - start_time))

sock.close()
