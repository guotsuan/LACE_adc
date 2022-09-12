#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
covert raw data to fft data
"""

import numpy as np
import h5py as h5
import datetime


from rx_helper import *
from params import *

data_dir = './raw_data'

fname = os.path.join(data_dir, 'info.h5')

ff = h5.File(fname, 'r')
start_id = ff['id_start']

output_sel = 0

str_time = str(ff['start_time'].asstr()[...])

start_time = datetime.datetime.fromisoformat(str_time)

input_time = start_time + datetime.timedelta(seconds=1)

str_input_time = datetime.datetime.isoformat(input_time)

raw_dir = data_file_prefix(data_dir,str_input_time)
f1,f2,f3 = data_file_prefix(data_dir,str_input_time, unpack=True)

loop_ctl = True

file_cnt = 0

scale_f = data_conf['scale_f']
fft_length = data_conf['fft_npoint']
avg_n = data_conf['avg_n']
data_size = data_conf['data_size']
n_frames_per_loop = data_conf['n_frames_per_loop']
dur_per_frame = data_size/sample_rate_over_100/2.0
ngrp = n_frames_per_loop*data_size/avg_n/2/fft_length
quantity = 'amplitude'
print("ngrp, ", ngrp)
fft_block_times = np.zeros((int(ngrp), ), dtype='S30')


h5out = None
while loop_ctl:
    fout = os.path.join(raw_dir, labels[output_sel] +
            '_' + str(file_cnt) +".h5")

    print("fcnt", file_cnt)
    if os.path.exists(fout):
        ff = h5.File(fout, 'r')
        voltage = ff['voltage'][...]
        block_ids = ff['block_ids'][...]

        dt_frame_start = datetime.timedelta(milliseconds=(block_ids[0] -
            start_id)*dur_per_frame)
        
        t_frame_start = start_time + dt_frame_start  
        fft_data = compute_fft_data2(voltage, avg_n, fft_length, scale_f,
                quantity)

        dur_of_block = datetime.timedelta(milliseconds=(block_ids[-1] -
            block_ids[0])*dur_per_frame)

        for kk in range(int(ngrp)):
            fft_block_times[kk] = (t_frame_start +
                    kk*dur_of_block/ngrp).isoformat()


        if file_cnt == 0:
            fout_name = os.path.join(data_dir, f1, f2, labels[output_sel] +
                '_fft_' + f3 +".h5")
            print(fout_name)
            h5out = h5.File(fout_name, 'w')
            maxshape = None
            dset = h5out.create_dataset(quantity, data=fft_data,
                    maxshape=(None, fft_data.shape[1]), chunks=True)

            dset.attrs['avg_n'] = avg_n
            dset.attrs['fft_length'] =  fft_length

            dset = h5out.create_dataset('block_time', data=fft_block_times,
                    dtype='S30',  maxshape=(None,), chunks=True)
        else:
            oldshape = h5out[quantity].shape
            newshape = (int(oldshape[0] + ngrp), oldshape[1])
            h5out[quantity].resize(newshape)
            h5out[quantity][oldshape[0]:newshape[0],...]=fft_data

            oldshape = h5out['block_time'].shape
            newshape = (int(oldshape[0] + ngrp), )
            h5out['block_time'].resize(newshape)
            h5out['block_time'][oldshape[0]:newshape[0]] = fft_block_times

        
    else:
        h5out.close()
        loop_ctl = False

    file_cnt += 1


