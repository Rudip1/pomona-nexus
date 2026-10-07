#!/usr/bin/env freecadcmd
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Pomona UV-C boom — a properly detailed fixture (not raw overlapping primitives).
# Built in FreeCAD, millimetres, base_link frame. Structure stacks vertically so
# nothing interpenetrates:
#
#   base flange  ->  mast (round tube)  ->  gusseted T-joint  ->  cross-beam
#   cross-beam   ->  drop brackets (one per side, ABOVE the panels)
#   drop bracket ->  reflector pan (downward-open housing)
#   pan end-walls-> lamp holders (tombstones) -> UV-C tubes plugged in
#
# Exports: uvc_frame.stl (grey steel), uvc_lamps.stl (tubes, colour blue),
#          uvc_assembly.stl (everything, for a quick look).

import os
import FreeCAD as App
import Part

V = App.Vector

# ----------------------------------------------------------------- helpers
def box_c(lx, ly, lz, cx, cy, cz):
    """Box of size (lx,ly,lz) centred at (cx,cy,cz)."""
    b = Part.makeBox(lx, ly, lz)
    b.translate(V(cx - lx / 2.0, cy - ly / 2.0, cz - lz / 2.0))
    return b

def cyl_z(r, z0, z1, x, y):
    """Vertical cylinder from z0 to z1 at (x,y)."""
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))

def cyl_x(r, x0, x1, y, z):
    """Cylinder along +X from x0 to x1 at (y,z)."""
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))

def gusset_xz(x_a, z_a, x_b, z_b, x_c, z_c, y_center, thick):
    """Triangular gusset in the XZ plane, extruded 'thick' in Y, centred on y."""
    pts = [V(x_a, y_center - thick / 2.0, z_a),
           V(x_b, y_center - thick / 2.0, z_b),
           V(x_c, y_center - thick / 2.0, z_c),
           V(x_a, y_center - thick / 2.0, z_a)]
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(V(0, thick, 0))

def tube_with_holders(y, z, x0, x1, tube_r, side_solids):
    """One UV-C tube along X + a tombstone holder at each end. Tube returned;
    holders appended to side_solids (steel)."""
    tube = cyl_x(tube_r, x0 + 18, x1 - 18, y, z)        # glass tube between holders
    for hx in (x0, x1 - 16):
        holder = box_c(16, 26, 34, hx + 8, y, z + 2)    # tombstone block
        pin = cyl_x(tube_r + 1.5, hx + 16 - 2, hx + 22, y, z)  # stub the tube plugs into
        side_solids.append(holder.fuse(pin))
    return tube

# ----------------------------------------------------------------- params (mm)
mast_x   = 212.0
flange_z = 280.0          # deck mount height (base_link frame)
flange_t = 10.0
flange_r = 60.0
mast_r   = 25.0
beam_cz  = 560.0          # cross-beam centre — ABOVE the panels (no overlap)
beam_h   = 40.0           # beam section (square)
beam_half_y = 790.0       # beam reaches just past the panels
mast_top = beam_cz - beam_h / 2.0     # mast meets beam underside

panel_y   = 750.0         # panel centre offset (±)
pan_top_z = 502.0         # reflector top-plate centre
pan_x_c   = 65.0
pan_len   = 730.0         # X
pan_wid   = 700.0         # Y
pan_depth = 46.0          # how far walls drop below the top plate
wall_t    = 4.0
lamp_z    = pan_top_z - pan_depth + 14.0   # tubes recessed inside the reflector
tube_r    = 8.0
tube_off  = (270.0, 90.0)  # |Y| offsets of the 4 tubes from a panel centre

frame = []   # grey steel solids
lamps = []   # blue tube solids

