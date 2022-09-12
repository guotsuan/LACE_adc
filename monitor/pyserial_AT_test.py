#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 gq <gq@Quans-iMac-Pro.lan>
#
# Distributed under terms of the MIT license.

"""

"""

import time
import serial

recipient = "+1234567890"
message = "Hello, World!"

connect = serial.Serial("/dev/tty.usbserial-0001", baudrate=9600,  timeout=5)
connect.write(b'AT+V\r\n')
time.sleep(0.5)
out=connect.readline()
print(out)
