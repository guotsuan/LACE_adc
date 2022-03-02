#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
read h5 format data
"""

import h5py as h5
import numpy as np
from params import *
from fft_helper import fft_to_dBm
import matplotlib.pyplot as plt
from numpy.fft import fft,rfft,rfftfreq,fftfreq
from rx_helper import epoctime2date
import sys

data_dir = './'

data_size = 8192
cycle = 4294967295

file_stop_num = 50

id_arr = np.zeros((2, file_stop_num, counts_to_save), dtype=np.uint32)
voltage_arr = np.zeros((2, file_stop_num, counts_to_save*data_size//2), dtype=np.float32)

output_type = [0, 2]

def check_continume(data):
    id_offsets = np.diff(id_arr) % cycle
    idx = id_offsets > 1
    num_lost_p = len(id_offsets[idx])

    return num_lost_p, idx


for j,t in enumerate(output_type):
    for i in range(file_stop_num):
        fout = 'data/' +labels[t] + '_' + str(i) + '.h5'
        x = h5.File(fout, 'r')
        vol = x['voltage'][...] * scale_fs[t]
        print("starttime: ", i, epoctime2date(x['voltage'].attrs["offset_time"], utc=False))
        frame_id = x['frame_id'][...]
        id_arr[j,i,:] = frame_id

        

        voltage_arr[j,i,...] = vol



sample_rate = 480 #Mhz
timestep = 1.0/sample_rate

k = 2.23
beta = 16.7

kasier_fil = np.kaiser(data_size//2, beta)
factor_kasier = np.sum(kasier_fil)


bad_frame_num, idx = check_continume(id_arr[0,...].ravel())
print(bad_frame_num)

print(id_arr[0,...].ravel())
print(id_arr[1,...].ravel())


fft_num = 8192


data0 = (voltage_arr[0,...].reshape(-1, fft_num))
data1 = (voltage_arr[1,...].reshape(-1, fft_num))

avg_n = data1.shape[0]
print(data0.shape)

print("averge times: ", avg_n)

# avg_n = 1
plt.figure()
if bad_frame_num == 0:
    print("good good")
    result = np.zeros((avg_n, fft_num))
    real_result = np.zeros((avg_n, fft_num))
    imag_result = np.zeros((avg_n, fft_num))
    freq = fftfreq(fft_num, d=timestep)
    for i in range(avg_n):
        fft_data_1 = fft(data0[i,:])
        
        fft_data_2 = fft(data1[i,:])


        # power = np.abs(fft_data_1 * fft_data_2)

        cross = fft_data_1 * np.conjugate(fft_data_2)

        power = fft_to_dBm(cross)

        # phase = np.arctan(cross.imag/cross.real)
        phase = np.arctan2(cross.imag, cross.real)

        result[i, :] = phase
        real_result[i, :] = cross.real
        imag_result[i, :] = cross.imag

    #plt.plot(freq[1:fft_data_1.size//2], power[1:fft_data_1.size//2], lw = 1.0)
    # Plot dbm
    # plt.plot(freq[1:fft_data_1.size//2], power[1:fft_data_1.size//2], lw = 1.0)
    print("haha")
    mean_result = np.mean(result, axis=0)
    mean_real_result = np.mean(real_result, axis=0)
    mean_imag_result = np.mean(imag_result, axis=0)
    scale_r = np.mean(np.abs(mean_real_result))
    scale_i = np.mean(np.abs(mean_imag_result))

    plt.plot(freq[1:fft_data_1.size//2], mean_result[1:fft_data_1.size//2], 
            lw = 1.0, color='k', label='Phase')
    plt.plot(freq[1:fft_data_1.size//2], mean_imag_result[1:fft_data_1.size//2]/scale_i, 
            lw = 1.0, color='b', label="imag")
    plt.plot(freq[1:fft_data_1.size//2],
            mean_real_result[1:fft_data_1.size//2]/scale_r, 
            lw = 1.0, color='r', label="real")
    plt.xlabel("Mhz")
    plt.ylabel("arctan(Cross_im/Cross_real)")
    plt.legend()
    # plt.plot(freq[1:fft_data_1.size//2][0:3000],
            # phase[1:fft_data_1.size//2][0:3000], lw = 1.0)

plt.show()

