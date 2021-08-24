#! /bin/sh
#
# set_kerenl_params.sh
# Copyright (C) 2021 gq <gq@gqhp>
#
# Distributed under terms of the MIT license.
#

sudo sysctl -w net.core.rmem_max=1610612736
sudo sysctl -w net.core.wmem_max=1610612736
sudo sysctl -w net.core.netdev_max_backlog=65536

