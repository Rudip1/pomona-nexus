#!/usr/bin/env bash
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Install Pomona udev rules to /etc/udev/rules.d/ and reload.
# Required for /dev/DH_hand, /dev/xsens_imu, and RealSense permissions.
# Run on the real robot once after first checkout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UDEV_SRC="$(cd "$SCRIPT_DIR/../udev" && pwd)"

echo "Installing udev rules from $UDEV_SRC"
for rule in "$UDEV_SRC"/*.rules; do
  echo "  → /etc/udev/rules.d/$(basename "$rule")"
  sudo install -m 0644 "$rule" "/etc/udev/rules.d/$(basename "$rule")"
done

echo "Reloading udev …"
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Done. Unplug & replug devices to apply new rules."
