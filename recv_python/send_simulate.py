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
import time, sys

from numpy.fft import fft,rfft,rfftfreq 

sock = socket.socket(socket.AF_INET, # Internet
                 socket.SOCK_DGRAM) # UDP

fft_sock = socket.socket(socket.AF_INET, # Internet
                 socket.SOCK_DGRAM) # UDP
# UDP parameters for waveform
IP = '127.0.0.1'
PORT = 50000
DPORT = 50001
sock.bind((IP,PORT))

# UDP parameters for FFT spectrum

fft_IP = '127.0.0.1'
fft_PORT = 60000
fft_DPORT = 60002
fft_sock.bind((fft_IP,fft_PORT))


# Signals parameters
# frequency
f = 3200

# Amplitude,  maxium is +0.5/-0.5
amp = 0.5
max_amp = 0.5
scale = (2**15-1) * amp / max_amp 
fft_scale = (2**32-1) * amp / max_amp 
sample_rate = 8192 * 8 


# generate wave signals
t = np.arange(0, 1.0, 1/sample_rate)
n = t.size

wave_signals = np.sin(2*np.pi*f*t) * amp

signals = np.int16(np.sin(2*np.pi*f*t)*scale)
print("The range of singals: ", signals.max(), signals.min())

# generate fft signals

fft_sig =  rfft(wave_signals)
fft_sig = np.uint32(np.abs(fft_sig/wave_signals.size)*fft_scale)
print("The rrange of fft of singals: ", fft_sig.max(), fft_sig.min())
print(fft_sig[0:20])

# Pack signals into UDP Payload

packet_size = 4096
byte_s = bytearray()
fft_byte_s = bytearray()

for i in fft_sig:
    if (i> 0):
        print("dog: ",i)
    fft_byte_s += int(i).to_bytes(4, 'big')

# print(fft_byte_s.max())
# sys.exit()

for i in signals:
    byte_s += int(i).to_bytes(2, 'big', signed=True)

seq = 0
print("len: ", len(byte_s))
print("Sending data....")
while True:
    seq =  seq % (2**32  - 1)
    for i in range(sample_rate//packet_size):
        s1 = i * 2 * packet_size
        s2 = (i + 1) * 2 * packet_size
        payload = byte_s[s1:s2] + (0).to_bytes(2, 'big') + \
            (0).to_bytes(2, 'big') +  int(seq).to_bytes(4, 'big')

        fft_payload = fft_byte_s[s1:s2] + (0).to_bytes(2, 'big') + \
            (0).to_bytes(2, 'big') +  int(seq).to_bytes(4, 'big')
        sock.sendto(payload, (IP, DPORT))
        fft_sock.sendto(fft_payload, (fft_IP, fft_DPORT))
        # print(fft_payload[0:10])
        time.sleep(0.01)
        seq += 1
