#! /bin/sh
#
# set_addr.sh
# Copyright (C) 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.
#


if [[ $OSTYPE == 'darwin'* ]]; then
  sudo ifconfig en9 ether 00:07:43:11:c0:a0
fi

if [[ $OSTYPE == 'linux'* ]]; then
  sudo ip link set dev enp34s0f0 address 00:07:43:11:c0:a0
fi
