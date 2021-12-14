#! /bin/sh
#
# set_addr.sh
# Copyright (C) 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.
#

dev="enp119s0f0"
#addr="24:5e:be:59:8d:46"
#addr="00:1b:21:bb:d0:ac"
addr="00:1b:21:85:6e:a1"

if [[ $OSTYPE == 'darwin'* ]]; then
  sudo ifconfig en9 ether $addr
fi

if [[ $OSTYPE == 'linux'* ]]; then
  sudo ip link set dev ${dev} address $addr
fi
