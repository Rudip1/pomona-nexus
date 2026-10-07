#!/usr/bin/env freecadcmd
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Pomona UV-C boom — STRUCTURE + LAMP HOUSING (no lamps; tubes added in xacro).
# FreeCAD, millimetres, base_link frame.
#
#   short mast (round, minimum length) -> gusseted saddle -> cross-beam
#   beam -> short connector -> lamp housing (per side)
#
# Lamp housing = a rectangular box OPEN AT THE BOTTOM: closed top plate (lamp
# mounting ceiling) + two DEEP long side walls (light shield) + two SHORT end
# walls. UV-C escapes only downward onto the bed. You add the tubes inside it.
#
# Tunables are grouped at the top. Export: uvc_housing.stl

import os, math
import FreeCAD as App
import Part

V = App.Vector

def box_c(lx, ly, lz, cx, cy, cz):
    b = Part.makeBox(lx, ly, lz)
    b.translate(V(cx - lx / 2.0, cy - ly / 2.0, cz - lz / 2.0))
    return b

def cyl_z(r, z0, z1, x, y):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))

def gusset_xz(xa, za, xb, zb, xc, zc, yc, thick):
    pts = [V(xa, yc - thick / 2.0, za), V(xb, yc - thick / 2.0, zb),
           V(xc, yc - thick / 2.0, zc), V(xa, yc - thick / 2.0, za)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, thick, 0))

# ============================ TUNABLES (mm) ============================
MAST_LEN   = 380.0    # round-bar height above the flange (raised for a 0.40 m bed)
END_SKIRT  = 60.0     # depth of the two short end walls (open-ish for the row)
HOUSING_LEN = 730.0   # X  (along the row)
HOUSING_WID = 700.0   # Y  (across the bed)

# ---- the shield BOTTOM is pinned to a safe height above the canopy; its DEPTH
#      then follows from how high the lamp sits (which depends on MAST_LEN).
#      shield_bottom_AGL = bed + plant + clearance   (never crashes the plants)
#      skirt_depth       = lamp_AGL - shield_bottom_AGL
#      -> raise the lamp (longer mast / higher mount) to get a deeper shield.
GROUND_Z_BL = -0.235  # ground (base_footprint) in base_link = wheel_off - wheel_r
BED_H       = 0.40    # raised bed / grow-gutter height          [SITE  — edit me]
PLANT_H     = 0.22    # full-grown strawberry plant height       [SITE  — edit me]
CLEARANCE   = 0.13    # safe vertical gap shield->canopy         [SAFETY — edit me]
# (SIDE_SKIRT is computed below, once the lamp height is known from MAST_LEN.)
# =======================================================================

mast_x   = 212.0
flange_z = 280.0
flange_t = 10.0
flange_r = 60.0
mast_r   = 25.0
beam_h   = 40.0
beam_half_y = 790.0
panel_y  = 750.0
hous_x_c = 65.0
wall_t   = 4.0

mast_top = flange_z + flange_t + MAST_LEN
beam_cz  = mast_top + beam_h / 2.0
top_z    = mast_top - 2.0          # housing ceiling sits just under the beam

# lamp height above ground follows from the geometry (so it tracks MAST_LEN);
# pin the shield bottom safely above the canopy and let the depth follow.
lamp_agl          = top_z / 1000.0 - GROUND_Z_BL
canopy_top_agl    = BED_H + PLANT_H
shield_bottom_agl = canopy_top_agl + CLEARANCE
SIDE_SKIRT        = (lamp_agl - shield_bottom_agl) * 1000.0     # -> mm
assert SIDE_SKIRT > 0, ("Lamp at %.3f m AGL is too low for canopy+clearance "
                        "(%.3f m) — raise MAST_LEN." % (lamp_agl, shield_bottom_agl))

parts = []

# ---- base flange (mates to your base_link STL) + short mast ----
flange = cyl_z(flange_r, flange_z, flange_z + flange_t, mast_x, 0)
for ang in (0, 90, 180, 270):
    bx = mast_x + 42.0 * math.cos(math.radians(ang))
    by = 42.0 * math.sin(math.radians(ang))
    flange = flange.cut(cyl_z(3.5, flange_z - 1, flange_z + flange_t + 1, bx, by))
parts.append(flange)
parts.append(cyl_z(mast_r, flange_z + flange_t, mast_top + 6, mast_x, 0))   # short mast

# ---- cross-beam + round->square saddle + gussets ----
parts.append(box_c(beam_h, 2 * beam_half_y, beam_h, mast_x, 0, beam_cz))
parts.append(box_c(80, 80, 10, mast_x, 0, mast_top - 1))
for s in (+1, -1):
    parts.append(gusset_xz(mast_x + s * mast_r, mast_top - 35,
                           mast_x + s * (mast_r + 55), mast_top - 35,
                           mast_x + s * mast_r, mast_top + 20, 0, 18))

# ---- per side: short connector + rectangular lamp housing ----
def side_wall(cx, cy, length_x, depth):
    return box_c(length_x, wall_t, depth, cx, cy, top_z - depth / 2.0 + wall_t / 2.0)

def end_wall(cx, cy, depth):
    return box_c(wall_t, HOUSING_WID, depth, cx, cy, top_z - depth / 2.0 + wall_t / 2.0)

for side in (+1, -1):
    py = side * panel_y
    # short connector from beam underside to housing ceiling (beam is right above)
    parts.append(box_c(44, 44, (beam_cz - beam_h / 2.0) - top_z + 6,
                       mast_x, py, ((beam_cz - beam_h / 2.0) + top_z) / 2.0))

    # housing: top plate (lamp ceiling)
    h = box_c(HOUSING_LEN, HOUSING_WID, wall_t, hous_x_c, py, top_z)
    # two DEEP long side walls (light shield)
    h = h.fuse(side_wall(hous_x_c, py + HOUSING_WID / 2 - wall_t / 2, HOUSING_LEN, SIDE_SKIRT))
    h = h.fuse(side_wall(hous_x_c, py - HOUSING_WID / 2 + wall_t / 2, HOUSING_LEN, SIDE_SKIRT))
    # two SHORT end walls (define the box; bed still passes through underneath)
    h = h.fuse(end_wall(hous_x_c + HOUSING_LEN / 2 - wall_t / 2, py, END_SKIRT))
    h = h.fuse(end_wall(hous_x_c - HOUSING_LEN / 2 + wall_t / 2, py, END_SKIRT))
    parts.append(h)

asm = parts[0]
for p in parts[1:]:
    asm = asm.fuse(p)

out = os.path.dirname(os.path.abspath(__file__))
asm.exportStl(os.path.join(out, "uvc_housing.stl"))
print("Wrote uvc_housing.stl")
print("  bbox (mm):", asm.BoundBox)
print("  --- shield math (AGL, metres) ---")
print("  lamp panel (from MAST_LEN=%.0f): %.3f" % (MAST_LEN, lamp_agl))
print("  canopy top (bed %.2f + plant %.2f): %.3f" % (BED_H, PLANT_H, canopy_top_agl))
print("  shield bottom (canopy+clearance): %.3f" % shield_bottom_agl)
print("  -> SIDE_SKIRT depth = %.0f mm   (clearance above canopy = %.0f mm)"
      % (SIDE_SKIRT, CLEARANCE * 1000.0))
print("  END_SKIRT=%.0f  volume=%.0f mm^3" % (END_SKIRT, asm.Volume))
