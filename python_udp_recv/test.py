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
import sys
import time
import threading

# import h5py as h5
import numpy as np

src_udp_ip = "192.168.90.20"
src_udp_port = 59000

udp_ip = "192.168.90.100"
udp_port = 60000

cycle = 49999

# sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1610612736)
sock.setblocking(True)
# err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
if err:
    raise ValueError("set socket error")

sock.bind((udp_ip, udp_port))

count = 2000

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


num_lost_all = 0.0

def dumpdata(file_name, data, header=None):
    np.save('/dev/shm/' + file_name, data)
    # ff = h5.File(file_name, 'w')
    # ff.create_dataset('voltage', data=data )
    # ff.close()

packet_buff_head = packet_buff

file_count = 2**16

id_head_before = 0
id_tail_before = 0

# Drop the fist data frame to avoid unstable
sock.recv(packet_size)
i = 0

s_time = time.perf_counter()
time_before = s_time

while True:

    pi1 = 0
    pi2 = payload_size

    hi1 = 0
    hi2 = 2

    count_down = count
    packet_buff = packet_buff_head
    while count_down:
        sock.recv_into(packet_buff, packet_size)

        load_buff[pi1:pi2] = packet_buff[header_size:packet_size]
        header_buff[hi1:hi2] = packet_buff[4:6]
        packet_buff = packet_buff[packet_size:]

        pi1 += payload_size
        pi2 += payload_size
        hi1 += header_id_size
        hi2 += header_id_size

        count_down -= 1

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


    # if not no_lost:
        # print("program last ", time.time() - s_time)
        # raise ValueError("sampleing is not continues")


    idx = id_offsets > 1
    num_lost_p = len(id_offsets[idx])
    num_lost_all += num_lost_p
    # print(f"{num_lost_p} packet lost, {num_lost_p/count * 100}% of packets lost.")

    # print("--- %s seconds ---" % (time.time() - start_time))
    
    
    k = i % 4
    if i % 1000 < 4:
        fout = 'out_' + str(k)
        writefile = threading.Thread(target=dumpdata, args=(fout,udp_payload_arr))
        writefile.start()
    # # fout=h5.File(fout, 'w')
    # # fout.create_dataset('voltage', data=udp_payload_arr)
    # # fout.close()

    # # time.sleep(0.08)

    i += 1
    time_now = time.perf_counter()
    print("---  seconds ---",time_now - time_before, "----lost_packet:", \
            num_lost_all, num_lost_all/i/8192)
    time_before = time_now


sock.close()
