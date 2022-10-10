import os
import h5py as h5
import numpy as np
import json
import sys
import matplotlib.pyplot as plt

def nfft_cal(rbw, fft_band=240.):
    float_np = round(np.log2(fft_band*1000.*2/rbw))
    return 2**float_np

def rbw_cal(nfft, fft_band=240.):
    rbw = fft_band*1000.*2/nfft
    return rbw

def peak_power_detector(freq, trace):
    peakPower = np.amax(trace)
    peakFreq = freq[np.argmax(trace)]

    return peakPower, peakFreq


from read_data import fft_px, get_data_file_list, get_data
sys.path.append("../")
from recv_python.fft_helper import *

#name_appedix = "wn_25dbm"
# wave_type = "sine"
wave_type = "white"
name_list = ["wn_10dbm", "wn_15dbm", "wn_20dbm", "wn_40dbm"]
name_list = ["wn_open", "wn_open_2", "danl2"]
color = ['k', 'b', 'r', 'y']

plt.figure(figsize=(9,5))
for name_appedix, cc in zip(name_list, color):

    data_dir ="/home/gq/projs/data/" + name_appedix
    if name_appedix == 'danl2':
        px, py, rbw = get_data(data_dir, 536870912, workers=4, file_stop=16*1,
                               fft_method="mkl_fft")
    else:
        px, py, rbw = get_data(data_dir)

    print("freq: ", rbw, " Hz")

    # plot receiver data

    # peakpower, peakf = peak_power_detector(px, dbm_fft)
    plt.plot(px, py - 10*np.log10(rbw) , color=cc, lw=0.5,
             label="RX " + f"rbw {rbw:.2f}", alpha=0.6)
    plt.plot(px, py, color=cc, lw=2.0,
             label="RX " + f"rbw {rbw:.2f} per Hz", alpha=0.4)
    # plt.axvline(peakf, color='y', alpha=0.5)
    plt.ylim([-160,-50])
    plt.xlim([-1,245])
    plt.xlabel("MHz")
    ppx = 45
    ppy = -60

    # plt.text(ppx, ppy,
    #     'Peak power in RX: {:.2f} dBm @ {:.2f} MHz, rbw: {:.2f} khz'.format(
    #       peakpower, peakf, 240./dbm_fft.shape[-1]*1000))

    # plot spectrum data

#     sfile = "spectrum_data_"+name_appedix + ".npz"
#     data = np.load(sfile, allow_pickle=True)
#     plt.plot(data['freq']/1e6, data['data'],'--', color=cc, alpha=0.6,
#             label="SA")
#     peakpower, peakf = peak_power_detector(data['freq']/1e6, data['data'])

# #     plt.text(ppx, ppy-5,
# #         'Peak power in SA: {:.2f} dBm @ {:.2f} MHz, rbw: {:.2f} khz'.format(
# #           peakpower, peakf, 7.32), color='r')

#     if wave_type == "sine":
#         plt.text(ppx, ppy-10,
#             'Peak power in theory: {:.2f} dBm @ {:.2f} MHz'.format(
#               23.01, peakf), color='b')

plt.legend(loc='upper right')
plt.ylabel("dBm/Hz")
plt.title("Dispaly Average Noise Level (DANL)")
# plt.tightlayout()
plt.show()
# plt.savefig("danl_single.pdf")
