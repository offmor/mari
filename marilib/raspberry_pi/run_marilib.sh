# === Step 1: Clone or unzip marilib repo ===
cd /home/pi/marilib


# === Step 2: Install marilib ===
sudo chmod +x install_marilib.sh
source install_marilib.sh


# === Step 3: create the service to run marilib on boot once the gateway is connected ===
cat <<'EOF' | sudo tee /etc/systemd/system/run_marilib.service

[Unit]
Description=run marilib
#If the gateway disconnects, stop the service
BindsTo=dev-ttyACM0.device
After=dev-ttyACM0.device

[Service]
User=pi
WorkingDirectory=/home/pi/marilib

#refuse to start if the gateway device is missing
ConditionPathExists=/dev/ttyACM0
ExecStartPre=/usr/bin/test -e /dev/ttyACM0

# run basic.py
ExecStart=/usr/bin/tmux new-session -A -s marilib -d  "/home/pi/marilib/venv/bi>
ExecStop=/usr/bin/tmux kill-session -t marilib
Type=forking

Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

# reload systemd units and enable
sudo systemctl daemon-reload
sudo systemctl enable --now run_marilib.path
sudo systemctl enable run_marilib.service
