#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""

"""
import socket
import time
import numpy as np

src_udp_ip = "192.168.90.20"
src_udp_port = 59000

udp_ip = "192.168.90.100"
udp_port = 60000

cycle = 49999

rx_buffer = 1610612736
count = 10
sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rx_buffer)
# sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
sock.bind((udp_ip, udp_port))

packet_size = 8200
header_size = 28
udp_payload = bytearray(count*packet_size)
id_array = bytearray(count*4)

# udp_payload = bytearray(count*4)

load_buff = memoryview(udp_payload)
id_buff = memoryview(id_array)
t1 = time.perf_counter()

maxid = 0

# n_frames_per_loop = 4096
# udp_payload = bytearray(n_frames_per_loop*payload_size)
# udp_data = bytearray(n_frames_per_loop*data_size)
# udp_id = bytearray(n_frames_per_loop*id_size)

# payload_buff = memoryview(udp_payload)
# data_buff = memoryview(udp_data)
# id_buff = memoryview(udp_id)

while True:
    sock.recv_into(load_buff, 8200)
    # pid = np.frombuffer(udp_payload[8196:8200], '>u4')
    # breakpoint()

    #print(pid)
    # if pid > maxid:
        # maxid = pid
    # print(np.frombuffer(load_buff[8198:8220], '>u2'))
    # count -= 1

# print(maxid)
# t2 = time.perf_counter()
# print(t2-t1)
sock.close()
