#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@Quans-iMac-Pro.lan>
#
# Distributed under terms of the MIT license.

"""

"""
from pymodbus.client.sync import ModbusSerialClient

client = ModbusSerialClient(method = 'rtu', port='/dev/tty.usbserial-0001',
                            stopbits=1,
                            bytesize=8,
                            parity='N',
                            baudrate=4800)

if client.connect():
    read=client.read_holding_registers(address = 0x3 ,count =1,unit=1)
    data=read.registers
    print(data)
    print(bin(data[0]))
