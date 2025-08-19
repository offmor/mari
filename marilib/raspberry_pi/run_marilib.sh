# === Step 1: Clone or unzip marilib repo ===
cd /home/pi/marilib


# === Step 2: Install marilib ===
sudo chmod +x install_marilib.sh
source install_marilib.sh


# === Step 3: create the service to run marilib on boot once the gateway is connected ===
cat <<'EOF' | sudo tee /etc/systemd/system/run_marilib.service

[Unit]
Description=run marilib on tty3 (only when /dev/ttyACM0 exists)
# If the gateway disconnects, stop the service
BindsTo=dev-ttyACM0.device
After=dev-ttyACM0.device

[Service]
User=pi
WorkingDirectory=/home/pi/marilib

# refuse to start if the gateway device is missing
ConditionPathExists=/dev/ttyACM0
ExecStartPre=/usr/bin/test -e /dev/ttyACM0

# attach to tty3 so the TUI is visible
StandardInput=tty
StandardOutput=tty
StandardError=tty
TTYPath=/dev/tty3
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes

# run basic.py
ExecStart=/home/pi/marilib/venv/bin/python /home/pi/marilib/examples/basic.py 
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

# --- create a path unit that triggers when the gateway device appears ---
cat <<'EOF' | sudo tee /etc/systemd/system/run_marilib.path
[Unit]
Description=Launch marilib when the gateway appears on /dev/ttyACM0

[Path]
PathExists=/dev/ttyACM0

[Install]
WantedBy=multi-user.target
EOF

# reload systemd units and enable
sudo systemctl daemon-reload
sudo systemctl enable --now run_marilib.path
sudo systemctl enable run_marilib.service
