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

src_udp_ip = "192.168.90.20"
src_udp_port = 59000

udp_ip = "192.168.90.100"
udp_port = 60000

cycle = 49999

count = 4096
# sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
sock.bind((udp_ip, udp_port))

packet_size = 8220
header_size = 28
udp_payload = bytearray(count*(packet_size - header_size))

load_buff = memoryview(udp_payload)
t1 = time.perf_counter()
while count:
    sock.recv_into(load_buff, 8220)
    load_buff = load_buff[8220:]
    count -= 1

t2 = time.perf_counter()
print(t2-t1)
