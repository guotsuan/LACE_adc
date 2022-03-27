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
import torch
import mkl_fft
from multiprocessing import shared_memory

from params import split_by_min, data_conf,fft_method,labels

def save_meta_file(fname, stime, s_id):
    ff = h5.File(fname, 'w')
    str_stime = epoctime2date(stime)
    ff.create_dataset('start_time', data=str_stime, dtype='S30')
    ff.create_dataset('time zone', data='utc')
    ff.create_dataset('version', data=0.5)
    ff.create_dataset('id_start', data=s_id)
    ff.close()

def display_metrics(time_before,time_now, s_time, num_lost_all, dconf):

    sample_rate = dconf['sample_rate']
    n_frames_per_loop = dconf['n_frames_per_loop']
    payload_size = dconf['payload_size']

    size_of_data_per_sec = sample_rate * 2  # 2 byte times 480e6 points/s
    acq_data_size = n_frames_per_loop * payload_size
    # duration  = acq_data_size / size_of_data_per_sec * 1.0
    acq_time = time_now - time_before

    os.system("clear")
    print(f"frame loop time: {time_now - time_before:.3f},", \
            " lost_packet:", num_lost_all, \
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


def data_file_prefix(indir, stime, unpack=False):
    if isinstance(stime, float):
        dt = datetime.datetime.utcfromtimestamp(stime)
    else:
        dt = datetime.datetime.fromisoformat(stime)
    folder_level1 = dt.strftime("%Y-%m-%d")
    folder_level2 = dt.strftime("%H")
    if split_by_min:
        folder_level3 = dt.strftime("%M")
        full_path = os.path.join(indir, folder_level1, folder_level2, folder_level3)
    else:
        full_path = os.path.join(indir, folder_level1, folder_level2)
    
    if not unpack:
        if not os.path.exists(full_path):
            os.makedirs(full_path)

    if unpack:
        return folder_level1, folder_level2, folder_level3
    else:
        return full_path




def epoctime2date(etime, utc=True):

    if utc:
        return datetime.datetime.utcfromtimestamp(etime).isoformat() 
        # return datetime.datetime.utcfromtimestamp(etime).isoformat() + ' UTC'
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

def compute_fft_data2(data, avg_n, fft_length, scale_f, quantity, mean=True):
    if mean:
        fft_in_data = scale_f*data.reshape((-1, avg_n, fft_length))
    else:
        fft_in_data = scale_f*data
    
    if fft_method =='cupy':
        fft_in_data = cp.array(fft_in_data)
        if quantity == 'amplitude':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())
        elif quantity == 'power': 
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())**2, 

        if mean:
            mean_fft_result = np.mean(mean_fft_result, axis=1)
                    
    elif fft_method == 'pytorch':
        device = torch.device('cuda')
        fft_in_data = torch.from_numpy(fft_in_data).to(device)

        if quantity == 'amplitude':
            mean_fft_result = np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).cpu().detach().numpy())
        elif quantity == 'power': 
            mean_fft_result = np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).detach().cpu().numpy())**2

        if mean:
            mean_fft_result = np.mean(mean_fft_result, axis=1)
    else:
        if quantity == 'amplitude':
            # mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))
            mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif quantity == 'power': 
            # mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))**2
            mean_fft_result = np.abs(np.fft.rfft(fft_in_data))**2 

        if mean:
            mean_fft_result = np.mean(mean_fft_result, axis=1)

    return mean_fft_result

def compute_fft_data_only(fft_in_data):

    # fft_in_data = fft_in_data[i,...].reshape(-1, fft_length)
    
    if fft_method =='cupy':
        fft_in_data = cp.array(fft_in_data)
        if data_conf['quantity'] == 'amplitude':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())
        elif data_conf['quantity'] == 'power': 
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())**2 
                    
    elif fft_method == 'pytorch':
        device = torch.device('cuda')
        fft_in_data = torch.from_numpy(fft_in_data).to(device)

        if data_conf['quantity'] == 'amplitude':
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).cpu().detach().numpy()), axis=1)
        elif data_conf['quantity'] == 'power': 
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).detach().cpu().numpy())**2, axis=1)

    else:
        if quantity == 'amplitude':
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))
            # mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif quantity == 'power': 
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))**2

    return mean_fft_result

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

