#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""

Read the output file from C
"""

import numpy as np
from numpy.fft import rfftfreq
from scipy.fft import rfft
import matplotlib.pyplot as plt

infile_name = './temp_1'
npoints = 8192 * 2

with open(infile_name, 'rb') as f:
    data_in = np.frombuffer(f.read(), dtype='>i2')

scale_f = 1.0/ 2 ** 16
sample_rate = 480 # Mhz

# real_data = data.reshape(8000, -1) * scale_f
real_data = data_in * scale_f

timestep = 1.0/sample_rate



k = 2.23
beta = 16.7

kasier_fil = np.kaiser(npoints, beta)
factor_kasier = np.sum(kasier_fil)/npoints

fft_data = rfft(real_data.reshape((-1, npoints)),  workers=-1)
freq = rfftfreq(npoints, d=timestep)

power = np.mean(np.log10((np.abs(fft_data) ** 2)), axis=0)
plt.plot(freq, power)
plt.savefig('test_new.pdf')

    

