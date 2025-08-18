# --- create the service to run marilib on boot once the gateway is connected ---
cat << EOF | sudo tee /etc/systemd/system/run_marilib.service
[Unit]
Description=run marilib
# If the device goes away, stop the service
BindsTo=dev-ttyACM0.device
After=dev-ttyACM0.device

[Service]
WorkingDirectory=/home/pi/marilib
#refuse to start if the device is missing
ConditionPathExists=/dev/ttyACM0

ExecStartPre=/usr/bin/test -e /dev/ttyACM0
ExecStart=/home/pi/marilib/venv/bin/python /home/pi/marilib/examples/basic.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

# --- create a path unit that triggers when the device appears ---
cat << EOF | sudo tee /etc/systemd/system/run_marilib.path
[Unit]
Description=Launch marilib when the gateway appears on the default port /dev/ttyACM0 

[Path]
# fire when the gateway device shows up
PathExists=/dev/ttyACM0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start run_marilib.path
sudo systemctl enable --now run_marilib.path