def save_raw_hdf5(data_dir, raw_data_to_file, raw_block_time_file,
        raw_id_to_file, nn, rx):

    print("save raw pid: ", os.getpid())
    file_path_old = ''

    n_frames_per_loop = data_conf['n_frames_per_loop']
    data_size = data_conf['data_size']
    n_blocks_to_save  = data_conf['n_blocks_to_save']
    quantity = data_conf['quantity']
    output_sel = data_conf['output_sel']
    file_stop_num = data_conf['file_stop_num']
    block_time = raw_block_time_file

    loop = True
    file_cnt = 0

    idx = nn.value

    while loop:
        if nn.value != idx:
            idx = nn.value
            file_path = data_file_prefix(data_dir, block_time)
            if file_path_old =='':
                file_path_old = file_path
            fout = os.path.join(file_path, labels[output_sel] +
                    '_' + str(file_cnt))

            print("nn: ", nn.value)

            f=h5.File(fout +'.h5','a')

            if idx == 1:
                maxshape = (n_blocks_to_save, n_frames_per_loop*data_size//2,)
                dset = f.create_dataset(quantity, 
                        data=np.atleast_2d(raw_data_to_file), 
                        maxshape=maxshape)
                maxshape = (n_blocks_to_save,)
                dset = f.create_dataset('block_time', 
                        data=np.atleast_1d(np.asarray(raw_block_time_file, dtype='S30')),
                        maxshape=maxshape)
                maxshape = (n_blocks_to_save,n_frames_per_loop,)
                dset = f.create_dataset('block_ids', 
                        data=np.atleast_2d(raw_id_to_file), 
                        maxshape=maxshape)
            else:
                oldshape = f[quantity].shape
                newshape = (idx, oldshape[1])
                # print('New shape: ', newshape)

                f[quantity].resize(newshape)
                f[quantity][idx-1,...]=raw_data_to_file

                newshape = (idx,)
                f['block_time'].resize(newshape)
                f['block_time'][idx-1]=raw_block_time_file

                oldshape = f['block_ids'].shape
                newshape = (idx, oldshape[1])
                f['block_ids'].resize(newshape)
                f['block_ids'][idx-1,...]=raw_id_to_file


            if idx == n_blocks_to_save:
                f.close()

                if file_path == file_path_old:
                    file_cnt += 1
                else:
                    file_cnt = 0

                file_path_old = file_path


            if file_stop_num < 0 or file_cnt <= file_stop_num:
                loop = True
            else:
                loop = False
                print("save fft loop ended")


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


def dumpdata_hdf5(file_name, data, id_data, block_time):

        # print("save raw pid: ", os.getpid())

        # n_frames_per_loop = data_conf['n_frames_per_loop']
        # data_size = data_conf['data_size']
        # n_blocks_to_save  = data_conf['n_blocks_to_save']
        quantity = 'power'
        # output_sel = data_conf['output_sel']
        # file_stop_num = data_conf['file_stop_num']

        f=h5.File(file_name +'.h5','w')
        dset = f.create_dataset(quantity, data=data)
        dset = f.create_dataset('block_time', data=block_time)
        # dset.attrs['block_time'] = epoctime2date(block_time)
        dset = f.create_dataset('block_ids', data=id_data)

        f.close()

def dumpdata_fft_hdf5(file_name, data, id_data, block_time):

        avg_n = data_conf['avg_n']
        fft_npoint = data_conf['fft_npoint']
        quantity = data_conf['quantity']

        f=h5.File(file_name +'.h5', 'w')

        dset = f.create_dataset(quantity, data=data)
        dset.attrs['avg_n'] = avg_n
        dset.attrs['fft_length'] =  fft_npoint

        dset = f.create_dataset('block_time', data=block_time)
        dset = f.create_dataset('block_ids', data=id_data)

        f.close()


def compute_fft(data_in, fft_length, i):

    fft_in_data = data_conf['scale_f']*data_in[i,...].reshape(-1, fft_length)
    
    if fft_method =='cupy':
        fft_in_data = cp.array(fft_in_data)
        if data_conf['quantity'] == 'amplitude':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())
        elif data_conf['quantity'] == 'power': 
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())**2 
                    
    elif fft_method == 'pytorch':
        device = torch.device('cuda')
        fft_in_data = torch.from_numpy(fft_in_data).to(device)

        if data_conf['quantity'] == 'amplitude':
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).cpu().detach().numpy()), axis=1)
        elif data_conf['quantity'] == 'power': 
            mean_fft_result = np.mean(np.abs(torch.fft.rfft(fft_in_data, 
                dim=-1).detach().cpu().numpy())**2, axis=1)

    else:
        if data_conf['quantity'] == 'amplitude':
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))
            # mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif data_conf['quantity'] == 'power': 
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))**2

    return mean_fft_result

    # if not qq.empty():
        # with lock:
            # data, ids, ide, block_time = qq.get()
        # data = data.reshape(-1, fft_length)
        # fft_data = compute_fft_data_only(data)
        # with wlock:
            # fft_out_q.put((fft_data, ids, ide, block_time))

