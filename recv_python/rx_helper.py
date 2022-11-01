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
import mkl_fft
import rich
from rich.table import Table
from scipy.fft import rfft,rfftfreq
import shutil
import logging
import subprocess
from multiprocessing import shared_memory

import cupyx.scipy.fft as cufft


sys.path.append('../')
from gps_and_oscillator.check_status import get_gps_coord

plan = None


def read_temp(sock):
    msgFromClient       = "Hello Receiver Temp Server"
    bytesToSend         = str.encode(msgFromClient)
    serverAddressPort   = ("192.168.1.188", 20001)
    bufferSize          = 1024

    sock.settimeout(2.0)

    try:
        sock.sendto(bytesToSend, serverAddressPort)
        msgFromServer =sock.recvfrom(bufferSize)

        temp_ps, temp_pl = np.frombuffer(msgFromServer[0], dtype='<f4')
    except:
        print("Reading temp error")
        temp_ps = -1.0
        temp_pl = -1.0
        logging.warning("Reading temp error")

    return temp_ps, temp_pl


def save_meta_file(fname, stime, s_id, data_conf):
    ff = h5.File(fname, 'w')
    str_stime = epoctime2date(stime)
    ff.create_dataset('start_time', data=str_stime, dtype='S30')
    ff.create_dataset('time zone', data='utc')
    ff.create_dataset('version', data=0.5)
    ff.create_dataset('id_start', data=s_id)
    ff.create_dataset('file_stop_num', data=data_conf['file_stop_num'])

    # loc = get_gps_coord()
    # if loc is not None:
        # print("saving locattion")
        # ff.create_dataset('location', data=loc)

    ff.close()

def display_metrics_header() -> Table:
    style = "bold white on blue"
    table = Table(title="Collecting data...", style=style, width=100)
    table.add_column("Time of the loop", style=style)
    table.add_column("Total lost packets", style=style)
    table.add_column("Elapsed time", style=style)
    table.add_column("Transfer Speed", style=style)
    table.add_column("Num of file saved", style=style)
    table.add_row("", "", "", "", "")
    return table

def display_metrics_rich(time_before,time_now, s_time, num_lost_all, dconf,
                    tot_file_cnt=None) -> Table:
    sample_rate = dconf['sample_rate']
    n_frames_per_loop = dconf['n_frames_per_loop']
    payload_size = dconf['payload_size']

    size_of_data_per_sec = sample_rate * 2  # 2 byte times 480e6 points/s
    acq_data_size = n_frames_per_loop * payload_size
    # duration  = acq_data_size / size_of_data_per_sec * 1.0
    acq_time = time_now - time_before

    style="bold white on blue"
    table = Table(title="Collecting data...", style=style, width=100)
    table.add_column("Time of the loop", style=style)
    table.add_column("Total lost packets", style=style)
    table.add_column("Elapsed time", style=style)
    table.add_column("Transfer Speed", style=style)
    table.add_column("Num of file saved", style=style)

    table.add_row(f"{time_now - time_before:.3f} s",
                  f"{num_lost_all:.3f}",
                  f"{time_now - s_time:.3f} s",
                  f'{acq_data_size/1024/1024/acq_time:.3f} MB/s' ,
                  f'{tot_file_cnt:d}'
                  )

    return table

def display_metrics(time_before,time_now, s_time, num_lost_all, dconf,
                    tot_file_cnt=None):

    sample_rate = dconf['sample_rate']
    n_frames_per_loop = dconf['n_frames_per_loop']
    payload_size = dconf['payload_size']

    size_of_data_per_sec = sample_rate * 2  # 2 byte times 480e6 points/s
    acq_data_size = n_frames_per_loop * payload_size
    # duration  = acq_data_size / size_of_data_per_sec * 1.0
    acq_time = time_now - time_before

    # os.system("clear")

    print ("\033[A                                                                                         \033[A")
    print(f"{time_now - time_before:.3f} s, \t\t      ", num_lost_all, \
          f"\t\t{time_now - s_time:.3f} s", \
          f'    {acq_data_size/1024/1024/acq_time:.3f} MB/s, ' \
          f'    {tot_file_cnt:d}')

    # if tot_file_cnt is not None:
        # print("The speed of acquaring data: " +
              # f'{acq_data_size/1024/1024/acq_time:.3f} MB/s, ' +
              # "The number of total files saved: " + f'{tot_file_cnt:d}\n')
    # else:
        # print("The speed of acquaring data: " +
                # f'{acq_data_size/1024/1024/acq_time:.3f} MB/s\n')


    # logging.info(f"frame loop time: {time_now - time_before:.3f}," + \
            # " lost_packet:" + str(num_lost_all) + \
            # f" already run: {time_now - s_time:.3f}")
    # logging.info("The speed of acquaring data: " + \
                 # f'{acq_data_size/1024/1024/acq_time:.3f} MB/s')

