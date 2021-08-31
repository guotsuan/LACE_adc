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

fd = sys.stdin.fileno()

oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)


src_udp_ip = "192.168.90.20"
src_udp_port = 59000

udp_ip = "192.168.90.100"
udp_port = 60000

# cycle = 49999
cycle = 2 ** 32
save_per_file = 1000
loop_file=True
output_fft = True
udp_raw = False
max_id = 0

sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
# sock = socket.socket(socket.AF_INET,  socket.SOCK_RAW, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1073741824)
# err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 3147584)

# sock.setblocking(True)
# err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
if err:
    raise ValueError("set socket error")

sock.bind((udp_ip, udp_port))

count = 1000

payload_size = 8200
data_size = payload_size - 8
header_size = 28
id_size = 4
packet_size = payload_size + header_size

udp_payload = bytearray(count*payload_size)
udp_data = bytearray(count*data_size)
udp_id = bytearray(count*id_size)

payload_buff = memoryview(udp_payload)
data_buff = memoryview(udp_data)
id_buff = memoryview(udp_id)


num_lost_all = 0.0
forever = True

# def terminate():
    # try:
        # # while 1:
        # try:
            # c = sys.stdin.read(1)
            # if c:
                # print("dog", repr(c))
        # except IOError: pass
    # finally:
        # termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        # fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

def dumpdata(file_name, data, stime, t1, ns, hdf5=False, header=None):

    if hdf5:
        f=h5.File(file_name,'w')
        dset = f.create_dataset('voltage', data=data)
        dset.attrs['start_time'] = stime
        dset.attrs['unit'] = 'V'
        dset.attrs['offset_time'] = t1
        dset.attrs['nsample'] = t1
        f.close()

    # np.save('/dev/shm/' + file_name, data)
    # ff = h5.File(file_name, 'w')
    # ff.create_dataset('voltage', data=data )
    # ff.close()

if __name__ == '__main__':
    # Warm up the system....
    # Drop the fist data frame to avoid unstable

    payload_buff_head = payload_buff

    id_head_before = 0
    id_tail_before = 0

    cout_down = 100
    warmup_data = bytearray(payload_size)
    warmup_buff = memoryview(warmup_data)

    # get 100 smaples for nothing
    while cout_down:
        sock.recv_into(warmup_buff, payload_size)
        cout_down -= 1


    id_tail_before = int.from_bytes(warmup_data[payload_size -4:payload_size], 
            'big')
    
    print("finsih warmup: with last data seqNo: ", id_tail_before)
    
    i = 0
    file_cnt = 0

    s_time = time.perf_counter()
    time_before = s_time
    c_time = time.time()

    while forever:
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

        count_down = count
        payload_buff = payload_buff_head
        t1_time = time.time()
        while count_down:
            sock.recv_into(payload_buff, payload_size)
            data_buff[pi1:pi2] = payload_buff[0:data_size]
            id_buff[hi1:hi2] = payload_buff[payload_size-4:payload_size]
            payload_buff = payload_buff[payload_size:]

            pi1 += data_size
            pi2 += data_size
            hi1 += id_size
            hi2 += id_size

            count_down -= 1

        id_arr = np.int32(np.frombuffer(udp_id,dtype='>u4'))
        # sys.exit()

        if id_arr[0] - id_tail_before == 1:
            pass
        else:
            print("block is not connected", id_tail_before, id_arr[0])
            print("program last ", time.time() - s_time)
            # raise ValueError("block is not connected")

        id_head_before = id_arr[0]
        id_tail_before = id_arr[-1]

        id_offsets = np.diff(id_arr) % cycle

        no_lost = True

        # if (np.sum(id_offsets) - count // 2) < 2:
            # if np.sum(np.diff(id_offsets)) == 0:
                # no_lost = True

        udp_payload_arr = np.frombuffer(data_buff, dtype='>i2')

        # sample_rate = 480e6
        # one_sample_size = 2
        # size_of_data_per_sec = sample_rate * 2
        # acq_data_size = count * payload_size
        # duration  = acq_data_size / size_of_data_per_sec * 1.0


        # if not no_lost:
            # print("program last ", time.time() - s_time)
            # raise ValueError("sampleing is not continues")


        idx = id_offsets > 1

        num_lost_p = len(id_offsets[idx])
        if (num_lost_p >0):
            # sys.exit()
            bad=np.arange(id_offsets.size)[idx][0]
            # np.save("testc.npy", udp_payload_arr[(bad-1)*data_size//2:
                # (bad+2)*data_size//2])
            print(id_arr[bad-1:bad+2])
            num_lost_all += num_lost_p
            # sys.exit()
        # print(f"{num_lost_p} packet lost, {num_lost_p/count * 100}% of packets lost.")

        # print("--- %s seconds ---" % (time.time() - start_time))
        
        if loop_file:
            k = file_cnt % 4
        else:
            k = file_cnt
        # if i % 1000 ==0 and no_lost :
            # fout = '/dev/shm/out_' + str(k) +'.h5'
            # nsample = payload_size * count
            # writefile = Process(target=dumpdata,
                    # args=(fout,udp_payload_arr, c_time, t1_time, nsample, True))
            # writefile.start()
            # file_cnt += 1
        # # fout=h5.File(fout, 'w')
        # # fout.create_dataset('voltage', data=udp_payload_arr)
        # # fout.close()

        # # time.sleep(0.08)

        if no_lost:
            i += 1
        else:
            print("file not saved")
        time_now = time.perf_counter()
        # if i % 100 == 0:
        # print(f"block loop time: {time_now - time_before:.3f},", " lost_packet:", \
                # num_lost_all, num_lost_all/i/8192, f"already run: {time_now - s_time:.3f}")
        time_before = time_now
        # print(max_id)


    sock.close()
