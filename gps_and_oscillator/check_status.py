#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.

"""
Checking the status of GPS and oscillator
"""

import socket
from io import BytesIO
import pynmea2
from pynmea2 import ParseError
import errno
from socket import error as socket_error
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


green_ok = bcolors.OKGREEN + " OK" + bcolors.ENDC
red_failed = bcolors.FAIL + " red_failed" + bcolors.ENDC

def get_gps_coord():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect(("192.168.1.111", 4001))
    except socket_error as serr:
        print("Cannot connect to the GPS/NTP server")
        print("Please wait for the GPS/NTP server to power up... or we have a serious problem.")
        sys.exit()

    get_coord =False

    with BytesIO() as buffer:
        while not get_coord:
            ff = s.recv(2048)       # Read in some number of bytes -- balance this
            buffer.write(ff)
            buffer.seek(0)
            for line in buffer.readlines():
                if line == '':
                    break

                try:
                    msg = pynmea2.parse(line.decode())
                except ParseError:
                    pass
                else:
                    if hasattr(msg, "lat"):
                        lat = msg.lat
                        full_lat = msg.lat_dir + lat[0:2]+ u"\N{DEGREE SIGN}" + lat[2:] + "'"

                        lon = msg.lon
                        full_lon = msg.lon_dir + lon[0:3]+ u"\N{DEGREE SIGN}" + lon[3:] + "'"
                        s.close()
                        get_coord = True

                        return full_lat, full_lon


def check_gps():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect(("192.168.1.111", 4001))
    except socket_error as serr:
        print("Cannot connect to the GPS/NTP server")
        print("Please wait for the GPS/NTP server to power up... or we have a serious problem.")
        sys.exit()


    print("   ")
    print("Connected to the GPS/Oscillator system....\n")

    lat_showed = False
    lon_showed = False
    sat_num_showed = False
    ant_showed = False
    sat_showed = False
    system_ready = False
    warm_up = False
    acq = False
    hold = False
    oscillator_ready = False

    delay = 50

    tn = 0
    with BytesIO() as buffer:

        while not system_ready:
            tn += 1

            if tn % delay == 0:
                lat_showed = False
                lon_showed = False
                sat_num_showed = False
                ant_showed = False
                sat_showed = False
                system_ready = False
                warm_up = False
                acq = False
                hold = False
                oscillator_ready = False
            ff = s.recv(2048)       # Read in some number of bytes -- balance this
            buffer.write(ff)
            buffer.seek(0)
            for line in buffer.readlines():
                if line == '':
                    break

                try:
                    msg = pynmea2.parse(line.decode())
                except ParseError:
                    pass
                else:
                    if hasattr(msg, "lat") and not lat_showed:
                        lat = msg.lat
                        # lmin = msg[3:]
                        full_lat = msg.lat_dir + lat[0:2]+ u"\N{DEGREE SIGN}" + lat[2:] + "'"

                        lon = msg.lon
                        # lmin = msg[3:]
                        full_lon = msg.lon_dir + lon[0:3]+ u"\N{DEGREE SIGN}" + lon[3:] + "'"
                        print("Latitude: ", full_lon, "Latitude: ", full_lat)

                        lat_showed = True
                        lon_showed = True


                    if hasattr(msg, 'data'):
                        if hasattr(msg, 'msg_type') and msg.msg_type == '12' and not sat_showed:
                            print("Date: ", msg.data[3] + '.' + msg.data[2] +'.' +
                                    msg.data[1], 'UTC: '+msg.data[0][0:2] +':' +
                                    msg.data[0][3:5] +':' + msg.data[0][5:])
                            print("GPS Sat number: ", msg.data[4], ", BD Sat number :", msg.data[5])
                            sat_showed = True

                        if "WARMUP" in msg.data and not warm_up:
                            print("Oscillator is warmed up")
                            warm_up = True

                        if "ACQUIRING" in msg.data and not acq:
                            print("Oscillator is acquiring")
                            acq = True

                        if "HOLDOVER" in msg.data and not hold:
                            print("Oscillator is in state of holdover...........WARNING, will red_failed in 24 hours")
                            hold = True

                        if "ANTENNA OPEN" in msg.data:
                            print("ANTENNA is disconnected......." + red_failed)

                        if "ANTENNA SHORT" in msg.data:
                            print("ANTENNA is shorted......." + red_failed)

                        if "ANTENNA OK" in msg.data and not ant_showed:
                            print("ANTENNA is ready......." + green_ok)
                            ant_showed = True

                        if "LOCKED" in msg.data and not oscillator_ready:
                            print("Oscillator is locked.........." + green_ok)
                            oscillator_ready = True

                        if ant_showed and oscillator_ready:
                            print("GPS Timer and Oscillator is ready ......" +
                                    green_ok + "\n")
                            print("Exited.....\n")
                            system_ready=True
                            s.close
                            return

    s.close()

if __name__ == "__main__":
    check_gps()
