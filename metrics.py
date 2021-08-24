#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@imac.lan>
#
# Distributed under terms of the MIT license.

"""

"Calculate the disk space of the data in one day"
"""

# data_per_sec = 66.485/0.13

data_rate = 480e6*2*8

data_per_sec = 480e6*2

data_per_day = data_per_sec * 60 * 60 * 24

timestep = 1/480e6
payload_size = 8192
nsample_per_packet = payload_size / 2
block_size = 8000

block_sample_n = payload_size * block_size /2

sample_rate = 480e6

sample_per_day = sample_rate * 60 * 60 * 24

file_n = sample_per_day / nsample_per_packet / block_size

print(f"Theory band with {data_rate/1024/1044:.3f} Gb/s, " + \
      f"with extra cost:{data_rate/8192*8220./1024/1024:.3f} Gb/s")
print(f"{data_per_day/1024/1024/1024:.3f} GB data per day")
print(f"{data_per_day/1024/1024/1024/1204:.3f} TB data per day")
print(f"minimal time step {timestep*1000:.3e} ms, {timestep*1e9:.3f} ns")
print("")
print(f"per file size: {payload_size*block_size/1024/1024:.3f} MB")
print(f"file num per day: {file_n:.3f}.")


