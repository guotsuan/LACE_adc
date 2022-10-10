# LACE_adc

ADC data recieving program draft (Python) version

## System requirement 
1. check_system.py will set kernel parameters and update the setting of Receiver accordingly
```
python check_system.py
```

## Collecting and Saving data
2. Collecting and Saveing file with spectrum of fft: raw_rx_fft5.py and raw_rx_fft6.py
```
 ./raw_rx_fft6.py 0 /data/test13/
```

3. Collecting and Saving raw sample data: raw_rx3.py
```
 ./raw_rx3.py 0 /data/raw1/
```

## Versions

1. Python version:  is working
2. C++ version: compile
```
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -Wall -Wextra" ../cpp_udp_rec

```
