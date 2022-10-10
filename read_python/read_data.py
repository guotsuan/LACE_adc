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
put file_num in info.h5 donegt
"""

import os
import h5py as h5
import numpy as np
import json
import sys
import subprocess
from natsort import natsorted
from scipy.fft import rfftfreq

import matplotlib.pyplot as plt
import glob
import re

sys.path.append("../")
from recv_python.fft_helper import *
from recv_python.rx_helper import compute_fft_data2

def fft_px(data_conf, np=None):
    if np is None:
        np = data_conf['fft_npoint']

    sample_rate_in_M = data_conf['sample_rate']/1e6
    time_step = 1/sample_rate_in_M

    return rfftfreq(np, time_step)


def get_data_file_list(data_dir, tot_file_num):

    data_file_list = np.zeros(tot_file_num, dtype="|S120")
    all_days_dir = sorted([ x for x in os.listdir(data_dir) \
                if os.path.isdir(os.path.join(data_dir, x)) ])
    file_cnt=0
    try:
        for day in all_days_dir:
            day_dir = os.path.join(data_dir, day)
            all_hours_dir = [x for x in sorted(os.listdir(day_dir))]
            for hour in all_hours_dir:
                if os.path.isdir(os.path.join(day_dir, hour)):
                    data_f_list = natsorted(os.listdir(os.path.join(day_dir,hour)))
                    for each_f in data_f_list:
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

                        if file_cnt == tot_file_num:
                            raise StopIteration
    except StopIteration:

        if b'' in data_file_list:
            raise ValueError("data_file_list contains empty file name")

        print("Check hdf5 files are valid.....")

        bad_file = False
        for file in data_file_list:
            child = subprocess.Popen(['h5stat', '-S', file], stdout=subprocess.PIPE)
            streamdata = child.communicate()[0]
            rc = child.returncode
            if rc == 1:
                print(file, " is corrupted..")
                bad_file = True

        if bad_file:
            raise ValueError("hdf5 files are corrupted...")
        else:
            print("All files are checked...")
        return data_file_list


def get_data(data_dir, nfft=None, power_unit='dBm', workers=None,
             file_stop=None, fft_method=None):

    paras_file = os.path.join(data_dir, "params.py")
    info_file = os.path.join(data_dir, "info.h5")
    data_conf_file = os.path.join(data_dir, "data_conf.json")
    with open(data_conf_file, 'r') as f:
        data_conf = json.load(f)


    if file_stop is None:
        file_stop = data_conf['file_stop_num']
    else:
        file_stop = file_stop
        if data_conf['file_stop_num'] < file_stop:
            print("file_stop_num: ", data_conf['file_stop_num'])
            raise ValueError("file stop is too large..")

    data_file_list = get_data_file_list(data_dir, file_stop)
    print("last: ",data_file_list[-1])

    if len(data_file_list) != file_stop:
        print(len(data_file_list), data_conf['file_stop_num'])
        raise ValueError("data file list is empty")

    qt = data_conf['quantity']

    if file_stop is None:
        file_num = data_conf['file_stop_num']
    else:
        file_num = file_stop

    print("file_num: ", file_stop)
    n_blocks_to_save = data_conf['n_blocks_to_save']

    if nfft is None:
        fft_npoint = data_conf['fft_npoint']
        fft_data = np.empty((file_num, n_blocks_to_save, fft_npoint//2+1),
                            dtype=np.float32)

        for file_cnt, data_f in enumerate(data_file_list):
            print(data_f, file_cnt)
            df = h5.File(data_f, 'r')
            fft_data[file_cnt,...] = df[qt][...]


        px = fft_px(data_conf, fft_method)
        freq_rbw = (px[1] - px[0])*1e6
        # print("freq: ", freq_rbw, " Hz")
        fft_data_array =fft_data.reshape(-1,fft_data.shape[-1])
        if power_unit == 'dBm':
            dbm_fft = np.mean(fft_to_dBm(fft_data_array), axis=0)
        elif power_unit == 'dBV':
            dbm_fft = np.mean(fft_to_dBV(fft_data_array), axis=0)
        elif dbm_fft == None:
            dbm_fft = np.mean(fft_data_array, axis=0)
        else:
            raise("Cannot handle unit: ", power_unit)

        return px, dbm_fft, freq_rbw

    else:
        if data_conf['output_fft']:
            raise("Conflict between output_fft and nfft")
        n_frames_per_loop = data_conf['n_frames_per_loop']
        data_size = data_conf['data_size']

        if data_conf['file_stop_num'] > 100:

            fft_count =0
            mean_fft = np.empty(nfft//2+1,
                                dtype=np.float32)

            px=fft_px(data_conf, nfft)
            fft_l = data_size*n_frames_per_loop//2
            block_num = nfft // fft_l
            print("block_Num: ",block_num)
            voltage_data = np.empty((block_num, data_size*n_frames_per_loop//2),
                                dtype=np.int16)

            for file_cnt, data_f in enumerate(data_file_list):
                print(data_f, file_cnt, file_cnt%block_num)
                df = h5.File(data_f, 'r')
                voltage_data[file_cnt%block_num,...] = df[qt][...]

                if file_cnt%block_num == block_num-1:

                    print("calcuating fft now: ", fft_count)
                    fft_data = compute_fft_data2(voltage_data,nfft,
                                                data_conf['voltage_scale_f'],
                                                'amplitude',
                                                mean=True,
                                                workers=workers,
                                                 fft_method=fft_method)
                    print('fft_data shpe', fft_data.shape)
                    print('mean_fft shpe', mean_fft.shape)
                    mean_fft += fft_to_dBm(fft_data)
                    fft_count +=1

            dbm_fft =mean_fft/ fft_count

            return px, dbm_fft, (px[1] - px[0])*1.e6
        else:
            voltage_data = np.empty((file_num, data_size*n_frames_per_loop//2),
                                dtype=np.int16)

            for file_cnt, data_f in enumerate(data_file_list):
                print(data_f, file_cnt)
                df = h5.File(data_f, 'r')
                voltage_data[file_cnt,...] = df[qt][...]

            fft_npoint = nfft
            px=fft_px(data_conf, fft_npoint)
            fft_data = compute_fft_data2(voltage_data,fft_npoint,
                                        data_conf['voltage_scale_f'],
                                        'amplitude',
                                        mean=True,
                                        workers=workers,
                                        fft_method=fft_method)

            dbm_fft= fft_to_dBm(fft_data)
        return px, dbm_fft, (px[1]-px[0])*1e6




if __name__ == '__main__':
    file_list = get_data_file_list('/data/danl', 40)
    print(file_list)
    # import matplotlib.pyplot as plt
    # data_dir ="/data/raw0/"
    # px,py,rbw = get_data(data_dir,nfft=65536)
    # cc='k'
    # plt.plot(px, py, color=cc, lw=1.0,
             # label="RX with fft post-processed")

    # data_dir ="/data/fft_65536/"
    # # plt.axvline(peakf, color='y', alpha=0.5)
    # px,py2,rbw = get_data(data_dir)
    # cc='k'
    # plt.plot(px, py, '--', color='r', lw=0.8,
             # label="RX with fft on-the-fly")
    # plt.ylim([-100,-60])
    # plt.xlim([-1,245])
    # plt.xlabel("MHz")
    # plt.ylabel("dBm")
    # plt.title("Sanity Check")
    # plt.legend()
    # plt.show()


