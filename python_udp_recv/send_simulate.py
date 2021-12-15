#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
simulate of sending data

"""

import numpy as np
import socket 
import time

sock = socket.socket(socket.AF_INET, # Internet
                 socket.SOCK_DGRAM) # UDP

# UDP parameters
IP = '127.0.0.1'
PORT = 50000
DPORT = 50001

sock.bind((IP,PORT))

# Signals parameters
# frequency
f = 32000

# Amplitude,  maxium is +0.5/-0.5
amp = 0.5
max_amp = 0.5
scale = (2**15-1) * amp / max_amp 
sample_rate = 819200


# generate signals
t = np.arange(0, 1.0, 1/sample_rate)
n = t.size
signals = np.int16(np.sin(2*np.pi*f*t)*scale)
print("singals: ", signals.max(), signals.min())

# Pack signals into UDP Payload

size = 4096
byte_s = bytearray()

for i in signals:
    byte_s += int(i).to_bytes(2, 'big', signed=True)

seq = 0
print("len: ", len(byte_s))
print("Sending data....")
while True:
    seq =  seq % (2**32  - 1)
    for i in range(sample_rate//size):
        s1 = i * 2 * size
        s2 = (i + 1) * 2 * size
        payload = byte_s[s1:s2] + (0).to_bytes(2, 'big') + \
            (0).to_bytes(2, 'big') +  int(seq).to_bytes(4, 'big')
        sock.sendto(payload, (IP, DPORT))
        time.sleep(0.01)
        seq += 1
