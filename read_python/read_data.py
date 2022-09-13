#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@lacebian1>
#
# Distributed under terms of the MIT license.

"""
Functions of reading data recorded
"""

"""
put file_num in info.h5 done
"""

import os
import h5py as h5
import numpy as np
import json
import sys
from scipy.fft import rfftfreq

import matplotlib.pyplot as plt

def fft_px(data_conf):
    np = data_conf['fft_npoint']
    sample_rate_in_M = data_conf['sample_rate']/1e6
    time_step = 1/sample_rate_in_M
    return rfftfreq(np, time_step)


def get_data_file_list(data_dir, tot_file_num):

    data_file_list = np.zeros(tot_file_num, dtype="|S120")
    all_days_dir = [ x for x in os.listdir(data_dir) \
                if os.path.isdir(os.path.join(data_dir, x)) ]
    file_cnt=0
    for day in (sorted(all_days_dir)):
        day_dir = os.path.join(data_dir, day)
        all_hours_dir = [x for x in sorted(os.listdir(day_dir))]
        for hour in all_hours_dir:
            if os.path.isdir(os.path.join(day_dir, hour)):
                for each_f in os.listdir(os.path.join(day_dir,hour)):
                    f_full_name = os.path.join(os.path.join(day_dir, hour, each_f))

                    if os.path.isfile(f_full_name):
                        data_file_list[file_cnt] = f_full_name
                        file_cnt += 1

                    # if there are mins folder
                    elif os.path.isdir(f_full_name):
                        for each_f2 in os.listdir(f_full_name):
                            f2_full_name = os.path.join(os.path.join(f_full_name,
                                                                    each_f2))

                            if os.path.isfile(f2_full_name):
                                data_file_list[file_cnt] = f2_full_name
                                file_cnt += 1
                    else:
                        raise("There are unrecogized files in the data folders")

    return data_file_list


data_dir ="/data/test10/"
paras_file = os.path.join(data_dir, "params.py")
info_file = os.path.join(data_dir, "info.h5")
data_conf_file = os.path.join(data_dir, "data_conf.json")

info_f = h5.File(info_file)
tot_file_num = info_f['file_stop_num'][...]

# get the file list of data files
data_file_list = get_data_file_list(data_dir, tot_file_num)
print(data_file_list[0:5])

with open(data_conf_file, 'r') as f:
    data_conf = json.load(f)

fft_npoint = data_conf['fft_npoint']
n_blocks_to_save = data_conf['n_blocks_to_save']
file_num = data_conf['file_stop_num']
file_num = 10
fft_data = np.empty((file_num, n_blocks_to_save, fft_npoint//2+1),
                    dtype=np.float32)

for file_cnt, data_f in enumerate(data_file_list[0:10]):
    print(data_f, file_cnt)
    df = h5.File(data_f, 'r')
    fft_data[file_cnt,...] = df['amplitude'][...]


px = fft_px(data_conf)
plt.plot(px, fft_data[0,0,:])
plt.savefig("test.pdf")


