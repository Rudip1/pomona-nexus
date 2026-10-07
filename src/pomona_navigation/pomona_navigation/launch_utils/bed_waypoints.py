# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
# =============================================================================
# pomona_navigation / launch_utils / bed_waypoints.py
# =============================================================================
# Generates the UV-C bed-disinfection waypoint mission for the pinwheel
# strawberry farm (pomona_gazebo/worlds/strawberry/generate_strawberry_farm.py).
#
# FARM GEOMETRY (must match the world generator)
#   6 beds per quadrant, bed pitch 2.0 m, bed length 10 m, aisle offset 1.0 m.
#   Bed centre coordinates along the across-axis:  s = 1.5, 3.5, 5.5, 7.5, 9.5, 11.5
#   Beds span the along-axis from CENTER-5 to CENTER+5 = 1.0 .. 11.0 m.
#
# DISINFECTION LANES
#   The UV-C boom carries two downward panels at y = ±1.0 m (robot frame), so a
#   single pass centred between a PAIR of beds disinfects BOTH at once. The three
#   lane centres per quadrant sit on the furrows between bed pairs:
#       lane = midpoint(s_i, s_{i+1}) = 2.5, 6.5, 10.5   (covers 6 beds in 3 passes)
#
# QUADRANT ORIENTATION (pinwheel)
#   Q1 top-right   : beds along Y at x=s     → lanes vary X, drive along Y
#   Q2 top-left    : beds along Y at x=-s    → lanes vary X, drive along Y
#   Q3 bottom-left : beds along X at y=-s    → lanes vary Y, drive along X
#   Q4 bottom-right: beds along X at y=-s    → lanes vary Y, drive along X
#
# MISSION
#   Start at spawn (0,0) → Q1 → Q2 → Q3 → Q4 (counter-clockwise) → back to spawn.
#   Each quadrant is swept serpentine (alternating lane direction) so the robot
#   never doubles back empty. Poses are (x, y, yaw) with yaw = travel heading.
# =============================================================================

import math

# ── farm constants (keep in sync with generate_strawberry_farm.py) ───────────
BEDS_PER_QUADRANT = 6
BED_LEN = 10.0
FURROW = 1.0
BED_W = 1.0
AISLE = 2.0
BED_PITCH = BED_W + FURROW          # 2.0
OFF = AISLE / 2.0                   # 1.0
CENTER = OFF + BED_LEN / 2.0        # 6.0

# bed centres across the quadrant, then lane centres between bed PAIRS
_S = [OFF + BED_W / 2.0 + i * BED_PITCH for i in range(BEDS_PER_QUADRANT)]  # 1.5..11.5
LANES = [(_S[i] + _S[i + 1]) / 2.0 for i in range(0, BEDS_PER_QUADRANT, 2)]  # 2.5,6.5,10.5

ALONG_MIN = CENTER - BED_LEN / 2.0  # 1.0  — bed start along its length
ALONG_MAX = CENTER + BED_LEN / 2.0  # 11.0 — bed end

# small standoff so the robot enters/exits just clear of the bed ends
END_PAD = 0.5
A0 = ALONG_MIN - END_PAD            # 0.5
A1 = ALONG_MAX + END_PAD           # 11.5

HOME = (0.0, 0.0, 0.0)

NORTH = math.pi / 2.0
SOUTH = -math.pi / 2.0
EAST = 0.0
WEST = math.pi


def _serpentine(lanes, along_lo, along_hi):
    """Yield (entry, exit) along-coordinates per lane, alternating direction."""
    for k, _lane in enumerate(lanes):
        if k % 2 == 0:
            yield along_lo, along_hi
        else:
            yield along_hi, along_lo


def _quadrant_poses(quadrant):
    """Return the ordered (x, y, yaw) list for one quadrant."""
    poses = []
    if quadrant == 1:        # top-right: lanes on +X, drive along +Y
        lanes = LANES
        for lane_x, (a_in, a_out) in zip(lanes, _serpentine(lanes, A0, A1)):
            yaw = NORTH if a_out > a_in else SOUTH
            poses += [(lane_x, a_in, yaw), (lane_x, a_out, yaw)]
    elif quadrant == 2:      # top-left: lanes on -X, drive along +Y
        lanes = [-l for l in LANES]
        for lane_x, (a_in, a_out) in zip(lanes, _serpentine(lanes, A1, A0)):
            yaw = NORTH if a_out > a_in else SOUTH
            poses += [(lane_x, a_in, yaw), (lane_x, a_out, yaw)]
    elif quadrant == 3:      # bottom-left: lanes on -Y, drive along -X
        lanes = [-l for l in LANES]
        for lane_y, (a_in, a_out) in zip(lanes, _serpentine(lanes, -A0, -A1)):
            yaw = WEST if a_out < a_in else EAST
            poses += [(a_in, lane_y, yaw), (a_out, lane_y, yaw)]
    elif quadrant == 4:      # bottom-right: lanes on -Y, drive along +X
        lanes = [-l for l in LANES]
        for lane_y, (a_in, a_out) in zip(lanes, _serpentine(lanes, A1, A0)):
            yaw = EAST if a_out > a_in else WEST
            poses += [(a_in, lane_y, yaw), (a_out, lane_y, yaw)]
    return poses


def mission_waypoints(quadrants=(1, 2, 3, 4), return_home=True):
    """Full disinfection mission as an ordered list of (x, y, yaw_rad).

    Start is the caller's current pose (not included). Sweeps each quadrant's
    three lanes serpentine, then optionally returns to the spawn origin.
    """
    poses = []
    for q in quadrants:
        poses += _quadrant_poses(q)
    if return_home:
        poses.append(HOME)
    return poses


if __name__ == "__main__":
    wps = mission_waypoints()
    print(f"{len(wps)} waypoints (lanes per quadrant: {LANES})")
    for i, (x, y, yaw) in enumerate(wps):
        print(f"  {i:2d}: x={x:6.2f}  y={y:6.2f}  yaw={math.degrees(yaw):+6.1f}deg")
