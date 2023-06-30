#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Author: Quan Guo <guoquan@shao.ac.cn>
#
# Distributed under terms of the MIT license.

"""
Prepare the parameters for RX
"""
import platform as pf
import netifaces
import argparse
import os
from rich import print
from rich.table import Table
import sys


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def is_nic_up(nic):
    addr = netifaces.ifaddresses(nic)
    return netifaces.AF_INET in addr

data_conf = {}
labels = ["RAW_output1", "FFT_output1", "RAW_output2", "FFT_output2"]
src_ip = ["192.168.90.20", "192.168.90.21", "192.168.90.30", "192.168.90.31"]
src_port = [59000, 59001, 59000, 59001]
dst_port = [60000, 60001, 60000, 60001]
dst_mac = []
dst_ip = []

grid = Table.grid()
grid.add_column(justify="left", width=50, vertical="center")
grid.add_column(width=30, vertical="cetner")
grid.add_column(justify="right", width=20, vertical="center")
grid.add_row("", "Info", "", style='bold white on blue')

green_ok = bcolors.OKGREEN + " .....OK." + bcolors.ENDC
# green_fft_data = bcolors.OKGREEN + "FFT data" + bcolors.ENDC
# green_raw_data = bcolors.FAIL + "raw data" + bcolors.ENDC
green_fft_data = "[green]FFT data"
green_raw_data = "[red]RAW data"

# the order of the lists is "RAW1, FFT1, RAW2, FFT2"
# do not change
# raw1, fft1, raw2, fft2
# dst_ip = ["192.168.90.100", "192.168.90.101",
#           "192.168.90.100", "192.168.90.111"]


platform_system = pf.system()
if 'Darwin' in platform_system:
    network_faces = ["en7", "en7", "en8", "en8"]
else:
    node_name = pf.node()
    if node_name == 'lacebian1':
        # network_faces = ["enp10s0", "enp10s0", "enp10s0f1", "enp10s0f1"]
        network_faces = ["enp10s0", "", "", ""]
    elif node_name == "firefly":
        network_faces = ["enp63s0", "", "", ""]
    elif node_name == "gqhp":
        network_faces = ["enp153s0f0", "enp153s0f0", "enp153s0f1",
                         "enp153s0f1"]
    else:
        network_faces = ["enp119s0f0", "enp119s0f0", "enp119s0f1",
                         "enp119s0f1"]

for nic in network_faces:
    if nic == '':
        dst_mac.append("")
        dst_ip.append("")
    else:
        av_nics = netifaces.interfaces()
        if not is_nic_up(nic):
            os.system("sudo netctl restart " + nic)
            print("Warning: " + nic + "is not up")
            print("Bring up " + nic)

        grid.add_row("Nic name: ", nic, "ready")
        addrs = netifaces.ifaddresses(nic)
        dst_mac.append(addrs[netifaces.AF_LINK][0]['addr'])
        dst_ip.append(addrs[netifaces.AF_INET][0]['addr'])


if 'raw_rx' in sys.argv[0]:
    parser = argparse.ArgumentParser()
    parser.add_argument("port",
                        choices=[0, 1, 2, 3],
                        help="the port number of the input that you \
                            want to observe",
                        type=int)

    parser.add_argument("--fft_npoint",
                        type=int,
                        default=65536,
                        help="the number of fft points")

    parser.add_argument("--f_num",
                        type=int,
                        default=20,
                        help="the number of files saved before stop")

    parser.add_argument("--avg_n",
                        type=int,
                        help="the average times of the spectrum ")

    if "plot" in sys.argv[0]:
        parser.add_argument('--waterfall',
                            action=argparse.BooleanOptionalAction)
        args = parser.parse_args()


    else:
        parser.add_argument("directory_to_save",
                            help="the path of directory to save the data")
        args = parser.parse_args()

        data_conf['data_dir'] = args.directory_to_save


    output_sel = args.port
    data_conf['output_sel'] = output_sel

    # the size of socket buffer for recieving data, maximum is 1610612736
    if 'Darwin' in platform_system:
        rx_buffer = 7168000
    else:
        rx_buffer = 1610612736

