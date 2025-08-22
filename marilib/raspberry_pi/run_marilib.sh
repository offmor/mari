# === Step 1: Clone or unzip marilib repo ===
cd /home/pi/marilib

# === Step 2: Install marilib ===
sudo chmod +x install_marilib.sh
source install_marilib.sh

# === Step 3: bind the gateway to systemlink port /dev/ttyACM10 ===
cd /home/pi/marilib/raspberry_pi
sudo chmod +x bind_interface.sh
source bind_interface.sh

# === Step 4: create the service to run marilib on boot once the gateway is connected ===
cat <<'EOF' | sudo tee /etc/systemd/system/run_marilib.service

[Unit]
Description=run marilib
#If the gateway disconnects, stop the service
BindsTo=dev-ttyACM10.device
After=dev-ttyACM10.device

[Service]
User=pi
WorkingDirectory=/home/pi/marilib

#refuse to start if the gateway device is missing
ConditionPathExists=/dev/ttyACM10
ExecStartPre=/usr/bin/test -e /dev/ttyACM10

# run basic.py
ExecStart=/usr/bin/tmux new-session -s marilib -d  "/home/pi/marilib/venv/bin/python /home/pi/marilib/examples/basic.py -p /dev/ttyACM10"
ExecStop=/usr/bin/tmux kill-session -t marilib 
Type=forking

Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

# === Step 4:  create a path unit that triggers when the gateway device appears ===
cat <<'EOF' | sudo tee /etc/systemd/system/run_marilib.path
[Unit]
Description=Launch marilib when the gateway appears on /dev/ttyACM10

[Path]
PathExists=/dev/ttyACM10

[Install]
WantedBy=multi-user.target
EOF

# reload systemd units and enable
sudo systemctl daemon-reload
sudo systemctl enable --now run_marilib.path
sudo systemctl enable run_marilib.service