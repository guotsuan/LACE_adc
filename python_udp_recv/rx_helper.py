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
import cupy as cp
from params import split_by_min, quantity, sample_rate, \
        n_frames_per_loop,fft_method, data_size, n_fft_blocks_per_loop
import torch
import mkl_fft
from multiprocessing import shared_memory


def save_meta_file(fname, stime):
    ff = h5.File(fname, 'w')
    ff.create_dataset('start_time', data=stime)
    ff.create_dataset('time zone', data='utc')
    ff.create_dataset('version', data=0.5)
    ff.close()

def display_metrics(i,time_before,time_now, s_time,num_lost_all, payload_size):
    if i % 1000 == 0:
        size_of_data_per_sec = sample_rate * 2  # 2 byte times 480e6 points/s
        acq_data_size = n_frames_per_loop * payload_size
        # duration  = acq_data_size / size_of_data_per_sec * 1.0
        acq_time = time_now - time_before

        print(f"frame loop time: {time_now - time_before:.3f},", \
                " lost_packet:", num_lost_all, \
                num_lost_all/(i+1)/n_frames_per_loop, \
                f"already run: {time_now - s_time:.3f}")

        print("The speed of acquaring data: " +
                f'{acq_data_size/1024/1024/acq_time:.3f} MB/s\n')

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

def compute_fft_data2(data, avg_n, fft_length, scale_f):
    # fft_in_data = scale_f*data.reshape((-1, avg_n, fft_length))
    fft_in_data = scale_f*data
    
    if fft_method =='cupy':
        fft_in_data = cp.array(fft_in_data)
        if quantity == 'amplitude':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())
        elif quantity == 'power': 
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())**2, 
                    
    elif fft_method == 'pytorch':
        device = torch.device('cuda')
        fft_in_data = torch.from_numpy(fft_in_data).to(device)

        if quantity == 'amplitude':
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).cpu().detach().numpy()), axis=1)
        elif quantity == 'power': 
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).detach().cpu().numpy())**2, axis=1)

    else:
        if quantity == 'amplitude':
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))
            # mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif quantity == 'power': 
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))**2
            # mean_fft_result = np.abs(np.fft.rfft(fft_in_data))**2 


def compute_fft_data_only(fft_in_data):

    # fft_in_data = fft_in_data[i,...].reshape(-1, fft_length)
    
    if fft_method =='cupy':
        fft_in_data = cp.array(fft_in_data)
        if quantity == 'amplitude':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())
        elif quantity == 'power': 
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())**2 
                    
    elif fft_method == 'pytorch':
        device = torch.device('cuda')
        fft_in_data = torch.from_numpy(fft_in_data).to(device)

        if quantity == 'amplitude':
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).cpu().detach().numpy()), axis=1)
        elif quantity == 'power': 
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).detach().cpu().numpy())**2, axis=1)

    else:
        if quantity == 'amplitude':
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))
            # mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif quantity == 'power': 
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))**2

    # return mean_fft_result

def compute_fft_data(fout,data, n_save, avg_n, fft_length, scale_f, 
        i,j, save_hdf5):

    fft_in_data = scale_f*data.reshape((-1, avg_n, fft_length))
    
    if fft_method =='cupy':
        fft_in_data = cp.array(fft_in_data)
        if quantity == 'amplitude':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())
        elif quantity == 'power': 
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())**2 
                    
    elif fft_method == 'pytorch':
        device = torch.device('cuda')
        fft_in_data = torch.from_numpy(fft_in_data).to(device)

        if quantity == 'amplitude':
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).cpu().detach().numpy()), axis=1)
        elif quantity == 'power': 
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).detach().cpu().numpy())**2, axis=1)

    else:
        if quantity == 'amplitude':
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))
            # mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif quantity == 'power': 
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))**2

    # fft_out[i:j,...]=mean_fft_result

    # if save_hdf5:
        # f=h5.File(fout +'.h5','a')

        # if quantity not in f:
            # maxshape = (n_save*n_fft_blocks_per_loop, fft_length//2+1)
            # dset = f.create_dataset(quantity, data=mean_fft_result,
                    # maxshape=maxshape)
            # # dset.attrs['start_time'] = stime
            # # dset.attrs['block_time'] = t1
            # dset.attrs['avg_n'] = avg_n
            # dset.attrs['fft_length'] =  fft_length
            # f.close()
        # else:
            # oldshape = f[quantity].shape
            # newshape = (j, oldshape[1])
            # f[quantity].resize(newshape)
            # f[quantity][i:j,...]=mean_fft_result
            # f.close()
    # else:
        # np.save(file_name +'.npy', data)


    # save small fft group of points and submit to ques and concurrentq

def dump_fft_data(file_name, data, stime, t1, avg_n, fft_length,
        scale_f=1.0, save_hdf5=False, header=None):

    if save_hdf5:
        f=h5.File(file_name +'.h5','w')
        dset = f.create_dataset(quantity, data=data)
        dset.attrs['start_time'] = stime
        dset.attrs['block_time'] = t1
        dset.attrs['avg_n'] = avg_n
        dset.attrs['fft_length'] =  fft_length
        f.close()
    else:
        np.save(file_name +'.npy', data)


def dumpdata(file_name, data, id_data, stime, t1, nb, 
        save_hdf5=False, header=None):

    # data_type = '>i2'

    # shm_data = shared_memory.SharedMemory(data_name)
    # data = np.ndarray(n_frames_per_loop*data_size//2, 
        # dtype=data_type, buffer=shm_data.buf)

    # shm_id_data = shared_memory.SharedMemory(id_data_name)
    # id_data = np.ndarray(n_frames_per_loop, 
        # dtype=np.uint32, buffer=shm_id_data.buf)

    if save_hdf5:
        f=h5.File(file_name +'.h5','w')
        dset = f.create_dataset('voltage', data=data)
        dset.attrs['start_time'] = stime
        dset.attrs['block_time'] = t1
        dset.attrs['n_broken'] = nb 
        dset = f.create_dataset('frame_id', data=id_data)
        f.close()
    else:
        np.save(file_name +'.npy', data)

     