def get_sample_data_new(sock,dconf):                 #{{{ payload_size,data_size, 

    n_frames_per_loop = dconf['n_frames_per_loop']
    payload_size = dconf['payload_size']
    data_size = dconf['data_size']
    id_size = dconf['id_size']
    data_type = dconf['data_type']
    id_tail_before = dconf['id_tail_before']
    output_fft = dconf['output_fft']

    udp_payload = bytearray(payload_size)
    udp_data = bytearray(n_frames_per_loop*data_size)
    udp_id = bytearray(n_frames_per_loop*id_size)

    payload_buff = memoryview(udp_payload)
    data_buff = memoryview(udp_data)
    id_buff = memoryview(udp_id)

    payload_buff_head = payload_buff
    
    i = 0
    file_cnt = 0
    fft_block_cnt = 0
    marker = 0
    num_lost_all = 0.0

    s_time = time.perf_counter()
    time_before = s_time
    t0_time = time.time()

    print("get sampe pid: ", os.getpid())

    # the period of the consecutive ID is 2**32 - 1 = 4294967295
    cycle = 4294967295
    max_id = 0

    while True:

        pi1 = 0
        pi2 = data_size

        hi1 = 0
        hi2 = id_size

        count_down = n_frames_per_loop
        payload_buff = payload_buff_head
        block_time1 = time.time()

        while count_down:
            sock.recv_into(payload_buff, payload_size)
            data_buff[pi1:pi2] = payload_buff[0:data_size]
            id_buff[hi1:hi2] = payload_buff[payload_size - id_size:payload_size]

            pi1 += data_size
            pi2 += data_size
            hi1 += id_size
            hi2 += id_size

            count_down -= 1

        block_time2 = time.time()
        id_arr = np.uint32(np.frombuffer(udp_id,dtype='>u4'))

        diff = id_arr[0] - id_tail_before
        if (diff == 1) or (diff == - cycle ):
            pass
        else:
            print("block is not connected", id_tail_before, id_arr[0])
            print("program last ", time.time() - s_time)
            num_lost_all += 1

        # update the ids before for next section
        id_head_before = id_arr[0]
        id_tail_before = id_arr[-1]

        id_offsets = np.diff(id_arr) % cycle

        idx = id_offsets > 1

        num_lost_p = len(id_offsets[idx])

        if (num_lost_p > 0):
            bad=np.arange(id_offsets.size)[idx][0]
            print(id_arr[bad-2:bad+3])
            num_lost_all += num_lost_p
        else:
            udp_data_arr = np.frombuffer(udp_data, dtype=data_type)
            # block_time = epoctime2date((block_time1 + block_time2)/2.)
            block_time = (block_time1 + block_time2)/2.
            if output_fft:
                raw_data_q.put((udp_data_arr,id_arr[0], id_arr[-1], block_time))
            else:
                raw_data_q.put((udp_data_arr,id_arr, block_time))

        time_now = time.perf_counter()

        if i == 1000:
            block_time = epoctime2date((block_time1 + block_time2)/2.)
            display_metrics(time_before, time_now, s_time, num_lost_all, 
                    data_conf)
            i = 0

        time_before = time_now
        i +=1

        # }}}

