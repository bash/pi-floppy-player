#!/usr/bin/env bash

set -e

if [[ -z "$SKIP_DEPS" ]]
then
    # Install dependencies
    sudo apt-get install -y python3-pyudev python3-gi mplayer
fi

# Enable user linger so that our user service
# is started on boot and kept around.
loginctl enable-linger "$USER"

INSTALL_DIR="$HOME/.local/opt/floppy-player"
mkdir -p "$INSTALL_DIR"
cp -R {player.py,floppy_player} "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/player.py"

SERVICES_DIR="$HOME/.config/systemd/user/"
mkdir -p "$SERVICES_DIR"
envsubst < floppy-player.service.in > "$SERVICES_DIR/floppy-player.service"

# We need our own polkit rule, because filesystem-mount is not allowed
# by default on raspberry pi os.
sudo cp etc/polkit-1/rules.d/50-floppy-player.rules /etc/polkit-1/rules.d/
sudo chmod 644 /etc/polkit-1/rules.d/50-floppy-player.rules

# Enable and start service
systemctl enable --now --user floppy-player
