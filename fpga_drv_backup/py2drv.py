#!/usr/bin/python3
from os import system
import time
import os
import re
from subprocess import Popen, PIPE


def execCmd(cmdstr):
    r = os.popen(cmdstr)
    text = r.read()
    r.close()
    return text

def set_PLL(mode):
    print('configure PLL for ADC')
    system("lmx2592drv -M %d"%(mode))
    time.sleep(0.01)

def set_10GbE_port():
    print('configure 10GbE port')

    src_ip=0xC0A85A14
    dst_ip=0xC0A85A64
    src_port=59000;
    dst_port=60000;
    src_mac0=0x01;
    src_mac1=0x1000;
    dst_mac0=0x4311C0A0;
    dst_mac1=0x0007;
    ctr=hex(dst_mac0)
    system("bram -s 10 -a 1 -w -v %s"%(ctr))
    ctr=hex(dst_ip)
    system("bram -s 10 -a 2 -w -v %s"%(ctr))
    ctr=hex((dst_port << 16)+dst_mac1)
    system("bram -s 10 -a 3 -w -v %s"%(ctr))
    ctr=hex(src_mac0)
    system("bram -s 10 -a 4 -w -v %s"%(ctr))
    ctr=hex(src_ip)
    system("bram -s 10 -a 5 -w -v %s"%(ctr))
    ctr=hex((src_port << 16)+src_mac1)
    system("bram -s 10 -a 6 -w -v %s"%(ctr))

    src_ip=0xC0A85A15
    dst_ip=0xC0A85A65
    src_port=59000
    dst_port=60000
    src_mac0=0x02
    src_mac1=0x1000
    dst_mac0=0x7F5E0002
    dst_mac1=0x105A
    ctr=hex(dst_mac0)
    system("bram -s 10 -a 9 -w -v %s"%(ctr))
    ctr=hex(dst_ip)
    system("bram -s 10 -a 10 -w -v %s"%(ctr))
    ctr=hex((dst_port << 16)+dst_mac1)
    system("bram -s 10 -a 11 -w -v %s"%(ctr))
    ctr=hex(src_mac0)
    system("bram -s 10 -a 12 -w -v %s"%(ctr))
    ctr=hex(src_ip)
    system("bram -s 10 -a 13 -w -v %s"%(ctr))
    ctr=hex((src_port << 16)+src_mac1)
    system("bram -s 10 -a 14 -w -v %s"%(ctr))

def set_adc_channel(ith):
    ctr=hex(ith)
    system("bram -s 10 -a 7 -w -v %s"%(ctr))

def set_DEV(dev, port):
    ctr=hex((port<<16) + dev)
    system("bram -s 10 -a 0 -w -v %s"%(ctr))

def get_DEV():
    cmd = "bram -s 10 -a 0"
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    result = p.stdout.read().strip().decode()
    
    line = result.split(":")
    dev = (int(line[-1],16) & 0xFFFF)
    port = ((int(line[-1],16) & 0xFFFF0000) >> 16)
    return dev,port
    

def set_rfin(Rfin):
    if (len(Rfin) == 8):
        ctr=hex((Rfin[1]<< 16)+Rfin[0])
        system("bram -s 10 -a 1 -w -v %s"%(ctr))
        ctr=hex((Rfin[3]<< 16)+Rfin[2])
        system("bram -s 10 -a 2 -w -v %s"%(ctr))
        ctr=hex((Rfin[5]<< 16)+Rfin[4])
        system("bram -s 10 -a 3 -w -v %s"%(ctr))
        ctr=hex((Rfin[7]<< 16)+Rfin[6])
        system("bram -s 10 -a 4 -w -v %s"%(ctr))

def set_outChannel(chnum, chan, devy):
    print(['set %sth output channel'%(chnum)])
    port=59000+devy
    ctr=hex((port << 16) + (devy << 8)+chan)
    system("bram -s 10 -a %s -w -v %s"%(hex(chnum+5),ctr))	

def get_outChannel(chnum):
    cmd="bram -s 10 -a %s"%(hex(chnum+5))
    p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    result = p.stdout.read().strip().decode()
    line=result.split(":")
    ctn=int(line[-1],16)
    chan=ctn & 0xFF
    devy=((ctn & 0xFF00) >> 8)
    port =59000+devy
    return chan, devy, port

def sync_PPS():
    print('synchronization for internal PPS')
    system("gpioctrl -m 1 -c 5 -v 0")
    system("gpioctrl -m 1 -c 5 -v 1")
    system("gpioctrl -m 1 -c 5 -v 0")
    time.sleep(1)

def reset_data():
    print('reset for data processing')
    system("gpioctrl -m 1 -c 6 -v 0")
    system("gpioctrl -m 1 -c 6 -v 1")
    system("gpioctrl -m 1 -c 6 -v 0")
    time.sleep(1)