def get_sample_data(sock,raw_data_q, dconf, v):                 #{{{ payload_size,data_size, 

    n_frames_per_loop = dconf['n_frames_per_loop']
    payload_size = dconf['payload_size']
    data_size = dconf['data_size']
    id_size = dconf['id_size']
    data_type = dconf['data_type']
    id_tail_before = dconf['id_tail_before']
    output_fft = dconf['output_fft']

    udp_payload = bytearray(n_frames_per_loop*payload_size)
    udp_data = bytearray(n_frames_per_loop*data_size)
    udp_id = bytearray(n_frames_per_loop*id_size)

    payload_buff = memoryview(udp_payload)
    data_buff = memoryview(udp_data)
    id_buff = memoryview(udp_id)

    warmup_data = bytearray(payload_size)
    warmup_buff = memoryview(warmup_data)

    payload_buff_head = payload_buff
    
    i = 0
    file_cnt = 0
    fft_block_cnt = 0
    marker = 0
    num_lost_all = 0.0

    s_time = time.perf_counter()
    time_before = s_time
    t0_time = time.time()

    print("get sampe pid: ", os.getpid())

    # the period of the consecutive ID is 2**32 - 1 = 4294967295
    cycle = 4294967295
    max_id = 0
    loop = True
    tmp_id = 0
    testme = False

    while loop:

        pi1 = 0
        pi2 = data_size

        hi1 = 0
        hi2 = id_size

        count_down = n_frames_per_loop
        payload_buff = payload_buff_head
        block_time1 = time.time()

        while count_down:
            sock.recv_into(payload_buff, payload_size)
            data_buff[pi1:pi2] = payload_buff[0:data_size]
            id_buff[hi1:hi2] = payload_buff[payload_size - id_size:payload_size]

            pi1 += data_size
            pi2 += data_size
            hi1 += id_size
            hi2 += id_size

            count_down -= 1

        block_time2 = time.time()
        id_arr = np.uint32(np.frombuffer(udp_id,dtype='>u4'))

        diff = id_arr[0] - id_tail_before
        if (diff == 1) or (diff == - cycle ):
            pass
        else:
            print("block is not connected", id_tail_before, id_arr[0])
            print("program last ", time.time() - s_time)
            num_lost_all += 1
            with open("block_dist.txt", 'a') as fff:
                fff.write("fresh id: " + str(id_arr[0]) + " " 
                        + str(id_arr[0]%16))
                fff.close()

            while id_arr[-1] % 16 != 15:
                sock.recv_into(warmup_buff, payload_size)
                tmp_id = int.from_bytes(warmup_data[payload_size-id_size:
                payload_size], 'big')
                testme = True

        # update the ids before for next section
        id_head_before = id_arr[0]
        id_tail_before = id_arr[-1]

        id_offsets = np.diff(id_arr) % cycle

        idx = id_offsets > 1

        num_lost_p = len(id_offsets[idx])

        if (num_lost_p > 0):
            bad=np.arange(id_offsets.size)[idx][0]
            print(id_arr[bad-2:bad+3])
            num_lost_all += num_lost_p
            with open("middle_dist.txt", 'a') as fff:
                fff.write("fresh id: " + str(id_arr[0]) + " " 
                        + str(id_arr[0]%16))
                fff.close()
            while id_arr[-1] % 16 != 15:
                sock.recv_into(warmup_buff, payload_size)
                tmp_id = int.from_bytes(warmup_data[payload_size-id_size:
                payload_size], 'big')
                testme = True

        else:
            udp_data_arr = np.frombuffer(udp_data, dtype=data_type)
            # block_time = epoctime2date((block_time1 + block_time2)/2.)
            block_time = (block_time1 + block_time2)/2.

            if output_fft:
                raw_data_q.put((udp_data_arr,id_arr, block_time))
            else:
                raw_data_q.put((udp_data_arr,id_arr, block_time))
                # raw_data_q.send((udp_data_arr,id_arr, block_time))

        time_now = time.perf_counter()

        if i == 2000:
            block_time = epoctime2date((block_time1 + block_time2)/2.)
            display_metrics(time_before, time_now, s_time, num_lost_all, 
                    data_conf)
            i = 0

        time_before = time_now
        i +=1

        if v.value == 1:
            loop = False
            print("read finished ")

    return

        # }}}
