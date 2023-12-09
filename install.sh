#!/usr/bin/env bash

set -e

# Install dependencies
sudo apt-get install -y python3-pyudev python3-gi mplayer

# Enable user linger so that our user service
# is started on boot and kept around.
loginctl enable-linger "$USER"

BIN_DIR="$HOME/.local/bin/"
mkdir -p "$BIN_DIR"
cp player.py "$BIN_DIR/floppy-player"
chmod +x "$BIN_DIR/floppy-player"

SERVICES_DIR="$HOME/.config/systemd/user/"
mkdir -p "$SERVICES_DIR"
envsubst < floppy-player.service.in > "$SERVICES_DIR/floppy-player.service"

# We need our own polkit rule, because filesystem-mount is not allowed
# by default on raspberry pi os.
sudo cp etc/polkit-1/rules.d/50-floppy-player.rules /etc/polkit-1/rules.d/
sudo chmod 644 /etc/polkit-1/rules.d/50-floppy-player.rules

# Enable and start service
systemctl enable --now --user floppy-player
