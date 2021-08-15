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

src_udp_ip = "192.168.90.20"
src_udp_port = 59000


udp_ip = "192.168.90.100"
udp_port = 60000

sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
# sock.setsockopt(socket.SO_NO_CHECK,1)


sock.bind((udp_ip, udp_port))
# sock.setsockopt(socket.IPPROTO_UDP, 1, 1)

# sock.connect((src_udp_ip, src_udp_port))
# data, addr=sock.recvfrom(8000)

data= sock.recv(16000)


