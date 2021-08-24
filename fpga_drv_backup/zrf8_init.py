#!/usr/bin/python
from os import system
import time
import os
import re
import py2drv as pd

def main():
    pd.set_PLL(5)
    #pd.set_DEV(5, 60000)
    #rfin=[8,9,10,11,12,13,14,15]
    #pd.set_rfin(rfin)
    #pd.set_gain_bram_0(1,1,1,1)
    #pd.set_gain_bram_1(1,1,1,1)
    #pd.set_gain_bram_2(1,1,1,1)
    #pd.set_gain_bram_3(1,1,1,1)
    #pd.set_outChannel(0, 16, 2)
    #pd.set_outChannel(1, 20, 3)
    #pd.set_outChannel(2, 21, 4)
    #pd.set_outChannel(3, 23, 5)
    #pd.set_outChannel(4, 25, 7)
    #pd.set_outChannel(5, 26, 9)
    #pd.set_outChannel(6, 27, 10)
    #pd.set_outChannel(7, 28, 11)
    #pd.set_outChannel(8, 30, 13)
    #pd.set_outChannel(9, 31, 15)
    #pd.set_outChannel(10, 32, 16)
    #pd.set_outChannel(11, 33, 17)
    #pd.set_outChannel(12, 34, 18)
    #pd.set_outChannel(13, 35, 19)
    #pd.set_outChannel(14, 36, 20)
    #pd.set_outChannel(15, 40, 21)
    #pd.set_outChannel(16, 41, 24)
    #pd.set_outChannel(17, 42, 25)
    #pd.set_outChannel(18, 43, 26)
    #pd.set_outChannel(19, 44, 27)
    #pd.set_outChannel(20, 45, 28)
    #pd.set_outChannel(21, 46, 29)
    #pd.set_outChannel(22, 47, 30)
    #pd.set_outChannel(23, 48, 31)
    pd.set_10GbE_port()
    pd.set_adc_channel(1)
    pd.sync_PPS()
    pd.reset_data()
    #pd.reset_10GbE()
    #pd.set_gpstime_self()
    #pd.set_pps_delay(-100)



if __name__ == '__main__':
    
    main()
    
    #print (pd.get_temp_PL())
    #print (pd.get_temp_PS())
    #print (pd.get_DEV())
    #print (pd.get_spec(3))
