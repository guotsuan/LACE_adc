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

src_udp_ip = "192.168.90.20"
src_udp_port = 59000


udp_ip = "192.168.90.100"
udp_port = 60000

sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16384)

# sock.setsockopt(socket.SO_NO_CHECK,1)


sock.bind((udp_ip, udp_port))

# sock.connect((src_udp_ip, src_udp_port))
# data, addr=sock.recvfrom(8000)

pyload_size = 8192
header_size = 28
count = 100

packet_size = pyload_size + header_size
udp_p = bytearray(count*packet_size)
mem_buff = memoryview(udp_p)

while count:

    sock.recvfrom_into(mem_buff, packet_size)
    count -= 1
    mem_buff = mem_buff[packet_size:]

sock.close()

udp_payload = np.zeros((packet_size - header_size, count), dtype=np.int16)
udp_notcont = np.zeros(count, np.bool)

token0 = np.frombuffer(udp_p[4:6], dtype='>i2')
cycle = 2**16 -1
for i in range(count):
    h1 = i*packet_size + 4
    h2 = i*packet_size + 6
    token1 = np.frombuffer(udp_p[h1:h2], dtype='>i2')

    diff = (token1 - token0) % cycle
    if diff > 1:
        udp_notcont[i] = True
        print("packet lose", i, token0, token11)
        sys.exit()

    token0 = token1
    

