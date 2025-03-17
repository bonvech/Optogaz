##  from LVS
from optogaz_device import Optogaz_device
import time


timeout = 60 ## sec
try:
    ##  Create and init device
    device = Optogaz_device()
    
    ##  Connect to device
    if device.connect():
        exit()
    time.sleep(1)

    ##  Main loop
    while True:
        device.request()
        time.sleep(timeout)

    device.unconnect()
    device.write_to_bot(f"{device.device_name}: Miracle! The undless while stopped!")
except Exception as error:
    device.write_to_bot(f"{device.device_name}: Error in main programm: {error}")

#x = input()