def reset_10GbE():
    print('reset for 10 GbE')
    system("gpioctrl -m 1 -c 4 -v 0")
    system("gpioctrl -m 1 -c 4 -v 1")
    system("gpioctrl -m 1 -c 4 -v 0")
    time.sleep(1)

def get_temp_PS():
    cmd = "cat /sys/bus/iio/devices/iio\:device0/in_temp0_ps_temp_raw";
    result = execCmd(cmd);
    tempstr = result
    temp = float(tempstr);
    temp = temp * 509.3140064 / 65536.0 - 280.23087870; 
    #print ("PS current temp is : %-3.2f"%(temp))
    return temp

def get_temp_PL():
    cmd = "cat /sys/bus/iio/devices/iio\:device0/in_temp1_remote_temp_raw";
    result = execCmd(cmd);
    tempstr = result
    temp = float(tempstr);
    temp = temp * 509.3140064 / 65536.0 - 280.23087870; 
    #print ("PL current temp is : %-3.2f"%(temp))
    return temp

def get_spec(ith):
    ## ith should be 0,1,...7; 
    cmd = "bram -s 1 -a %s -n 0x80"%(hex(128*ith))
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    result = p.stdout.read().strip().decode()
    list_out = []
    lines = result.splitlines()
    for i in lines:
        line = i.split(":")
        list_out.append(int(line[-1],16))

    cmd = "bram -s 2 -a %s -n 0x80"%(hex(128*ith))
    #print cmd
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    result = p.stdout.read().strip().decode()
    lines = result.splitlines()
    for i in lines:
        line = i.split(":")
        list_out.append(int(line[-1],16))

    return list_out

def get_voltage():
    cmd = "cat /sys/bus/iio/devices/iio\:device0/in_voltage0_vcc_pspll0_raw"
    unit = float(execCmd(cmd));

    cmd = "cat /sys/bus/iio/devices/iio\:device0/in_voltage0_vcc_pspll0_scale"
    precision = float(execCmd(cmd));
    
    voltage = unit*precision/1000.0
    return voltage

def set_gain_bram_0(a0,a1,a2,a3):
    gain =hex((a3 << 24)+(a2 << 16) + (a1 << 8)+a0)
    for ii in range(0,128):
        system("bram -s 3 -a %s -w -v %s"%(hex(ii),gain))

def set_gain_bram_1(a0,a1,a2,a3):
    gain =hex((a3 << 24)+(a2 << 16) + (a1 << 8)+a0)
    for ii in range(0,128):
        system("bram -s 4 -a %s -w -v %s"%(hex(ii),gain))    


def set_gain_bram_2(a0,a1,a2,a3):
    gain =hex((a3 << 24)+(a2 << 16) + (a1 << 8)+a0)
    for ii in range(0,128):
        system("bram -s 5 -a %s -w -v %s"%(hex(ii),gain))

def set_gain_bram_3(a0,a1,a2,a3):
    gain =hex((a3 << 24)+(a2 << 16) + (a1 << 8)+a0)
    for ii in range(0,128):
        system("bram -s 6 -a %s -w -v %s"%(hex(ii),gain))

