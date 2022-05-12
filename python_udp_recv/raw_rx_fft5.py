#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
DAC RAW data sampling output after ffting
Method: save single frame data

n_frames_per_loop = 8192 is tested

Switch to max_workers to 1, and it seems working

data stored in cuda, transfer to host once.

There is no delay in block_time in saving

"""

import socket
import sys
import os
import time
import datetime
import shutil
from concurrent import futures
from multiprocessing import RawValue, Process, SimpleQueue

# import h5py as h5
import numpy as np
import cupy as cp
#import termios, fcntl

# put all configrable parameters in params.py
from params import *
from rx_helper import *

data_dir = ''
good = 0
output_sel = -1
file_path = ''
file_path_old =''

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
scale_f = data_conf['voltage_scale_f']

src_udp_ip = src_ip[output_sel]
src_udp_port = src_port[output_sel]

udp_ip = dst_ip[output_sel]
udp_port = dst_port[output_sel]

if output_sel % 2 == 0:
    data_type = '>i2'
else:
    data_type = '>u4'

n_frames_per_loop = data_conf['n_frames_per_loop']
n_blocks_to_save = data_conf['n_blocks_to_save']
quantity = data_conf['quantity']
file_stop_num = data_conf['file_stop_num']
file_prefix = labels[data_conf['output_sel']]

# set the input of keyboard no-blocking
if file_stop_num < 0:
    set_noblocking_keyboard()

# the period of the consecutive ID is 2**32 - 1 = 4294967295
cycle = 4294967295
max_id = 0
forever = True

# length of ID (bytes)
id_size = 4

# seprator size
sep_size = 4
payload_size = 8200
header_size = 28
block_size = 1024
warmup_size = 4096

num_lost_all = 0.0

data_conf['payload_size'] = payload_size
data_conf['id_size'] = id_size
data_size = payload_size - id_size - sep_size
data_conf['data_size'] = data_size
fft_length = data_conf['fft_npoint']
avg_n = data_conf['avg_n']

dur_per_frame = data_size/sample_rate_over_100/2.0

sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rx_buffer)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

affinity_mask = {2,3}
pid = 0
os.sched_setaffinity(0, affinity_mask)

#os.setpriority(os.PRIO_PROCESS, 0, 0)
# psutil.Process().nice(-20)


if err:
    sock.close()
    raise ValueError("set socket error")

print("Receiving IP and Port: ", udp_ip, udp_port, "Binding...")
sock.bind((udp_ip, udp_port))


udp_payload = bytearray(n_frames_per_loop*payload_size)
udp_data = bytearray(n_frames_per_loop*data_size)
udp_id = bytearray(n_frames_per_loop*id_size)

payload_buff = memoryview(udp_payload)
data_buff = memoryview(udp_data)
id_buff = memoryview(udp_id)

v= RawValue('i', 0)
file_q = SimpleQueue()
v.value = 0
nn = 0
file_cnt = 0
tot_file_cnt = 0

ngrp = int(n_frames_per_loop*data_size/avg_n/2/fft_length)

fft_block_time_to_file = np.zeros((n_blocks_to_save,), dtype='S30')
fft_data_to_file = cp.zeros((n_blocks_to_save, fft_length//2+1))
fft_id_to_file = np.zeros((n_blocks_to_save, n_frames_per_loop), dtype=np.uint32)

def move_file(file_q, v):
    # pid = 0
    # os.sched_setaffinity(0, {11})

    loop = True
    while loop:
        file_to_move, file_dest = file_q.get()
        if os.path.exists(file_to_move):
            shutil.move(file_to_move, file_dest)
        if v.value == 1:
            loop = False


def dumpdata_hdf5_fft_q5(data_dir, mem_dir, data, id_data, file_q):

    global nn
    global ngrp
    global file_cnt
    global file_prefix
    global tot_file_cnt
    global output_sel, file_path, file_path_old

    global fft_block_time_to_file
    global fft_data_to_file
    global fft_id_to_file

    # print("save raw pid: ", os.getpid())


    avg_n = data_conf['avg_n']
    fft_npoint = data_conf['fft_npoint']
    scale_f = data_conf['voltage_scale_f']
    quantity = data_conf['quantity']
    n_blocks_to_save = data_conf['n_blocks_to_save']
    # start_time = data_conf['t0_time']

    global plan

    try:
        data_in = cp.asarray(scale_f *data).astype(cp.float32).reshape(-1, avg_n,
                                                                    fft_npoint)
        if plan is None:
            plan = cufft.get_fft_plan(data_in, axes=2, value_type='R2C')

        fft_out = cufft.rfft(data_in, axis=2, plan=plan)

        if quantity == 'amplitude':
            mean_out = cp.mean(cp.abs(fft_out), axis=1)
        elif quantity == 'power':
            mean_out = cp.mean(cp.abs(fft_out)**2, axis=1)
        else:
            print("wrong")

        i1 = nn*ngrp
        i2 = i1+ngrp
        fft_data_to_file[i1:i2,...] = mean_out
        fft_block_time_to_file[i1:i2] = epoctime2date(block_time)
        nn += 1


        if i2 == n_blocks_to_save:
            nn = 0

            if loop_file:
                k = file_cnt % 20
            else:
                k = file_cnt

            # print("epoch: ", epoctime2date(block_time))
            file_path = data_file_prefix(data_dir, block_time)
            fout = os.path.join(file_path, labels[output_sel] +
                    '_' + str(k))

            mem_fout = os.path.join(mem_dir, file_prefix +
                    '_' + str(k))

            # temp_result = subprocess.getoutput('ssh rec "python readtemp.py"')
            # tmp_str=temp_result[1:-2].split(",")
            # t_ps, t_pl = [float(b) for b in tmp_str]
            f=h5.File(fout +'.h5','w')


            dset = f.create_dataset(quantity, data=fft_data_to_file.get())
            # dset.attrs['temp_ps'] = t_ps
            # dset.attrs['temp_pl'] = t_pl
            dset = f.create_dataset('block_time', data=fft_block_time_to_file)
            dset = f.create_dataset('block_ids', data=fft_id_to_file)

        # # # dset = f.create_dataset(quantity, data=cp.asnumpy(mean_out))

            f.close()

            file_q.put((mem_fout +'.h5', fout +'.h5'))

            if file_path == file_path_old:
                file_cnt += 1
            else:
                # logging.info("new file dir: " + fout)
                # logging.info("block time: " + epoctime2date(block_time))
                file_cnt = 0

            tot_file_cnt += 1
            file_path_old = file_path
    except:
        v.value = 1
        raise ("dumpdata_hdf5_fft_q5 error")


    return



if __name__ == '__main__':
    # Warm up the system....
    # Drop the some data packets to avoid unstable

    print("Starting....\n")
    payload_buff_head = payload_buff

    pstart = False
    fft_file_save = False


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
            tmp_id % block_size, "\n")

    logfile = os.path.join(data_dir, 'rx.log')
    logging.basicConfig(filename=logfile, level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Warmup finished with last data seqNo: %i, %i ", id_tail_before,
            tmp_id % block_size)
    i = 0
    loop_cnt = 0
    fft_block_cnt = 0

    s_time = time.perf_counter()
    time_before = s_time
    t0_time = time.time()
    start_time = datetime.datetime.utcfromtimestamp(t0_time)

    time_last = time.perf_counter()

    # FIXME: how to save time xxxxxx.xxxx properly
    data_conf['id_tail_before'] = id_tail_before
    data_conf['t0_time'] = t0_time
    start_id = id_tail_before
    save_meta_file(os.path.join(data_dir, 'info.h5'), t0_time, id_tail_before)
    # Saveing parameters
    shutil.copy('./params.py', data_dir)
    file_path_old = data_file_prefix(data_dir, t0_time)

    executor = futures.ThreadPoolExecutor(max_workers=1)

    mem_dir = '/dev/shm/recv/'
    if not os.path.exists(mem_dir):
        os.makedirs(mem_dir )

    file_move=Process(target=move_file, args=(file_q,  v),
                      daemon=True)
    file_move.start()


    try:
        while forever:
            if file_stop_num < 0:
                try:
                    c = sys.stdin.read(1)
                    if c =='x':
                        print("program will stop on given order")
                        forever = False
                except IOError: pass

            pi1 = 0
            pi2 = data_size

            hi1 = 0
            hi2 = id_size

            count_down = n_frames_per_loop
            payload_buff = payload_buff_head
            block_time1 = time.time()
            no_lost = False

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
                udp_payload_arr = np.frombuffer(udp_data, dtype=data_type)
                id_offsets = np.diff(id_arr) % cycle

                idx = id_offsets > 1

                num_lost_p = len(id_offsets[idx])
                block_time = (block_time1 + block_time2)/2.
                if (num_lost_p > 0):
                    if data_conf['save_lost']:
                        no_lost = True
                    else:
                        no_lost = False

                    bad=np.arange(id_offsets.size)[idx][0]
                    logging.warning("inside block is not continuis")
                    logging.warning(id_arr[bad-1:bad+2])
                    num_lost_all += 1
                else:
                    wfile = executor.submit(dumpdata_hdf5_fft_q5,
                                        data_dir, mem_dir, udp_payload_arr, id_arr, file_q)


                    # dumpdata_hdf5_fft_q4(data_dir, mem_dir, udp_payload_arr, id_arr, file_q)
            else:
                logging.warning("block is not connected, %i, %i", id_tail_before, id_arr[0])
                num_lost_all += 1
                no_lost = False

            # update the ids before for next section
            id_head_before = id_arr[0]
            id_tail_before = id_arr[-1]



            #######################################################################
            #                            saving data                              #
            #######################################################################



            #######################################################################
            #                           information out                           #
            #######################################################################
            time_now = time.perf_counter()

            if time_now - time_last > 10.0:

                time_last = time.perf_counter()
                display_metrics(time_before, time_now, s_time, num_lost_all,
                        data_conf, tot_file_cnt=tot_file_cnt)

            time_before = time_now

            if (file_stop_num > 0) and (tot_file_cnt > file_stop_num) :
                forever = False
                v.value = 1

        # file_move.terminate()
        print("start finishing job....")
        executor.shutdown(wait=False, cancel_futures=True)
        print("Process save fft ended")
        logging.warning("Process save fft ended")
        sock.close()
    except KeyboardInterrupt:
        # file_move.terminate()
        executor.shutdown(wait=False, cancel_futures=True)
        sock.close()

