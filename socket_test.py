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

#src_udp_ip = "192.168.90.30"
#src_udp_port = 59000

udp_ip = "192.168.90.100"
udp_port = 60000

cycle = 49999

sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.bind((udp_ip, udp_port))

data = sock.recv(8192)
if data:
    print("Socket recieved data sucessuflly....")


