#!/usr/bin/env bash
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Bring up can0 at 500 kbps (Scout V2 native rate).
# Run on the real robot before launching pomona_bringup.

set -euo pipefail

IFACE="${1:-can0}"
BITRATE="${2:-500000}"

if ! ip link show "$IFACE" >/dev/null 2>&1; then
  echo "Interface $IFACE does not exist. Check that the CAN-to-USB adapter is plugged in."
  echo "Tip: lsusb should show your CAN dongle; dmesg | tail should show it enumerating."
  exit 1
fi

echo "Bringing up $IFACE @ ${BITRATE} bps …"
sudo ip link set "$IFACE" down 2>/dev/null || true
sudo ip link set "$IFACE" type can bitrate "$BITRATE"
sudo ip link set "$IFACE" up

echo "Done."
ip -details link show "$IFACE"
