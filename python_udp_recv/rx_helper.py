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

def dumpdata(file_name, data, stime, t1, ns, save_hdf5=False, header=None):

    if save_hdf5:
        f=h5.File(file_name,'w')
        dset = f.create_dataset('voltage', data=data)
        dset.attrs['start_time'] = stime
        dset.attrs['unit'] = 'V'
        dset.attrs['offset_time'] = t1
        dset.attrs['nsample'] = t1
        f.close()

    np.save(file_name, data)

    # ff = h5.File(file_name, 'w')
    # ff.create_dataset('voltage', data=data )
    # ff.close()
