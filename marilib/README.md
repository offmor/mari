# MariLib 💫 👀 🐍

MariLib is a Python library to interact with a local [Mari](https://github.com/DotBots/mari) network.
It connects to a Mari gateway via UART.

## Example with TUI
MariLib provides a stateful class with gateway and node information, network statistics, and a rich real-time TUI:

[mari-edge-2.webm](https://github.com/user-attachments/assets/fe50f2ba-8e67-4522-8700-69730f8e3aee)

See the how it works in `examples/basic.py`.

## Minimal example
Here is a minimal example showcasing how to use MariLib:

```python
import time
from marilib.marilib import MariLib
from marilib.serial_uart import get_default_port

def main():
    mari = MariLib(lambda event, data: print(event.name, data), get_default_port())
    while True:
        for node in mari.gateway.nodes:
            mari.send_frame(dst=node.address, payload=b"A" * 3)
        statistics = [(f"{node.address:016X}", node.stats.received_rssi_dbm()) for node in mari.gateway.nodes]
        print(f"Network statistics: {statistics}")
        time.sleep(0.25)

if __name__ == "__main__":
    main()
```
See it in action in `examples/minimal.py`.


## Getting Started
### Step 1: Flash Operating System to the micro-SD card

Depending on your computer operating system, the installation procedure can change. 
Please follow the instruction on the Raspbian website: https://www.raspberrypi.com/software/

From the link above download and install the Raspberry Pi Imager.

In the Raspberry Pi Imager select:
- Device           - Raspberry Pi 5,  
- Operating System - Raspberry Pi OS (64-BIT)
- Storage          - micro-SD card 64 GO 

After flashing, insert the micro-SD into the Raspberry Pi. 
Power ON the Raspberry and connect it to a screen with an HDMI cable, and connect a mouse and a keyboard.

On the first boot of the OS you need to fill in the location and language info, username and password.

For the username type: `pi`
For the password type: `raspberry`

Then install the updates with:
```
sudo apt update
sudo apt upgrade
```

### Step 2: Install Marilib repository

NOTE: this repository needs to be cloned or unzipped in `/home/pi/marilib`

### Step 3: Run Marilib 

We run marilib on the Raspberry Pi inside a systemd service
to run on boot after detecting that the gateway is connected.

To install the service on Raspberry Pi run this once:
```
cd /home/pi/marilib/raspberry_pi
sudo chmod +x run_marilib.sh
source run_marilib.sh
```

To launch the TUI:
```
until tmux has-session -t marilib 2>/dev/null; do sleep 0.2; done; tmux attach -t marilib
```