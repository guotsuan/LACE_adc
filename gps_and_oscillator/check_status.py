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
from socket import error as socket_error
from rich import print
from rich.table import Table
import sys


green_ok = "[green]OK"


def get_gps_coord():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect(("192.168.1.111", 4001))
    except socket_error:
        print("Cannot connect to the GPS/NTP server")
        print("Please wait for the GPS/NTP server to power up...,",
              "or we have a serious problem.")
        sys.exit()

    get_coord = False

    with BytesIO() as buffer:
        while not get_coord:
            ff = s.recv(2048)
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
                        full_lat = msg.lat_dir + lat[0:2] + \
                            u"\N{DEGREE SIGN}" + lat[2:] + "'"

                        lon = msg.lon
                        full_lon = msg.lon_dir + lon[0:3] + \
                            u"\N{DEGREE SIGN}" + lon[3:] + "'"
                        s.close()
                        get_coord = True

                        return full_lat, full_lon


def check_gps():
    grid = Table.grid()

    grid.add_column(justify="left", width=40, vertical="center")
    grid.add_column(justify="right", width=60, vertical="center")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect(("192.168.1.111", 4001))
    except socket_error:
        print("Cannot connect to the GPS/NTP server")
        print("Please wait for the GPS/NTP server to power up...",
              " or we have a serious problem.")
        sys.exit()

    print("   ")
    print("Connected to the GPS/Oscillator system....\n")

    lat_showed = False
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
                ant_showed = False
                sat_showed = False
                system_ready = False
                warm_up = False
                acq = False
                hold = False
                oscillator_ready = False
            ff = s.recv(2048)
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
                        full_lat = msg.lat_dir + lat[0:2] + \
                            u"\N{DEGREE SIGN}" + lat[2:] + "'"

                        lon = msg.lon
                        full_lon = msg.lon_dir + lon[0:3] + \
                            u"\N{DEGREE SIGN}" + lon[3:] + "'"
                        grid.add_row("Lontitude: ", "Latitude: ")
                        grid.add_row(full_lon,  full_lat)

                        lat_showed = True

                    if hasattr(msg, 'data'):
                        if hasattr(msg, 'msg_type') and msg.msg_type == '12' \
                                and not sat_showed:
                            print("Date: ", msg.data[3] + '.' +
                                  msg.data[2] + '.' + msg.data[1],
                                  'UTC: ' + msg.data[0][0:2] + ':' +
                                  msg.data[0][3:5] + ':' + msg.data[0][5:])
                            print("GPS Sat number: ", msg.data[4],
                                  ", BD Sat number :", msg.data[5])
                            sat_showed = True

                        if "WARMUP" in msg.data and not warm_up:
                            print("Oscillator is warmed up")
                            warm_up = True

                        if "ACQUIRING" in msg.data and not acq:
                            print("Oscillator is acquiring")
                            acq = True

                        if "HOLDOVER" in msg.data and not hold:
                            print("Oscillator is in state of holdover...",
                                  "WARNING, will red_failed in 24 hours")
                            hold = True

                        if "ANTENNA OPEN" in msg.data:
                            grid.add_row("ANTENNA is disconnected...",
                                         "[red]failed")

                        if "ANTENNA SHORT" in msg.data:
                            grid.add_row("ANTENNA is shorted...",
                                         "[red]failed")

                        if "ANTENNA OK" in msg.data and not ant_showed:
                            grid.add_row("ANTENNA is ready...",
                                         green_ok)
                            ant_showed = True

                        if "LOCKED" in msg.data and not oscillator_ready:
                            grid.add_row("Oscillator is locked...",
                                         green_ok)
                            oscillator_ready = True

                        if ant_showed and oscillator_ready:
                            print(grid)
                            grid.add_row(
                                "GPS Timer and Oscillator is ready ...",
                                green_ok)
                            print("Exited.....\n")
                            system_ready = True
                            s.close

    s.close()
    return


if __name__ == "__main__":
    check_gps()