def set_gain_ad0(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFFFF00)+(gain(ii) & 0xFF)
        system("bram -s 3 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFFFF00)+(gain(ii+128) & 0xFF)
        system("bram -s 4 -a %s -w -v %s"%(hex(ii),gaintx))

def set_gain_ad1(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFF00FF)+((gain(ii) & 0xFF) <<8)
        system("bram -s 3 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFF00FF)+((gain(ii+128) & 0xFF) << 8)
        system("bram -s 4 -a %s -w -v %s"%(hex(ii),gaintx))

def set_gain_ad2(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFF00FFFF)+((gain(ii) & 0xFF) << 16)
        system("bram -s 3 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xF00FFFFF)+((gain(ii+128) & 0xFF) << 16)
        system("bram -s 4 -a %s -w -v %s"%(hex(ii),gaintx))

def set_gain_ad3(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0x00FFFFFF)+((gain(ii) & 0xFF) << 24)
        system("bram -s 3 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0x00FFFFFF)+((gain(ii+128) & 0xFF) << 24)
        system("bram -s 4 -a %s -w -v %s"%(hex(ii),gaintx))
              
def set_gain_ad4(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFFFF00)+(gain(ii) & 0xFF)
        system("bram -s 5 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFFFF00)+(gain(ii+128) & 0xFF)
        system("bram -s 6 -a %s -w -v %s"%(hex(ii),gaintx))

def set_gain_ad5(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFF00FF)+((gain(ii) & 0xFF) <<8)
        system("bram -s 5 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFFFF00FF)+((gain(ii+128) & 0xFF) << 8)
        system("bram -s 6 -a %s -w -v %s"%(hex(ii),gaintx))

def set_gain_ad6(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xFF00FFFF)+((gain(ii) & 0xFF) << 16)
        system("bram -s 5 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0xF00FFFFF)+((gain(ii+128) & 0xFF) << 16)
        system("bram -s 6 -a %s -w -v %s"%(hex(ii),gaintx))

def set_gain_ad7(gain):
    gaintx=0
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0x00FFFFFF)+((gain(ii) & 0xFF) << 24)
        system("bram -s 5 -a %s -w -v %s"%(hex(ii),gaintx))
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=int(line[-1],16)
        gaintx=(ctn & 0x00FFFFFF)+((gain(ii+128) & 0xFF) << 24)
        system("bram -s 6 -a %s -w -v %s"%(hex(ii),gaintx))

def setEqualizerGains(ith, gain):
    if ith == 0: set_gain_ad0(gain)
    elif ith == 1: set_gain_ad1(gain)
    elif ith == 2: set_gain_ad2(gain)
    elif ith == 3: set_gain_ad3(gain)
    elif ith == 4: set_gain_ad4(gain)
    elif ith == 5: set_gain_ad5(gain)
    elif ith == 6: set_gain_ad6(gain)
    elif ith == 7: set_gain_ad7(gain)
    else: set_gain_ad0(gain)

def get_gain_ad0():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF)
        gain.append(ctn)
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF)
        gain.append(ctn)

    return(gain)

def get_gain_ad1():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF00)
        gain.append((ctn>>8))
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF00)
        gain.append((ctn>>8))
    
    return(gain)

def get_gain_ad2():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF0000)
        gain.append((ctn>>16))
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF0000)
        gain.append((ctn>>16))
    
    return(gain)

def get_gain_ad3():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 3 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF000000)
        gain.append((ctn>>24))
    for ii in range(0,128):
        cmd=("bram -s 4 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF000000)
        gain.append((ctn>>24))
    
    return(gain)

def get_gain_ad4():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF)
        gain.append(ctn)
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF)
        gain.append(ctn)

    return(gain)

def get_gain_ad5():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF00)
        gain.append((ctn>>8))
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF00)
        gain.append((ctn>>8))
    
    return(gain)

def get_gain_ad6():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF0000)
        gain.append((ctn>>16))
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF0000)
        gain.append((ctn>>16))
    
    return(gain)

def get_gain_ad7():
    gain=[]
    for ii in range(0,128):
        cmd=("bram -s 5 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0xFF000000)
        gain.append((ctn>>24))
    for ii in range(0,128):
        cmd=("bram -s 6 -a %s"%(hex(ii)))
        p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        result = p.stdout.read().strip().decode()
        line=result.split(":")
        ctn=((int(line[-1],16)) & 0XFF000000)
        gain.append((ctn>>24))
    
    return(gain)

def getEqualizerGains(ith):
    gain=[]
    if ith == 0: gain=get_gain_ad0()
    elif ith == 1: gain=get_gain_ad1()
    elif ith == 2: gain=get_gain_ad2()
    elif ith == 3: gain=get_gain_ad3()
    elif ith == 4: gain=get_gain_ad4()
    elif ith == 5: gain=get_gain_ad5()
    elif ith == 6: gain=get_gain_ad6()
    elif ith == 7: gain=get_gain_ad7()
    else: gain=sgt_gain_ad0(gain)
    return(gain)


def set_gpstime(a0):
    print("set gps time: %s"%(a0))
    gpstime=hex(a0)
    system("bram -s 10 -a 0x1F -w -v %s"%(gpstime))
    system("gpioctrl -m 1 -c 8 -v 0")
    system("gpioctrl -m 1 -c 8 -v 1")
    system("gpioctrl -m 1 -c 8 -v 0")
    

def get_gpstime():
    cmd=("bram -s 10 -a 0x1F")
    p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    result = p.stdout.read().strip().decode()
    line=result.split(":")
    ctn=int(line[-1],16)
    print("get gpstime:%s"%(ctn))
    return(ctn)
    
def set_gpstime_self():
    tt=int(time.mktime(time.localtime()))
    t0=(tt & 0xFFFFFFFF)
    set_gpstime(t0)
 
def set_pps_delay(a0):
    print("set pps delay: %s"%(a0))
    if a0 < 0:
        delay=hex(163839999+a0)
    else:
        delay = hex(a0)
    system("bram -s 10 -a 0x1E -w -v %s"%(delay))

def get_pps_delay():
    cmd=("bram -s 10 -a 0x1E")
    p=Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    result = p.stdout.read().strip().decode()
    line=result.split(":")
    ctn=int(line[-1],16)
    if ctn>819200:
        delay=ctn-163839999
    else:
        delay = ctn
    print("get PPS delay:%s"%(delay))
    return(delay)
   
   
   
