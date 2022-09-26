#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
DAC RAW data sampling output after ffting
Method: group multiple frame data and save once
change max_workers = 1 is working, will lose 2 times with file_num = 20000

The block_time is delayed in saving file, don't why yet

"""

import socket
import sys
import os
import time
import datetime
import shutil
from concurrent import futures
from multiprocessing import RawValue, Process, SimpleQueue, Queue, Pipe

import numpy as np
#import termios, fcntl

# import cupyx.scipy.fft as cufft

# put all configrable parameters in params.py
from params import *
from rx_helper import *

data_dir = ''
single_plot = True
good = 0

affinity_mask = {0,1}
pid = 0
os.sched_setaffinity(0, affinity_mask)
# os.setpriority(os.PRIO_PROCESS, 0, 0)

args_len = len(sys.argv)
if args_len < 2:
    print("python " + sys.argv[0] + " <rx_type>")
    sys.exit()

elif args_len == 2:
    waterf = False
    try:
        args = sys.argv[1].split()
        input_type = int(args[0])

        output_sel = input_type
    except:
        print("input type must be one of 0,1,2,3")

    if output_sel > 3:
        print("input type", input_type, " must be one of 0,1,2,3")
        sys.exit()
    else:
        print("display output type from input in real time: ", labels[output_sel])

elif args_len == 3:
    try:
        args = sys.argv[1].split()
        input_type = int(args[0])
        waterf = True
        output_sel = input_type
    except:
        print("input type must be one of 0,1,2,3")

    if output_sel > 3:
        print("input type", input_type, " must be one of 0,1,2,3")
        sys.exit()
    else:
        print("display output type from input in real time: ", labels[output_sel])



fft_data_rec = ''
old_fft_data_rec = ''
waterfall_data = ''
mean_fft_data = ''
gnn = 0
wnn = 0
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


# dur_per_frame = avg_n * data_size/sample_rate_over_100/2.0

sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM, socket.IPPROTO_UDP)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rx_buffer)
err = sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
# sock.setblocking(False)



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
tot_file_cnt=RawValue('i', 0)
file_q, tx = Pipe()

v.value = 0
nn = 0

ngrp = int(n_frames_per_loop*data_size/avg_n/2/fft_length)
print("ngrp: ", ngrp)

def save_fft_data(fft_out_q, dconf, v, tot):  #{{{
    # We need to save:
    # 1. fft_data(n_blockas_to_save, fft_npoint//2+1)
    # 2. averaged epochtime,  (t0_time + t1_time)
    # 3. the first ID of raw data frame and the last ID of raw data frame

    # pid = 0
    # os.sched_setaffinity(0, {8})


    import matplotlib.pyplot as plt
    import matplotlib
    from matplotlib.animation import FuncAnimation
    from scipy.fft import rfftfreq
    from fft_helper import fft_to_dBm
    from matplotlib.widgets import Button
    from scipy.signal import resample
    from scipy.interpolate import interp1d


    global mean_fft_data

    # matplotlib.use('qt5agg')

    fft_length = dconf['fft_npoint']
    fft_single_time = dconf['fft_single_time']
    # fig, (ax, ) = plt.subplots(2, 1, sharex=False,
                                  # gridspec_kw={'height_ratios': [1,1.5]})
    fig, ax = plt.subplots()
    fig.set_size_inches(8,6)
    plt.subplots_adjust(top=0.95, bottom=0.15, hspace=0.0)

    print("fft_length: ", fft_length)

    # plt.style.use('fivethirtyeight')

    sample_rate = 480.
    px = rfftfreq(fft_length, d=1/sample_rate)

    class Index:
        avg_num = 1
        single_plot = True
        ghost = True


        def single(self,event):
            self.avg_num = 1
            self.single_plot = True

        def incs(self, event):
            self.avg_num *= 2
            global gnn
            gnn = 0
            self.single_plot = False

        def decs(self, event):
            self.single_plot = False
            global mean_fft_data
            mean_fft_data = ''
            self.avg_num = max(self.avg_num // 2, 1)

        def ghosts(self, event):
            self.ghost = not(self.ghost)

    callback = Index()
    axs = plt.axes([0.1, 0.02, 0.15, 0.05])
    axprev = plt.axes([0.3, 0.02, 0.15, 0.05])
    axnext = plt.axes([0.5, 0.02, 0.15, 0.05])
    axghost = plt.axes([0.7, 0.02, 0.15, 0.05])


    axs = Button(axs, 'Single FFT')
    axs.on_clicked(callback.single)

    bnext = Button(axnext, 'Increase')
    bnext.on_clicked(callback.incs)

    bprev = Button(axprev, 'Decrease')
    bprev.on_clicked(callback.decs)

    bghost = Button(axghost, 'Ghosts')
    bghost.on_clicked(callback.ghosts)

    def animate(i):
        global fft_data_rec, gnn, mean_fft_data,waterfall_data,wnn
        global old_fft_data_rec
        avg_time = avg_n * fft_single_time


        if i% ngrp == 0 or isinstance(fft_data_rec, str):
            fft_data_rec, _, _ = fft_out_q.recv()

        if waterf == True:
            nsample = 1000
            if isinstance(waterfall_data, str):
                waterfall_data = np.zeros((ngrp*5, nsample)) - 100.

            if i % ngrp == 0:
                ff = interp1d(px, fft_data_rec)
                xx = np.linspace(0, px.max(), nsample)
                waterfall_data[0:ngrp,...] = fft_to_dBm(ff(xx))

            waterfall_data = np.roll(waterfall_data, 1, 0)
            # py = np.arange(ngrp*5)
            # xx,yy=np.meshgrid(px, py)
            # ax.pcolormesh(xx, yy, waterfall_data)

            ax.imshow(waterfall_data[ngrp:,...], resample=False,
                    aspect='auto',
                    interpolation='none', vmin=-120, vmax=-80)
            tick_locs = np.arange(0,nsample,100)
            tick_labels= ["{0:.0f}".format(i) for i in  242*tick_locs/nsample]
            ax.set_xticks(tick_locs)
            ax.set_xticklabels(tick_labels)
            ax.set_xlabel("Freq (Mhz)")
            ax.set_ylabel("Time")

        else:

            # ghost plotting

            if callback.single_plot:
                ax.clear()
                power_dbm = fft_to_dBm(fft_data_rec[i%ngrp,...])


                nbuff = 7
                if isinstance(old_fft_data_rec, str):
                    old_fft_data_rec = np.zeros((nbuff, fft_data_rec.shape[1])) - 500.

                alpha = 0.8
                colors = ['m', 'b', 'c', 'g', 'r', 'orange', 'y']
                if callback.ghost:
                    for ii in range(nbuff):
                        if old_fft_data_rec[ii, 0] > -200:
                            an= alpha - ii*0.02 - 0.02
                            # print(alpha)
                            ax.plot(px, old_fft_data_rec[ii,...] + 5*ii + 5,
                                    color=colors[ii], alpha=0.6)


                ax.plot(px, power_dbm, color='k', alpha=0.7)
                ax.set_title(f"avg time: {avg_time:.3f} ms, avg_n: {avg_n:d}, \
                            frame id: {i%ngrp:d}")


                old_fft_data_rec = np.roll(old_fft_data_rec,1,axis=0)
                old_fft_data_rec[0,...] = power_dbm
            else:

                if callback.avg_num <= ngrp:
                    if (i % (ngrp/callback.avg_num) == 0) or isinstance(mean_fft_data, str):
                        fft_l = fft_data_rec.shape[1]
                        nn = callback.avg_num
                        mean_fft_data = np.mean(fft_data_rec.reshape((-1,nn,fft_l)), axis=1)

                    idx = i % int(ngrp//callback.avg_num)
                    ax.clear()
                    ax.plot(px, fft_to_dBm(mean_fft_data[idx,...]), color='b', alpha=0.8)

                else:
                    fft_l = fft_data_rec.shape[1]
                    if gnn == 0:
                        mean_fft_data = np.zeros((callback.avg_num, fft_l))

                    if gnn*ngrp < callback.avg_num:
                        i1 = gnn*ngrp
                        i2 = i1+ngrp
                        mean_fft_data[i1:i2,...] = fft_data_rec
                        gnn +=1

                    if gnn*ngrp == callback.avg_num:
                        mean_data = np.mean(mean_fft_data, axis=0)
                        ax.clear()
                        ax.plot(px, fft_to_dBm(mean_data), color='b', alpha=0.8)
                        gnn = 0

                ax.set_title(f"avg time: {callback.avg_num*avg_time:.3f} ms, \
                            avg_n: {callback.avg_num*avg_n:d}, frame id {i%ngrp:d}")
            ax.set_xlim([0, 245])

            ax.set_ylim([-120, -10])
            ax.set_xlabel("Freq (Mhz)")
            ax.set_ylabel("Power (dBm)")


    ani = FuncAnimation(fig, animate, interval = 20)

    # plt.tight_layout()
    plt.show()

#}}}


if __name__ == '__main__':
    # Warm up the system....
    # Drop the some data packets to avoid unstable

    print("Starting....pid", os.getpid())
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
            tmp_id % block_size)

    # logfile = os.path.join(data_dir, 'rx.log')
    # logging.basicConfig(filename=logfile, level=logging.DEBUG,
                        # format='%(asctime)s %(levelname)s: %(message)s')
    # logging.info("Warmup finished with last data seqNo: %i, %i ", id_tail_before,
            # tmp_id % block_size)
    i = 0
    file_cnt = 0
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
    file_path_old = data_file_prefix(data_dir, t0_time)

    executor = futures.ThreadPoolExecutor(max_workers=1)
    executor_save = futures.ThreadPoolExecutor(max_workers=1)

    mem_dir = '/dev/shm/recv/'
    if not os.path.exists(mem_dir):
        os.makedirs(mem_dir )

    file_move=Process(target=save_fft_data, args=(file_q, data_conf, v,
                                                tot_file_cnt),
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
                # block_time = (block_time1 + block_time2)/2.
                block_time = block_time2
                # block_time = block_time2
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

                    executor.submit(dumpdata_hdf5_fft_q3,udp_payload_arr, id_arr,
                                    block_time, tx)
                # dumpdata_hdf5_fft_q3(udp_payload_arr, id_arr,
                                # block_time, tx)
            else:
                logging.warning("block is not connected, %i, %i", id_tail_before, id_arr[0])
                num_lost_all += 1
                no_lost = False

            # update the ids before for next section
            id_head_before = id_arr[0]
            id_tail_before = id_arr[-1]


            #######################################################################
            #                           information out                           #
            #######################################################################
            time_now = time.perf_counter()

            if time_now - time_last > 10.0:

                time_last = time.perf_counter()
                display_metrics(time_before, time_now, s_time, num_lost_all,
                        data_conf, tot_file_cnt.value)

            time_before = time_now

            if v.value == 1:
                forever = False

        file_move.join()
        file_q.close()
        tx.close()
        executor.shutdown(wait=False, cancel_futures=True)
        executor_save.shutdown(wait=False, cancel_futures=True)
        print("Process save fft ended")
        logging.warning("Process save fft ended")
        sock.close()
    except KeyboardInterrupt:
        file_move.terminate()
        file_q.close()
        tx.close()
        executor.shutdown(wait=False, cancel_futures=True)
        executor_save.shutdown(wait=False, cancel_futures=True)
        sock.close()
