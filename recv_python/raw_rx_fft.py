#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
test DAC sampling
"""

import socket
import sys
import os
import time
import datetime
import shutil
from concurrent import futures
from functools import partial

import h5py as h5
import numpy as np
from multiprocessing import Queue, Process, RawValue, Lock, Pool, Pipe


# put all configrable parameters in params.py
from params import *
from rx_helper import *

data_dir = ''

if not data_conf['output_fft']:
    sys.exit("wrong program, please use raw_rx2.py or change output_fft to True")

args_len = len(sys.argv)
if args_len < 3:
    print("python rx.py <rx_type> <data_dir> ")
    sys.exit()

elif args_len == 3:
    try:
        args = sys.argv[1].split()
        input_type = int(args[0])

        data_dir = sys.argv[2]
        output_sel = input_type
    except:
        print("input type must be one of 0,1,2,3")

    if output_sel > 3:
        print("input type", input_type, " must be one of 0,1,2,3")
        sys.exit()
    else:
        print("recieving output type from input: ", labels[output_sel])
        print("saving into the folder: ", data_dir)

if data_dir == '':
    sys.exit("data directory has not been specified")
else:
    prepare_folder(data_dir)

data_conf['output_sel'] = output_sel

src_udp_ip = src_ip[output_sel]
src_udp_port = src_port[output_sel]

udp_ip = dst_ip[output_sel]
udp_port = dst_port[output_sel]

if output_sel % 2 == 0:
    data_conf['data_type'] = '>i2'
else:
    data_conf['data_type'] = '>u4'

# set the input of keyboard no-blocking
if data_conf['file_stop_num'] < 0:
    set_noblocking_keyboard()


# length of ID (bytes)
id_size = 4

# seprator size
sep_size = 4
payload_size = 8200
data_size = payload_size - id_size - sep_size
header_size = 28
block_size = 1024
warmup_size = 4096

data_conf['payload_size'] = payload_size
data_conf['id_size'] = id_size
data_conf['data_size'] = data_size

sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rx_buffer)

if err:
    sock.close()
    raise ValueError("set socket error")

print("Receiving IP and Port: ", udp_ip, udp_port, "Binding...")
sock.bind((udp_ip, udp_port))


executor = futures.ThreadPoolExecutor(max_workers=4)
fft_data_q = Queue()


fft_pool = Pool(max_workers)

v= RawValue('i', 0)
v.value = 0


def save_fft_data(fft_out_q, dconf, v):  #{{{
    # We need to save:
    # 1. fft_data(n_blockas_to_save, fft_npoint//2+1)
    # 2. averaged epochtime,  (t0_time + t1_time)
    # 3. the first ID of raw data frame and the last ID of raw data frame

    n_blocks_to_save = dconf['n_blocks_to_save']
    n_frames_per_loop = dconf['n_frames_per_loop']
    quantity = dconf['quantity']
    file_stop_num = dconf['file_stop_num']
    fft_npoint = dconf['fft_npoint']
    avg_n = dconf['avg_n']
    file_prefix = labels[dconf['output_sel']]


    nn = 0
    file_cnt = 0
    file_path_old = ''

    loop_forever = True
    wstart = False

    fft_data_to_file = np.zeros((n_blocks_to_save, fft_npoint//2+1))
    fout = ''

    while loop_forever:
        fft_data, ids, ide, block_time = fft_out_q.get()
        if nn == 0:
            file_block_time = block_time
            file_path = data_file_prefix(data_dir, file_block_time)
            if file_path_old =='':
                file_path_old = file_path
            fout = os.path.join(file_path, file_prefix +
                    '_' + str(file_cnt))

        fft_out = np.mean(fft_data.reshape(-1,avg_n, fft_npoint//2+1),
                    axis=1)

        ngrp = fft_out.shape[0]

        if nn ==0:
            fft_id_to_file = np.zeros((n_blocks_to_save//ngrp, 2), dtype=np.uint32)
            fft_block_time_to_file = np.zeros((n_blocks_to_save//ngrp,),
                    dtype='S30')

        fft_id_to_file[nn,0] = ids
        fft_id_to_file[nn,1] = ide

        fft_block_time_to_file[nn] = epoctime2date(block_time)
        i1 = nn*ngrp
        i2 = i1+ngrp
        fft_data_to_file[i1:i2,...] =fft_out
        nn +=1

        # if nn == n_blocks_to_save - 50:
            # if wstart:
                # wfile.result()
                # wstart = False

        # print("nn: ", nn, i2, n_blocks_to_save)
        if i2 == n_blocks_to_save:
            nn = 0

            # print("nn: ", nn, i2, n_blocks_to_save)

            # wfile = executor.submit(dumpdata_fft_hdf5, fout, fft_data_to_file,
                    # fft_id_to_file, fft_block_time_to_file)
            # wstart = True

            # f=h5.File(fout +'.h5', 'w')

            # dset = f.create_dataset(quantity, data=fft_data_to_file)
            # dset.attrs['avg_n'] = avg_n
            # dset.attrs['fft_length'] =  fft_npoint

            # dset = f.create_dataset('block_time', data=fft_block_time_to_file)
            # dset = f.create_dataset('block_ids', data=fft_id_to_file)

            # f.close()

            if file_path == file_path_old:
                file_cnt += 1
            else:
                file_cnt = 0

            file_path_old = file_path


        if file_stop_num < 0 or file_cnt <= file_stop_num:
            loop_forever = True
        else:
            loop_forever = False
            v.value = 1
            print("save fft loop ended")

   #}}}


if __name__ == '__main__':
    # Warm up the system....
    # Drop the some data packets to avoid unstable

    print("Starting rx_fft....", os.getpid())

    id_head_before = 0
    id_tail_before = 0

    warmup_data = bytearray(payload_size)
    warmup_buff = memoryview(warmup_data)

    tmp_id = 0

    print("Warming Up....")
    # Wait until the SeqNo is 1023 to start collect data, which is easy
    # to drap the data frames if one of them are lost in the transfering.

    while tmp_id % warmup_size != warmup_size - 1:
        sock.recv_into(warmup_buff, payload_size)
        tmp_id = int.from_bytes(warmup_data[payload_size-id_size:
        payload_size], 'big')

    id_tail_before = int.from_bytes(warmup_data[payload_size-id_size:
        payload_size], 'big')

    print("Warmup finished with last data seqNo: ", id_tail_before,
            tmp_id % block_size)

    t0_time = time.time()
    data_conf['id_tail_before'] = id_tail_before
    #
    # In info.h5, we need to save
    # 1. t0_time: The start time of rx_fft.py receiving.
    # 2. id_tail_before: The first ID of the data received by rx_fft.py
    # 3.

    save_meta_file(os.path.join(data_dir, 'info.h5'), t0_time, id_tail_before)

    # Saving parameters
    shutil.copy('./params.py', data_dir)

    # copy info.txt from receiver and save
    os.system("scp rec:~/info.txt " + os.path.join(data_dir, 'info_recv.txt'))

    # start a new Process to receive data from the Receiver

    n_frames_per_loop = data_conf['n_frames_per_loop']
    data_type = data_conf['data_type']

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
    thread_cnt = 0

    s_time = time.perf_counter()
    time_before = s_time
    t0_time = time.time()

    # the period of the consecutive ID is 2**32 - 1 = 4294967295
    cycle = 4294967295
    max_id = 0

    loop_ctl = True

    data_in_shape1 = data_conf['n_frames_per_loop']*data_conf['data_size']//2
    data_in = np.empty((max_workers, int(data_in_shape1)))
    compute_fft_map = partial(compute_fft, data_in,data_conf['fft_npoint'])

    ids_list = [0]*max_workers
    ide_list = [0]*max_workers
    block_time_list=[0.0]*max_workers

    # save_fft=Process(target=save_fft_data, args=(fft_data_q, data_conf, v),
        # daemon=True)
    # save_fft.start()

    while loop_ctl:

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
            # data_in[thread_cnt,...] = np.frombuffer(udp_data, dtype=data_type)
            # block_time = epoctime2date((block_time1 + block_time2)/2.)
            block_time = (block_time1 + block_time2)/2.
            ids_list[thread_cnt] = id_arr[0]
            ide_list[thread_cnt] = id_arr[-1]
            block_time_list[thread_cnt] = block_time
            thread_cnt += 1

        # print("i: ",i)

        time_now = time.perf_counter()

        if i == 500:
            block_time = epoctime2date((block_time1 + block_time2)/2.)
            display_metrics(time_before, time_now, s_time, num_lost_all,
                    data_conf)
            i = 0

        time_before = time_now

        i +=1

        if thread_cnt == max_workers:
            thread_cnt = 0
        # start a new Process to save the FFT data


        # the order of averaged fft is not sequential.

        # if v.value == 0:
            # if thread_cnt == max_workers:
                # data_back = fft_pool.map(compute_fft_map, range(max_workers))
                # for d,s,e,b in zip(data_back, ids_list, ide_list, block_time_list):
                    # fft_data_q.put((d,s,e,b))
                # thread_cnt = 0

        # else:
            # loop_ctl=True
            # print("rx_fft.py will exit, clean up....\n")
            # fft_pool.terminate()


    save_fft.terminate()
    print("Save file processe was terminated")

    fft_data_q.cancel_join_thread()
    print("Clean up multiprocessing Queues.\n")

    sys.exit("rx_fft.py exited...")
