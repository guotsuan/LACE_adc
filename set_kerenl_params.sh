#! /bin/sh
#
# set_kerenl_params.sh
# Copyright (C) 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.
#


if [ $# -eq 0 ] 
then 
  echo "Usage $0 NIC1 NIC2 ...."
else
  NIC=$*
fi

if [[ $OSTYPE == 'darwin'* ]]; then
  # mac pro MAX, maxspace=7168000
  sudo sysctl -w net.inet.udp.recvspace=7168000
fi

if [[ $OSTYPE == 'linux'* ]]; then
  sudo sysctl -w net.core.rmem_max=1610612736
#  sudo sysctl -w net.core.wmem_max=1610612736
  sudo sysctl -w net.core.netdev_max_backlog=300000
  sudo sysctl -w net.core.optmem_max=1020000 
  sudo sysctl -w net.ipv4.udp_mem="11416320 15221760 22832640"

  for i in $NIC
  do
    echo "adjusting 10G NIC $i, should be set during the startup of NIC"
    sudo netctl stop $i
    sudo ip link set $i txqueuelen 10000
    sudo ethtool -G $i rx 8184
    sudo netctl start $i
  done
fi

#sudo ethtool -G enp10s0f0 rx 4096
#sudo ethtool -G enp10s0f1 rx 4096

