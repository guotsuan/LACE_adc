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
import threading
from multiprocessing import Process

import h5py as h5
import numpy as np
import termios, fcntl

# put all configrable parameters in params.py
from params import *
from rx_helper import dumpdata

# fd = sys.stdin.fileno()

# oldterm = termios.tcgetattr(fd)
# newattr = termios.tcgetattr(fd)
# newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
# termios.tcsetattr(fd, termios.TCSANOW, newattr)

# oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
# fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)


# cycle = 49999
# cycle = 99999
# the period of the consecutive ID is 2**32 - 1 = 4294967295
cycle = 4294967295
max_id = 0

# length of ID (bytes)
id_size = 4

# seprator size
sep_size = 4
payload_size = 8200
data_size = payload_size - id_size - sep_size
header_size = 28
block_size = 1024

num_lost_all = 0.0

print("Receiving IP and Port: ", udp_ip, udp_port)
sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.bind((udp_ip, udp_port))
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rx_buffer)

if err:
    sock.close()
    raise ValueError("set socket error")



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

    # cout_down = 100
    warmup_data = bytearray(payload_size)
    warmup_buff = memoryview(warmup_data)

    tmp_id = 0

    # get 100 smaples for nothing
    while tmp_id % block_size !=1023:
        sock.recv_into(warmup_buff, payload_size)
        tmp_id = int.from_bytes(warmup_data[payload_size-id_size:
        payload_size], 'big')

    id_tail_before = int.from_bytes(warmup_data[payload_size-id_size:
        payload_size], 'big')

    print("finsih warmup: with last data seqNo: ", id_tail_before,
            tmp_id % block_size)

    i = 0
    file_cnt = 0

    s_time = time.perf_counter()
    time_before = s_time
    c_time = time.time()

    while forever:
        # try:
            # c = sys.stdin.read(1)
            # if c =='x':
                # print("program will stop on given order")
                # forever = False
        # except IOError: pass

        pi1 = 0
        pi2 = data_size

        hi1 = 0
        hi2 = id_size

        count_down = counts_to_save
        payload_buff = payload_buff_head
        t1_time = time.time()

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
            no_lost = False
            bad=np.arange(id_offsets.size)[idx][0]
            print(id_arr[bad-1:bad+2])
            num_lost_all += num_lost_p
        else:
            no_lost = True


        # print("--- %s seconds ---" % (time.time() - start_time))

        # FIXME: how to export data

        if loop_file:
            k = file_cnt % 4
        else:
            k = file_cnt
        if i % 100 ==0 and no_lost :
            fout = './out_' + str(k) + '.npy'
            nsample = payload_size * counts_to_save
            # writefile = Process(target=dumpdata,
                    # args=(fout,udp_payload_arr, c_time, t1_time, nsample, False))
            # writefile.start()
            file_cnt += 1

            print(f"{num_lost_p} packet lost, \
                    {num_lost_p/counts_to_save * 100}% of packets lost.")

        if no_lost:
            i += 1
        else:
            print("file not saved")

        time_now = time.perf_counter()
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
                    f'{acq_data_size/1024/1024/acq_time:.3f} MB/s')
        time_before = time_now


    sock.close()
