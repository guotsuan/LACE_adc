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
import threading
from multiprocessing import Process

import h5py as h5
import numpy as np
import termios, fcntl


# put all configrable parameters in params.py
from params import *
from rx_helper import dumpdata,set_noblocking_keyboard,prepare_folder,\
        data_file_prefix


data_dir = ''


args_len = len(sys.argv)
if args_len < 3:
    print("python rx.py <rx_type> <data_dir> ")
    sys.exit()

elif args_len == 3:
    try:
        args = sys.argv[1].split()
        input_type = int(args[0])

        data_dir = sys.argv[2]
        output_type = input_type
    except:
        print("input type must be one of 0,1,2,3")

    if output_type > 3:
        print("input type", input_type, " must be one of 0,1,2,3")
        sys.exit()
    else:
        print("recieving output type from input: ", labels[output_type])
        print("saving into the folder: ", data_dir)


if data_dir == '':
    sys.exit("data directory has not been specified")
else:
    prepare_folder(data_dir)


src_udp_ip = src_ip[output_type]
src_udp_port = src_port[output_type]

udp_ip = dst_ip[output_type]
udp_port = dst_port[output_type]

if output_type % 2 == 0:
    data_type = '>i2'
    fft_data = False
else:
    data_type = '>u4'
    fft_data = True


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
data_size = payload_size - id_size - sep_size
header_size = 28
block_size = 1024
warmup_size = 4096

num_lost_all = 0.0

sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rx_buffer)

if err:
    sock.close()
    raise ValueError("set socket error")

print("Receiving IP and Port: ", udp_ip, udp_port, "Binding...")
sock.bind((udp_ip, udp_port))


udp_payload = bytearray(counts_to_save*payload_size)
udp_data = bytearray(counts_to_save*data_size)
udp_id = bytearray(counts_to_save*id_size)

payload_buff = memoryview(udp_payload)
data_buff = memoryview(udp_data)
id_buff = memoryview(udp_id)


if __name__ == '__main__':
    # Warm up the system....
    # Drop the some data packets to avoid unstable

    print("Starting....")
    payload_buff_head = payload_buff

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

    i = 0
    file_cnt = 0

    s_time = time.perf_counter()
    time_before = s_time
    t0_time = time.time()

    file_path_old = data_file_prefix(data_dir, t0_time)
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

        count_down = counts_to_save
        payload_buff = payload_buff_head
        block_time = time.time()

        while count_down:
            sock.recv_into(payload_buff, payload_size)
            data_buff[pi1:pi2] = payload_buff[0:data_size]
            id_buff[hi1:hi2] = payload_buff[payload_size - id_size:payload_size]

            pi1 += data_size
            pi2 += data_size
            hi1 += id_size
            hi2 += id_size

            count_down -= 1

        id_arr = np.int32(np.frombuffer(udp_id,dtype='>u4'))

        diff = id_arr[0] - id_tail_before
        if (diff == 1) or (diff == - cycle ):
            pass
        else:
            print("block is not connected", id_tail_before, id_arr[0])
            print("program last ", time.time() - s_time)
            # raise ValueError("block is not connected")

        # update the ids before for next section
        id_head_before = id_arr[0]
        id_tail_before = id_arr[-1]

        udp_payload_arr = np.frombuffer(data_buff, dtype=data_type)
        id_offsets = np.diff(id_arr) % cycle

        # sample_rate = 480e6
        # one_sample_size = 2
        # size_of_data_per_sec = sample_rate * 2
        # acq_data_size = count * payload_size
        # duration  = acq_data_size / size_of_data_per_sec * 1.0

        idx = id_offsets > 1

        num_lost_p = len(id_offsets[idx])
        if (num_lost_p > 0):
            if save_lost:
                no_lost = True
            else:
                no_lost = False

            bad=np.arange(id_offsets.size)[idx][0]
            print(id_arr[bad-1:bad+2])
            num_lost_all += num_lost_p
        else:
            no_lost = True


        # FIXME: how to export data

        if loop_file:
            k = file_cnt % 4
        else:
            k = file_cnt

        if  no_lost :
            file_path = data_file_prefix(data_dir, block_time)
            if save_hdf5:
                fout = os.path.join(file_path, labels[output_type] +
                        '_' + str(k) + '.h5')

            else:
                fout = './out_' + str(k) + '.npy'

            nsample = payload_size * counts_to_save
            if 'Darwin' not in platform_system:
                writefile = Process(target=dumpdata,
                        args=(fout,udp_payload_arr, id_arr, t0_time, block_time,
                            num_lost_p, save_hdf5))
                writefile.start()
            else:
                # dumpdata(fout, udp_payload_arr, c_time, t1_time, nsample, False)
                pass

            if file_path == file_path_old:
                file_cnt += 1
            else:
                file_cnt = 0

            file_path_old = file_path


        if no_lost:
            i += 1
        else:
            print("file not saved")

        time_now = time.perf_counter()
        if (file_stop_num > 0) and (i > file_stop_num) :
            forever = False

        if i % 100 == 0:

            sample_rate = 480e6
            size_of_data_per_sec = sample_rate * 2
            acq_data_size = counts_to_save * payload_size
            duration  = acq_data_size / size_of_data_per_sec * 1.0

            acq_time = time_now - time_before

            print(f"block loop time: {time_now - time_before:.3f},", \
                    " lost_packet:", num_lost_all, \
                    num_lost_all/(i+1)/block_size, \
                    f"already run: {time_now - s_time:.3f}")

            print("The speed of acquaring data: " +
                    f'{acq_data_size/1024/1024/acq_time:.3f} MB/s\n')

        time_before = time_now




    sock.close()