###############################################################################
#                       The default values of data_conf                       #
###############################################################################

    # the number of fft which will determine the RBW
    data_conf['fft_npoint'] = args.fft_npoint
    # the rx program runing forever ? file_stop_num < 0 or it will stop
    # after saving file_stop_num files
    # run_forever = True
    data_conf['file_stop_num'] = args.f_num
    # group files by the hour of the day, if too many files in a folder, can
    # also be grouped by each minute of the hour
    # default by hour
    data_conf['split_by_min'] = False
    data_conf['loop_file'] = False
    data_conf['loop_file_num'] = 500
    data_conf['node_name'] = node_name
    data_conf['network_faces'] = network_faces
    data_conf['sample_rate'] = 480e6
    data_conf['data_size'] = 8192
    data_conf['save_hdf5'] = True
    data_conf['save_lost'] = False
    data_conf['voltage_scale_f'] = 0.5/2**15
    data_conf['avg_n'] = 8
    data_conf['abs_fail_volt'] = 18.0

    style = "bold white on blue"

    if 'fft' in sys.argv[0]:
        data_conf['output_fft'] = True
        grid.add_row("output ",  "", green_fft_data)
    else:
        data_conf['output_fft'] = False
        grid.add_row("output ",  "", green_raw_data)

    if data_conf['output_fft']:
        data_conf['n_frames_per_loop'] = 8192*2
        data_conf['n_blocks_to_save'] = 1024
        data_conf['quantity'] = 'amplitude'
    else:
        # How many udp packets of data received in one read loop
        # how many raw data read loops accumulated then save
        # useless in non-fft mode
        data_conf['n_frames_per_loop'] = 8192
        data_conf['n_blocks_to_save'] = 1024
        data_conf['quantity'] = 'voltage'

    # the average time of spectrum
    # data_conf['avg_time'] = 1.0   #ms
    sample_rate_over_1000 = data_conf['sample_rate']/1000
    fft_single_time = data_conf['fft_npoint'] / sample_rate_over_1000
    data_conf['fft_single_time'] = fft_single_time

    if args.avg_n:
        up_factor = args.avg_n // data_conf['avg_n']
        data_conf['avg_n'] = args.avg_n
        data_conf['n_blocks_to_save'] = 1024 * up_factor
    data_conf['avg_time'] = data_conf['avg_n']*fft_single_time

    # How many udp packets of data received in one read loop
    # every *fft_npoint* will be grouped for FFT
    # how many fft groups in one read loop
    data_conf['n_fft_blocks_per_loop'] = int(data_conf['data_size'] *
                                             data_conf['n_frames_per_loop']
                                             / data_conf['fft_npoint']/2)

    # how many averageed fft groups in one read loop
    data_conf['n_avg_fft_blocks_per_loop'] = \
        data_conf['n_fft_blocks_per_loop'] // data_conf['avg_n']

    if data_conf['loop_file']:
        if data_conf['file_stop_num'] > data_conf['loop_file_num']:
            raise ValueError("file stop num greater than loop file \
                             num...Please check again")

    if data_conf['output_fft']:
        grid.add_row("Each fft block has:",
                     f"{data_conf['fft_npoint']} points",
                     f"{480000/data_conf['fft_npoint']:.3f} kHz rbw")
        grid.add_row("Each processing loop has",
                     f"{data_conf['n_fft_blocks_per_loop']}",
                     "fft blocks")
        grid.add_row(f"The average time of fft spectrum is",
                     f"{data_conf['avg_time']:.3f} ms",
                     f"every {data_conf['avg_n']} times")
    else:
        grid.add_row("Each file has ",
                     f"{data_conf['n_blocks_to_save']}",
                     "data frames")

    if data_conf['file_stop_num'] < 0:
        grid.add_row("The Program will run", "",
                     "[red]forever")
    else:
        grid.add_row("The Program will stop after saving ",
                     f"{data_conf['file_stop_num']}",
                     "files")
else:
    data_conf['fft_npoint'] = 65536
    data_conf['file_stop_num'] = 4000

print(grid)