def prepare_folder(indir):
    isdir = os.path.isdir(indir)
    if isdir:
        files = os.listdir(indir)
        if len(files) != 0:
            # raise ValueError(indir + ' is not empty')
            print("clear diretory.....\n")
            shutil.rmtree(indir)
            os.mkdir(indir)

    else:
        os.mkdir(indir)


def data_file_prefix(indir, stime, data_conf, unpack=False):

    if type(stime) != datetime.datetime:
        if isinstance(stime, float):
            dt = datetime.datetime.utcfromtimestamp(stime)
        else:
            dt = datetime.datetime.fromisoformat(stime)
    else:
        dt = stime

    folder_level1 = dt.strftime("%Y-%m-%d")
    folder_level2 = dt.strftime("%H")
    if data_conf['split_by_min']:
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

def compute_fft_data2(data, fft_length, scale_f, quantity, mean=True,
                      fft_method=''):
    if mean:
        fft_in_data = scale_f*data.reshape((-1,fft_length))
        print("fft_in_data shape: ",fft_in_data.shape)
    else:
        fft_in_data = scale_f*data

    if fft_method == 'cupy':
        fft_in_data = cp.array(fft_in_data)
        if quantity == 'amplitude':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())
        elif quantity == 'power':
            mean_fft_result = np.abs(cp.fft.rfft(fft_in_data).get())**2,

        if mean:
            mean_fft_result = np.mean(mean_fft_result, axis=0)
    elif fft_method == 'mkl_fft':
        if quantity == 'amplitude':
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))
            # mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif quantity == 'power':
            mean_fft_result =np.abs(mkl_fft.rfft_numpy(fft_in_data))**2
    else:
        print(quantity)
        if quantity == 'amplitude':
            mean_fft_result =np.abs(rfft(fft_in_data))
            # mean_fft_result =np.abs(np.fft.rfft(fft_in_data))
        elif quantity == 'power':
            mean_fft_result =np.abs(rfft(fft_in_data))**2
            # mean_fft_result = np.abs(np.fft.rfft(fft_in_data))**2

    if mean:
        mean_fft_result = np.mean(mean_fft_result, axis=0)

    return mean_fft_result


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


def dumpdata_savez(file_name, data, id_data, block_time):
    np.savez(file_name, power=data,
            block_ids=id_data,
            block_time=block_time)

    return

def dumpdata_hdf5(file_name, data, id_data, block_time):

    # print("save raw pid: ", os.getpid())

    # n_frames_per_loop = data_conf['n_frames_per_loop']
    # data_size = data_conf['data_size']
    # n_blocks_to_save  = data_conf['n_blocks_to_save']

    quantity = data_conf['quantity']
    # output_sel = data_conf['output_sel']
    # file_stop_num = data_conf['file_stop_num']

    f=h5.File(file_name +'.h5','w')
    # f=h5.File(file_name +'.h5','w', driver="core")
    dset = f.create_dataset(quantity, data=data)
    dset = f.create_dataset('block_time', data=block_time)
    # dset.attrs['block_time'] = epoctime2date(block_time)
    dset = f.create_dataset('block_ids', data=id_data)

    f.close()

    return

def save_hdf5_fft_data3(file_name, data, id_data, block_time):

    # print("dumpdata_hdf5_fft_q3 pid: ", os.getpid())

    avg_n = data_conf['avg_n']
    fft_npoint = data_conf['fft_npoint']
    scale_f = data_conf['voltage_scale_f']
    quantity = data_conf['quantity']
    # start_time = data_conf['t0_time']

    # temp_result = subprocess.getoutput('ssh rec "python readtemp.py"')
    # tmp_str=temp_result[1:-2].split(",")
    # t_ps, t_pl = [float(b) for b in tmp_str]

    f=h5.File(file_name +'.h5','w')

    # f=h5.File(file_name +'.h5','w', driver="core")
    dset = f.create_dataset(quantity, data=data)
    # dset.attrs['temp_ps'] = t_ps
    # dset.attrs['temp_pl'] = t_pl
    dset = f.create_dataset('block_time', data=block_time)
    dset = f.create_dataset('block_ids', data=id_data)

    f.close()


    return


def dumpdata_hdf5_fft_q3(data_conf, data, id_data, block_time, file_q):

    # print("dumpdata_hdf5_fft_q3 pid: ", os.getpid())

    avg_n = data_conf['avg_n']
    fft_npoint = data_conf['fft_npoint']
    scale_f = data_conf['voltage_scale_f']
    quantity = data_conf['quantity']
    # start_time = data_conf['t0_time']

    global plan

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

    # f=h5.File(file_name +'.h5','w', driver='core')

    # f=h5.File(file_name +'.h5','w', driver="core")
    # dset = f.create_dataset(quantity, data=data)
    # dset = f.create_dataset(quantity, data=mean_out.get())

    file_q.send((mean_out.get(), id_data, block_time))
    # dset = f.create_dataset(quantity, data=cp.asnumpy(mean_out))
    # dset = f.create_dataset('block_time', data=block_time)
    # dset = f.create_dataset('block_ids', data=id_data)

    # f.close()

    # file_q.put((file_name +'.h5', fout_dst +'.h5'))

    return



