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
from multiprocessing import Queue, Process, RawValue, Lock, Pool, Pipe, \
    SimpleQueue


# put all configrable parameters in params.py
from params import *
from rx_helper import *

data_dir = ''

if not data_conf['output_fft']:
    sys.exit("wrong program, please use fft_rx.py or change output_fft to True")

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

    if output_sel % 2 == 0:
        print("input type", input_type, " must be one of 1,3")
        sys.exit()
    else:
        print("recieving output type from input: ", labels[output_sel])
        print("saving into the folder: ", data_dir)

if data_dir == '':
    sys.exit("data directory has not been specified")
else:
    prepare_folder(data_dir)

data_conf['output_sel'] = output_sel

if output_sel % 2 !=0:
    data_conf['quantity'] = 'power'

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
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

if err:
    sock.close()
    raise ValueError("set socket error")

print("Receiving IP and Port: ", udp_ip, udp_port, "Binding...")
sock.bind((udp_ip, udp_port))


executor = futures.ThreadPoolExecutor(max_workers=4)
# raw_data_q = Queue()
# raw_data_q = SimpleQueue()
# save_data_q = Queue()
# file_q = SimpleQueue()
raw_data_q, tx= Pipe(False)


v= RawValue('i', 0)
v.value = 0

def move_file(file_q, v):
    loop = True
    while loop:
        file_to_move, file_dest = file_q.get()
        shutil.move(file_to_move, file_dest)
        if v.value == 1:
            loop = False

def save_data(data_q, v, quantity):

    loop = True
    while loop:
        raw_data_to_file, raw_id_to_file, \
            raw_block_time_to_file, fout = data_q.get()

        f=h5.File(fout +'.h5', 'w')

        dset = f.create_dataset(quantity, data=raw_data_to_file)

        dset = f.create_dataset('block_time', data=raw_block_time_to_file)
        dset = f.create_dataset('block_ids', data=raw_id_to_file)

        f.close()
        if v.value == 1:
            loop = False

