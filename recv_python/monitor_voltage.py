#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@macpro.lan>
#
# Distributed under terms of the MIT license.

"""

"""
import logging
import minimalmodbus as mbus

dev = mbus.Instrument('/dev/ttyUSB0', 1)
dev.serial.baudrate = 4800


def check_voltage():
    try:
        addr = int(0x48)
        voltage = dev.read_register(addr, 2)
    except IOError:
        voltage = -100
        logging.warning("Monitoring voltage failed...")

    return voltage


if __name__ == "__main__":
    print(check_voltage())
