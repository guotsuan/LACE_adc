#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
the helpers that will be userd in rx.py
"""
import numpy as np
import h5py as h5
import sys
import os
import datetime, time
import termios, fcntl
from params import split_by_min

def prepare_folder(indir):
    isdir = os.path.isdir(indir)
    if isdir:
        files = os.listdir(indir)
        if len(files) != 0:
            raise ValueError(indir + ' is not empty')
            
    else:
        os.mkdir(indir)


def data_file_prefix(indir, stime):
    dt = datetime.datetime.utcfromtimestamp(time.time())
    folder_level1 = dt.strftime("%Y-%m-%d")
    folder_level2 = dt.strftime("%H")
    if split_by_min:
        folder_level3 = dt.strftime("%M")
        full_path = os.path.join(indir, folder_level1, folder_level2, folder_level3)
    else:
        full_path = os.path.join(indir, folder_level1, folder_level2)
    
    if not os.path.exists(full_path):
        os.makedirs(full_path)

    return full_path




def epoctime2date(etime, utc=True):
    import datetime

    if utc:
        return datetime.datetime.utcfromtimestamp(etime).isoformat() + ' UTC'
    else:
        return datetime.datetime.fromtimestamp(etime).isoformat()


def set_noblocking_keyboard():

    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

def dump_fft_data(file_name, data, stime, t1, avg_n, fft_length,
        scale_f=1.0, save_hdf5=False, header=None):

    fft_in_data = scale_f*data.reshape((-1, avg_n, fft_length))
    n_times = fft_in_data.shape[0]

    mean_fft_result = np.mean(np.abs(np.fft.rfft(fft_in_data, axis=2)), 
            axis=1)

    if save_hdf5:
        f=h5.File(file_name,'w')
        dset = f.create_dataset('power', data=mean_fft_result)
        dset.attrs['start_time'] = stime
        dset.attrs['block_time'] = t1
        dset.attrs['avg_n'] = avg_n
        dset.attrs['fft_length'] =  fft_length
        f.close()
    else:
        np.save(file_name, data)


def dumpdata(file_name, data, id_data, stime, t1, nb, save_hdf5=False, header=None):

    if save_hdf5:
        f=h5.File(file_name,'w')
        dset = f.create_dataset('voltage', data=data)
        dset.attrs['start_time'] = stime
        dset.attrs['block_time'] = t1
        dset.attrs['n_broken'] = nb 
        dset = f.create_dataset('frame_id', data=id_data)
        f.close()
    else:
        np.save(file_name, data)

    # ff = h5.File(file_name, 'w')
    # ff.create_dataset('voltage', data=data )
    # ff.close()