def save_raw_data_simple(rx, dconf, v):  #{{{
    # We need to save:
    # 1. fft_data(n_blockas_to_save, fft_npoint//2+1)
    # 2. averaged epochtime,  (t0_time + t1_time)
    # 3. the first ID of raw data frame and the last ID of raw data frame

    n_blocks_to_save = dconf['n_blocks_to_save']
    n_frames_per_loop = dconf['n_frames_per_loop']
    quantity = dconf['quantity']
    file_stop_num = dconf['file_stop_num']
    file_prefix = labels[dconf['output_sel']]
    data_size = dconf['data_size']
    id_tail_before = dconf['id_tail_before']
    pstart_id = id_tail_before
    data_type = dconf['data_type']

    dur_per_frame = data_size/sample_rate_over_100/2.0

    fft_npoints = 65536

    nn = 0
    time_last = 0.0
    file_cnt = 0
    tot_file_cnt = 0
    file_path_old = ''
    memfile_path_old = ''
    num_lost_all = 0.0
    cycle = 4294967295
    i = 0
    time_now = 0.0

    loop_forever = True

    ngrp = int(n_frames_per_loop * data_size / 2 /fft_npoints)
    print("ngrp: ", ngrp)

    udp_data = bytearray(n_frames_per_loop*data_size)
    udp_id = bytearray(n_frames_per_loop*id_size)

    udp_id_buff = memoryview(udp_id)
    udp_payload_buff = memoryview(udp_data)

    raw_data_to_file = np.zeros((n_blocks_to_save, fft_npoints//2))
    raw_id_to_file = np.zeros((n_blocks_to_save,n_frames_per_loop), dtype=np.uint32)
    raw_block_time_to_file = np.zeros((n_blocks_to_save,), dtype='S30')

    start_t0 = datetime.datetime.fromtimestamp(t0_time)

    raw_data = bytearray(payload_size)
    raw_data_buff = memoryview(raw_data)

    wstart = False

    pi1 = 0
    pi2 = data_size

    hi1 = 0
    hi2 = id_size

    i1 = 0
    i2 = 0
    count = 0
    id_arr = None
    nn = 0
    tmp_id = 0

    s_time = time.perf_counter()

    mem_dir = '/dev/shm/recv/'
    if not os.path.exists(mem_dir):
        os.makedirs(mem_dir )

    while loop_forever:
        if count == 0:
            pi1 = 0
            pi2 = data_size

            hi1 = 0
            hi2 = id_size
            time_before = time.perf_counter()

        raw_data_q.recv_bytes_into(raw_data_buff)
        udp_payload_buff[pi1:pi2] = raw_data_buff[0:data_size]
        udp_id_buff[hi1:hi2] = raw_data_buff[payload_size-4:payload_size]

        count += 1

        hi1 += id_size
        hi2 += id_size

        pi1 += data_size
        pi2 += data_size

        i += 1

        if nn == 0:
            block_time = time.time()
            file_path = data_file_prefix(data_dir, block_time)

            if file_path_old =='':
                file_path_old = file_path

            if file_path != file_path_old:
                file_cnt = 0

            if loop_file:
                k = file_cnt % 10
            else:
                k = file_cnt

            fout = os.path.join(file_path, file_prefix +
                    '_' + str(k))
            mem_fout = os.path.join(mem_dir, file_prefix +
                    '_' + str(k))



        if count == n_frames_per_loop:
            id_arr = np.uint32(np.frombuffer(udp_id, dtype='>u4'))
            udp_data_arr = np.frombuffer(udp_data, dtype=data_type)

            count = 0

            diff = id_arr[0] - id_tail_before

            if (diff == 1) or (diff == - cycle ):
                # update the ids before for next section

                id_offsets = np.diff(id_arr) % cycle
                idx = id_offsets > 1
                num_lost_p = len(id_offsets[idx])

                if id_arr[0] % 16 != 0:
                    num_lost_p = 1

                if (num_lost_p > 0):
                    bad=np.arange(id_offsets.size)[idx][0]
                    print(id_arr[bad-2:bad+3])
                    logging.debug("id numb : " + str(id_arr[bad-2:bad+3]))
                    num_lost_all += num_lost_p
                    logging.warning("fresh id %i, %i, %i, %i" ,
                                id_arr[0], id_arr[0]%16,
                                    id_arr[-1], id_arr[-1]%16)

                else:

                    i1 = nn*ngrp
                    i2 = i1 + ngrp
                    raw_data_to_file[nn*ngrp:nn*ngrp+ngrp,...] = udp_data_arr.reshape(-1, fft_npoints//2)
                    raw_id_to_file[nn,...] = id_arr

                    block_id_start_t = datetime.timedelta(milliseconds=(id_arr[0] -
                        pstart_id)*dur_per_frame)

                    dur_of_block = datetime.timedelta(milliseconds=(id_arr[-1] -
                        id_arr[0])*dur_per_frame)

                    t_frame_start = start_t0 + block_id_start_t

                    for kk in range(i1,i2):
                        raw_block_time_to_file[kk] = (t_frame_start +
                                kk*dur_of_block/ngrp).isoformat()


                    nn += 1

                    # if i2 >= (nn - 1) * ngrp:
                        # if wstart:
                            # wfile.result()
                            # wstart = False

                    # # print("nn: ", nn, i2, n_blocks_to_save)
                    if i2 == n_blocks_to_save:
                        nn = 0
                        # save_data_q.put((raw_data_to_file, raw_data_to_file,
                                         # raw_block_time_to_file, fout))
                        wfile = executor.submit(dumpdata_hdf5, fout, raw_data_to_file,
                                raw_id_to_file, raw_block_time_to_file)
                        # wfile = executor.submit(dumpdata_hdf5, mem_fout, raw_data_to_file,
                                # raw_id_to_file, raw_block_time_to_file, fout,
                                                # file_q)
                        # wstart = True
                        # np.savez(fout, power=raw_data_to_file,
                                # block_ids=raw_id_to_file,
                                # block_time=raw_block_time_to_file)

                        # f=h5.File(mem_fout +'.h5', 'w',driver="core")

                        # dset = f.create_dataset(quantity, data=raw_data_to_file)
                        # dset = f.create_dataset('block_time', data=raw_block_time_to_file)
                        # dset = f.create_dataset('block_ids', data=raw_id_to_file)

                        # f.close()


                        tot_file_cnt += 1
                        file_cnt += 1

                        file_path_old = file_path


                    if file_stop_num < 0 or tot_file_cnt <= file_stop_num:
                        loop_forever = True
                    else:
                        loop_forever = False
                        v.value = 1
                        print("save raw data loop ended")
                        return



            else:
                print("block is not connected", id_tail_before, id_arr[0])
                logging.debug("block is not connected %i, %i", id_tail_before, id_arr[0])
                num_lost_all += 1
                logging.warning("disc blocked fresh id: " + str(id_arr[0]) + " "
                            + str(id_arr[0]%16))

            id_head_before = id_arr[0]
            id_tail_before = id_arr[-1]

            if id_arr[-1] % 16 != 15:
                tmp_id = id_arr[-1]
                while tmp_id % 16 != 15:
                    raw_data_q.recv_bytes_into(warmup_buff)
                    tmp_id = int.from_bytes(warmup_data[payload_size-id_size:
                    payload_size], 'big')

                id_tail_before = tmp_id
                logging.warning("fixed tail id: %i, %i ",
                                id_tail_before, id_tail_before%16)

            time_now = time.perf_counter()

            if time_now - time_last > 10.0:
                # block_time = epoctime2date((time)
                time_last = time.perf_counter()
                display_metrics(time_before, time_now, s_time, num_lost_all,
                        data_conf)
                i = 0




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

    logfile = os.path.join(data_dir, 'rx.log')
    logging.basicConfig(filename=logfile, level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Warmup finished with last data seqNo: %i, %i ", id_tail_before,
            tmp_id % block_size)

    t0_time = time.time()
    data_conf['id_tail_before'] = id_tail_before

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

    read=Process(target=get_sample_data_simple, args=(sock, tx, data_conf, v),
        daemon=True)
    read.start()

    # start a new Process to save the FFT data

    save_raw=Process(target=save_raw_data_simple, args=(raw_data_q,
                                                        data_conf, v), daemon=True)
    save_raw.start()

    # file_move=Process(target=move_file, args=(file_q, v))
    # file_move.start()

    # save = Process(target=save_data, args=(save_data_q, v, data_conf['quantity']))
    # save.start()
    print("save_raw finshied", v.value)
    save_raw.join()

    if v.value == 1:
        print("rx_fft.py will exit, clean up....\n")
        sys.exit("rx_fft.py exited...")

    read.join()

