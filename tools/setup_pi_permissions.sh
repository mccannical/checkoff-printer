#!/bin/bash

# setup_pi_permissions.sh
# Run this with sudo: sudo ./tools/setup_pi_permissions.sh

set -e

PRINTER_USER="printer"
PROJECT_DIR="/home/printer/checkoff-printer"
SUDOERS_FILE="/etc/sudoers.d/checkoff-printer"
UDEV_FILE="/etc/udev/rules.d/99-printer.rules"

echo "🔧 Starting permissions setup for $PRINTER_USER..."

# 1. Ensure user is in necessary groups
echo "👥 Adding $PRINTER_USER to lp, dialout, and video groups..."
usermod -a -G lp,dialout,video $PRINTER_USER

# 2. Fix directory ownership
echo "📂 Fixing ownership of $PROJECT_DIR..."
chown -R $PRINTER_USER:$PRINTER_USER $PROJECT_DIR

# 3. Setup udev rule for Epson Thermal Printer (Vendor ID 04b8)
echo "🔌 Creating udev rule for USB printer access..."
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04b8", MODE="0666", GROUP="lp"' > $UDEV_FILE
udevadm control --reload-rules
udevadm trigger

# 4. Setup Passwordless Sudo for service management
echo "🔐 Configuring sudoers for service management..."
echo "$PRINTER_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart checkoff-printer" > $SUDOERS_FILE
echo "$PRINTER_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl status checkoff-printer" >> $SUDOERS_FILE
chmod 440 $SUDOERS_FILE

echo "✅ Setup complete!"
echo "⚠️  Note: You may need to logout and log back in for group changes to take effect."
echo "🔌 Note: Unplug and replug the USB printer to apply the new udev rules."
