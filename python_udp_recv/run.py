#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
run two receiving files
"""

import subprocess
from multiprocessing import Process, Lock, Pool
import time

python_run ='/home/gq/mambaforge/bin/python'

def run_rx(type):
    print(time.perf_counter(), type)
    subprocess.run([python_run, "rx.py", type])

if __name__ == "__main__":
    for num in [0, 2]:
            Process(target=run_rx, args=(str(num), )).start()



# subprocess.run([python_run, "rx.py", "0 &"])
# subprocess.run([python_run, "rx.py", "2 &"])

