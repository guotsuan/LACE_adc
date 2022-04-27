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
  sudo sysctl -w net.core.wmem_max=1610612736
  sudo sysctl -w net.core.netdev_max_backlog=300000
fi