def dumpdata_hdf5_fft_q2(file_name, data, id_data, block_time, fout_dst, file_q):

    # print("save raw pid: ", os.getpid())

    avg_n = data_conf['avg_n']
    fft_npoint = data_conf['fft_npoint']
    scale_f = data_conf['voltage_scale_f']
    quantity = data_conf['quantity']
    # start_time = data_conf['t0_time']

    global plan

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

    # out = mean_out.get()
    f=h5.File(file_name +'.h5','w')

    # f=h5.File(file_name +'.h5','w', driver="core")
    # dset = f.create_dataset(quantity, data=data)
    dset = f.create_dataset(quantity, data=mean_out.get())

    # # dset = f.create_dataset(quantity, data=cp.asnumpy(mean_out))
    dset = f.create_dataset('block_time', data=block_time)
    dset = f.create_dataset('block_ids', data=id_data)

    f.close()

    file_q.put((file_name +'.h5', fout_dst +'.h5'))

    return


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
        lost_p = False

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
        else:
            print("block is not connected", id_tail_before, id_arr[0])
            print("program last ", time.time() - s_time)
            num_lost_all += 1


        if i == 1000:
            block_time = epoctime2date((block_time1 + block_time2)/2.)
            display_metrics(time_before, time_now, s_time, num_lost_all,
                    data_conf)
            i = 0

        time_before = time_now
        i +=1

        # }}}

def get_sample_data_simple(sock,raw_data_q, dconf, v):                 #{{{ payload_size,data_size,

    print("get sampe pid: ", os.getpid())

    # the period of the consecutive ID is 2**32 - 1 = 4294967295
    payload_size = dconf['payload_size']
    udp_payload = bytearray(payload_size)
    payload_buff = memoryview(udp_payload)

    loop = True

    while loop:
        sock.recv_into(payload_buff, payload_size)
        raw_data_q.send_bytes(payload_buff)
        if v.value == 1:
            loop = False
            print("read finished ")
    return

        # }}}

def get_sample_data(sock,raw_data_q, dconf, v):                 #{{{ payload_size,data_size,

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


    print("get sampe pid: ", os.getpid())

    loop = True

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

        raw_data_q.put((udp_data,udp_id))

        # if v.value == 1:
            # loop = False
            # print("read raw data finished ")

    return

    # }}}

def get_sample_data2(sock,raw_data_q, dconf, v):                 #{{{ payload_size,data_size,

    n_frames_per_loop = dconf['n_frames_per_loop']
    payload_size = dconf['payload_size']
    data_size = dconf['data_size']
    id_size = dconf['id_size']
    data_type = dconf['data_type']
    print("data_type", data_type)
    logging.info("data_type: %s", data_type)
    id_tail_before = dconf['id_tail_before']
    output_fft = dconf['output_fft']

    udp_payload = bytearray(payload_size)
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

        id_head_before = id_arr[0]
        id_tail_before = id_arr[-1]
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
                logging.warning("fresh id: %i, %i, %i, %i ",
                                id_arr[0],id_arr[0]%16,
                                id_arr[-1], id_arr[-1]%16)

            else:
                udp_data_arr = np.frombuffer(udp_data, dtype=data_type)
                # block_time = epoctime2date((block_time1 + block_time2)/2.)
                block_time = (block_time1 + block_time2)/2.

                if output_fft:
                    raw_data_q.put((udp_data_arr,id_arr, block_time))
                else:
                    raw_data_q.put((udp_data_arr,id_arr, block_time))
        else:
            print("block is not connected", id_tail_before, id_arr[0])
            logging.debug("block is not connected %i, %i", id_tail_before, id_arr[0])
            print("program last ", time.time() - s_time)
            num_lost_all += 1
            logging.warning("previous blocked fresh id: %i, %i, id_tail, %i, %i ",
                            id_head_before,id_head_before%16,
                            id_tail_before,id_tail_before%16)

            logging.warning("disc blocked fresh id: %i, %i, id_tail, %i, %i",
                            id_arr[0],id_arr[0]%16,
                            id_arr[-1], id_arr[-1]%16)

        if id_arr[-1] % 16 != 15:
            while tmp_id % 16 != 15:
                sock.recv_into(warmup_buff, payload_size)
                tmp_id = int.from_bytes(warmup_data[payload_size-id_size:
                payload_size], 'big')

            id_tail_before = tmp_id
            logging.warning("fixed tail id: %i, %i ",
                            id_tail_before, id_tail_before%16)

        time_now = time.perf_counter()

        if i == 200:
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