# ----------------------------------------------------------------- base flange + mast
flange = cyl_z(flange_r, flange_z, flange_z + flange_t, mast_x, 0)
for ang in (0, 90, 180, 270):
    import math
    bx = mast_x + 42.0 * math.cos(math.radians(ang))
    by = 42.0 * math.sin(math.radians(ang))
    flange = flange.cut(cyl_z(3.5, flange_z - 1, flange_z + flange_t + 1, bx, by))  # bolt holes
frame.append(flange)
frame.append(cyl_z(mast_r, flange_z + flange_t, mast_top + 6, mast_x, 0))   # mast tube (into beam)

# ----------------------------------------------------------------- cross-beam + gussets
frame.append(box_c(beam_h, 2 * beam_half_y, beam_h, mast_x, 0, beam_cz))
# square saddle on top of mast, under the beam, to transition round->rectangular
frame.append(box_c(80, 80, 10, mast_x, 0, mast_top - 1))
# two gussets bracing mast to beam (front & back)
for s in (+1, -1):
    frame.append(gusset_xz(mast_x + s * mast_r, mast_top - 40,
                           mast_x + s * (mast_r + 70), mast_top - 40,
                           mast_x + s * mast_r, mast_top + 30,
                           0, 20))

# ----------------------------------------------------------------- per side: bracket + reflector + lamps
for side in (+1, -1):
    py = side * panel_y
    # drop bracket: post from beam underside down to the pan top (beam is above)
    frame.append(box_c(44, 44, beam_cz - beam_h / 2.0 - pan_top_z + 8,
                       mast_x, py, (beam_cz - beam_h / 2.0 + pan_top_z) / 2.0))
    # small bracket gussets fore/aft on the post
    for s in (+1, -1):
        frame.append(gusset_xz(mast_x + s * 22, pan_top_z + 6,
                               mast_x + s * 60, pan_top_z + 6,
                               mast_x + s * 22, pan_top_z + 70,
                               py, 16))

    # reflector pan: top plate + 4 walls, open at the bottom (faces ground)
    pan = box_c(pan_len, pan_wid, wall_t, pan_x_c, py, pan_top_z)               # top plate
    pan = pan.fuse(box_c(pan_len, wall_t, pan_depth, pan_x_c, py + pan_wid/2 - wall_t/2, pan_top_z - pan_depth/2))
    pan = pan.fuse(box_c(pan_len, wall_t, pan_depth, pan_x_c, py - pan_wid/2 + wall_t/2, pan_top_z - pan_depth/2))
    pan = pan.fuse(box_c(wall_t, pan_wid, pan_depth, pan_x_c + pan_len/2 - wall_t/2, py, pan_top_z - pan_depth/2))
    pan = pan.fuse(box_c(wall_t, pan_wid, pan_depth, pan_x_c - pan_len/2 + wall_t/2, py, pan_top_z - pan_depth/2))
    frame.append(pan)

    # 4 UV-C tubes + tombstone holders at each end
    x0 = pan_x_c - pan_len / 2.0 + wall_t
    x1 = pan_x_c + pan_len / 2.0 - wall_t
    for off in tube_off:
        for s in (+1, -1):
            ty = py + s * off
            lamps.append(tube_with_holders(ty, lamp_z, x0, x1, tube_r, frame))

# ----------------------------------------------------------------- fuse + export
steel = frame[0]
for s in frame[1:]:
    steel = steel.fuse(s)

lamp_compound = Part.makeCompound(lamps)
assembly = Part.makeCompound([steel, lamp_compound])

out = os.path.dirname(os.path.abspath(__file__))
steel.exportStl(os.path.join(out, "uvc_frame.stl"))
lamp_compound.exportStl(os.path.join(out, "uvc_lamps.stl"))
assembly.exportStl(os.path.join(out, "uvc_assembly.stl"))

print("Wrote uvc_frame.stl, uvc_lamps.stl, uvc_assembly.stl")
print("  assembly bbox (mm):", assembly.BoundBox)
print("  steel volume (mm^3): %.0f   tubes: %d" % (steel.Volume, len(lamps)))
