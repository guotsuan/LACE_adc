#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
functions for fft 

"""
import numpy as np


# for raw output 

def fft_to_dBV(data):
    
    out = 20.*np.log10(np.abs(data/data.size))
    return out

def fft_to_dBm(data):
    
    resistor = 50
    mili_power = 0.001
    out = 10.*np.log10(np.abs(data/data.size)**2/resistor/mili_power)
    return out
