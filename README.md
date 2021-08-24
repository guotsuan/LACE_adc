# LACE_adc

ADC data recieving program draft version

## System requirement 
1. set kernel parameters for the maxium buffersize of UDP socket
```
./set_kerenl_params.sh

```
2. Change the mac addr the data was bound to the below mac address (can be changed in the FPGA driver)
```
 sudo ip link set dev enp119s0f0 address 00:07:43:11:c0:a0
```

3. Set the MTU = 9000
```
/usr/bin/ip link set enp119s0f0 mtu 900

```

## Versions

1. Python version: slower than C++ version
2. C++ version: compile
```
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -Wall -Wextra" ../cpp_udp_rec

```
