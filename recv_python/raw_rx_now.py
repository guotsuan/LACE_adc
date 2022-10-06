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
import shutil
import json
import queue
import logging
from concurrent import futures
from multiprocessing import Queue

import h5py as h5
import numpy as np

# put all configrable parameters in params.py
from params import labels, data_conf, rx_buffer, output_sel, \
    src_ip, src_port, dst_ip, dst_port, green_ok

from rx_helper import save_meta_file, display_metrics, \
    prepare_folder, set_noblocking_keyboard, read_temp, data_file_prefix, \
    epoctime2date

affinity_mask = {0, 1}
os.sched_setaffinity(0, affinity_mask)

data_dir = data_conf['data_dir']
print("-"*80)
print("recieving output type from input: ", labels[output_sel])
print("saving into the folder: ", data_dir)

prepare_folder(data_dir)

data_conf['output_sel'] = output_sel
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
cycle = 4294967295
forever = True

# set the input of keyboard no-blocking
if file_stop_num < 0:
    set_noblocking_keyboard()

# the period of the consecutive ID is 2**32 - 1 = 4294967295

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

sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rx_buffer)
sock.settimeout(2.0)

affinity_mask = {0, 1}
pid = 0
os.sched_setaffinity(0, affinity_mask)

if err:
    sock.close()
    raise ValueError("set socket error")

print("Receiving IP and Port: ", udp_ip, udp_port, "Binding..."+green_ok)
sock.bind((udp_ip, udp_port))


udp_payload = bytearray(n_frames_per_loop*payload_size)
udp_data = bytearray(n_frames_per_loop*data_size)
udp_id = bytearray(n_frames_per_loop*id_size)

payload_buff = memoryview(udp_payload)
data_buff = memoryview(udp_data)
id_buff = memoryview(udp_id)

# v= RawValue('i', 0)
file_q = Queue()


def move_file(file_q):
    loop = True
    while loop:
        try:
            file_to_move, file_dest = file_q.get(timeout=2.0)
            if os.path.exists(file_to_move):
                shutil.move(file_to_move, file_dest)
        except queue.Empty:
            print("All files have been moved. Terminate move_file queue...")
            loop = False


def dumpdata_hdf5_q4(file_name, data, id_data, block_time):

    quantity = data_conf['quantity']
    f = h5.File(file_name + '.h5', 'w')
    dset = f.create_dataset(quantity, data=data)
    temp_ps, temp_pl = read_temp(sock_temp)
    dset.attrs['temp_ps'] = temp_ps
    dset.attrs['temp_pl'] = temp_pl

    dset = f.create_dataset('block_time', data=block_time)
    dset = f.create_dataset('block_ids', data=id_data)

    f.close()

    return


def dumpdata_hdf5_q3(file_name, data, id_data, block_time, fout_dst, file_q):

    quantity = data_conf['quantity']

    f = h5.File(file_name + '.h5', 'w')
    dset = f.create_dataset(quantity, data=data)
    temp_ps, temp_pl = read_temp(sock_temp)
    dset.attrs['temp_ps'] = temp_ps
    dset.attrs['temp_pl'] = temp_pl

    dset = f.create_dataset('block_time', data=block_time)
    dset = f.create_dataset('block_ids', data=id_data)

    f.close()

    file_q.put((file_name +'.h5', fout_dst +'.h5'))

    return


if __name__ == '__main__':
    # Warm up the system....
    # Drop the some data packets to avoid unstable

    print("Starting....")
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
        try:
            sock.recv_into(warmup_buff, payload_size)
        except socket.timeout:
            print("Socket recieving warmup data timeout...  exited...")
            sock.close()
            sys.exit(1)

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

    try:
        sock_temp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    except socket.error as msg:
        logging.warning("socket of reading temp is failed to open")
        logging.warning(msg)

    i = 0
    file_cnt = 0
    tot_file_cnt = 0
    loop_cnt = 0
    fft_block_cnt = 0

    s_time = time.perf_counter()
    time_before = s_time
    t0_time = time.time()
    time_last = time.perf_counter()

    # FIXME: how to save time xxxxxx.xxxx properly
    save_meta_file(os.path.join(data_dir, 'info.h5'), t0_time,
                   id_tail_before,
                   data_conf)
    # Saveing parameters
    shutil.copy('./params.py', data_dir)
    file_path_old = data_file_prefix(data_dir, t0_time, data_conf)

    executor = futures.ThreadPoolExecutor(max_workers=1)

    mem_dir = '/dev/shm/recv/'
    if not os.path.exists(mem_dir):
        os.makedirs(mem_dir )

    # file_move=Process(target=move_file, args=(file_q,))
    # file_move.start()

    json_data_conf = os.path.join(data_dir,'data_conf.json')
    with open(json_data_conf, 'w') as f:
        json.dump(data_conf, f, sort_keys=True, indent=4,
                  separators=(',',': '))

    print("   ")
    print("Time of single loop     Total lost packets    Elapsed time   Speed \
           Num of saved file\n")

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
                # raise ValueError("block is not connected")

            # update the ids before for next section
            id_head_before = id_arr[0]
            id_tail_before = id_arr[-1]

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
                print(id_arr[bad-1:bad+2])
                num_lost_all += num_lost_p
            else:
                no_lost = True


            #######################################################################
            #                            saving data                              #
            #######################################################################

            if data_conf['loop_file']:
                k = file_cnt % data_conf['loop_file_num']
            else:
                k = file_cnt


            if no_lost:
                file_path = data_file_prefix(data_dir, block_time, data_conf)
                fout = os.path.join(file_path, labels[output_sel] +
                        '_' + str(k))

                mem_fout = os.path.join(mem_dir, file_prefix +
                        '_' + str(k))

                block_time_str = epoctime2date(block_time)

                wfile = executor.submit(dumpdata_hdf5_q4, fout, udp_payload_arr,
                        id_arr, block_time_str)

                # wfile = executor.submit(dumpdata_hdf5_q3, mem_fout, udp_payload_arr,
                        # id_arr, block_time_str, fout,
                                        # file_q)

                if file_path == file_path_old:
                    file_cnt += 1
                else:
                    file_cnt = 0

                file_path_old = file_path
                tot_file_cnt += 1

            else:
                print("block is dropped")
                logging.warning("block is dropped")



            #######################################################################
            #                           information out                           #
            #######################################################################
            time_now = time.perf_counter()

            if time_now - time_last > 10.0:

                time_last = time.perf_counter()
                # display_metrics(time_before, time_now, s_time, num_lost_all,
                        # data_conf)
                display_metrics(time_before, time_now, s_time, num_lost_all,
                        data_conf, tot_file_cnt=tot_file_cnt)
                i = 0

            time_before = time_now

            if (file_stop_num > 0) and (tot_file_cnt >= file_stop_num) :
                forever = False

            i += 1

        print("Process save fft ended")
        executor.shutdown(wait=False, cancel_futures=True)
        logging.warning("Process save fft ended")
        # file_move.join()
        sock.close()

    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        sock.close()

