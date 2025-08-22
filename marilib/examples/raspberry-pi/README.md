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