#!/usr/bin/env bash
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Regenerate flat URDFs from the xacro single source of truth.
# Useful for the SDF pipeline (pomona_gazebo/models/pomona/model.sdf) and for
# offline inspection (urdf/urdf/pomona.urdf is gitignore-safe).
#
# Usage:  bash scripts/xacro_to_urdf.sh
#         (run from this package source dir, or anywhere if ROS env is sourced)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Two robot models, each self-contained under urdf/<model>/{xacro,urdf}:
#   pomona_original — stock Scout V2 wheels, no UV-C (real-robot-accurate)
#   pomona_uvc      — sim: oversized wheels + cantilever UV-C boom
for MODEL in pomona_original pomona_uvc; do
  XACRO_ROOT="$PKG_DIR/urdf/$MODEL/xacro/pomona.xacro"
  OUT_DIR="$PKG_DIR/urdf/$MODEL/urdf"
  mkdir -p "$OUT_DIR"
  echo "[xacro] $MODEL/urdf/${MODEL}.urdf      (use_sim:=false)"
  xacro "$XACRO_ROOT" use_sim:=false > "$OUT_DIR/${MODEL}.urdf"
  echo "[xacro] $MODEL/urdf/${MODEL}_sim.urdf  (use_sim:=true)"
  xacro "$XACRO_ROOT" use_sim:=true  > "$OUT_DIR/${MODEL}_sim.urdf"
done

echo "Generated:"
ls -la "$PKG_DIR"/urdf/pomona_*/urdf/
