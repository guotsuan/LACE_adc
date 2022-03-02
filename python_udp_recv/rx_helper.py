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
import termios, fcntl


def set_noblocking_keyboard():

    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

def dumpdata(file_name, data, id_data, stime, t1, ns, save_hdf5=False, header=None):

    if save_hdf5:
        f=h5.File(file_name,'w')
        dset = f.create_dataset('voltage', data=data)
        dset.attrs['start_time'] = stime
        dset.attrs['unit'] = 'V'
        dset.attrs['offset_time'] = t1
        dset.attrs['nsample'] = t1
        dset = f.create_dataset('frame_id', data=id_data)
        f.close()
    else:
        np.save(file_name, data)

    # ff = h5.File(file_name, 'w')
    # ff.create_dataset('voltage', data=data )
    # ff.close()
