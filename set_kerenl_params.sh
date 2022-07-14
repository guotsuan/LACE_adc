#! /bin/sh
#
# set_kerenl_params.sh
# Copyright (C) 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.
#

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

  sudo netctl stop enp10s0f0
  sudo netctl stop enp10s0f1
  sudo ip link set enp10s0f1 txqueuelen 10000
  sudo ip link set enp10s0f0 txqueuelen 10000
  sudo ethtool -G enp10s0f0 rx 4096
  sudo ethtool -G enp10s0f1 rx 4096
  sudo netctl start enp10s0f0
  sudo netctl start enp10s0f1

fi

#sudo ethtool -G enp10s0f0 rx 4096
#sudo ethtool -G enp10s0f1 rx 4096

