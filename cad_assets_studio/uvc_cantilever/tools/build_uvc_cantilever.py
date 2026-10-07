#!/usr/bin/env freecadcmd
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Trial: build the Pomona UV-C cantilever + panels in FreeCAD and export a mesh.
# Geometry is the single source of truth from
#   src/pomona_description/urdf/pomona_uvc/xacro/uvc_cantilever.xacro
# (base_link frame). Built here in millimetres (CAD convention); for URDF use
# either scale="0.001 0.001 0.001" on the <mesh>, or regenerate in metres.
#
# Run headless:  freecad.cmd build_uvc_cantilever.py     (snap)
#            or  freecadcmd build_uvc_cantilever.py
#
# Shape (top view): two flat panels each on the end of a cross-arm, on a short
# mast (rod) that sits over the arm-base mount on the deck.

import os
import FreeCAD as App
import Part

MM = 1000.0  # metres -> millimetres

# ---- dimensions (metres), mirrored from uvc_cantilever.xacro ---------------
panel_y_c   = 0.75    # panel centre (bed centre) from robot centreline
panel_width = 0.70    # panel lateral width (Y)
arm_z       = 0.50    # panel plane height (base_link frame)
panel_len   = 0.73    # panel fore-aft length (X)
panel_x_c   = 0.065   # panel fore-aft centre (X)
panel_thick = 0.012   # panel thickness (Z)
beam_w      = 0.035   # cross-arm square section
rod_x       = 0.212   # mast over the arm base
rod_z_bot   = 0.28
arm_top     = arm_z
rod_radius  = 0.025

def box_centered(lx, ly, lz, cx, cy, cz):
    """Axis-aligned box of size (lx,ly,lz) centred at (cx,cy,cz), all metres."""
    b = Part.makeBox(lx * MM, ly * MM, lz * MM)
    b.translate(App.Vector((cx - lx / 2) * MM, (cy - ly / 2) * MM, (cz - lz / 2) * MM))
    return b

# ---- build the parts -------------------------------------------------------
# mast / rod (vertical cylinder from rod_z_bot up to arm_z)
rod = Part.makeCylinder(rod_radius * MM, (arm_top - rod_z_bot) * MM,
                        App.Vector(rod_x * MM, 0, rod_z_bot * MM),
                        App.Vector(0, 0, 1))

# cross-arm spanning out to both panel centres
cross_arm = box_centered(beam_w, 2 * panel_y_c, beam_w, rod_x, 0.0, arm_z)

# the two flat panels
panel_L = box_centered(panel_len, panel_width, panel_thick, panel_x_c,  panel_y_c, arm_z)
panel_R = box_centered(panel_len, panel_width, panel_thick, panel_x_c, -panel_y_c, arm_z)

# fuse into one solid
cantilever = rod.fuse(cross_arm).fuse(panel_L).fuse(panel_R)

# ---- export ----------------------------------------------------------------
out_dir = os.path.dirname(os.path.abspath(__file__))
stl_path = os.path.join(out_dir, "uvc_cantilever.stl")
dae_path = os.path.join(out_dir, "uvc_cantilever.dae")

cantilever.exportStl(stl_path)
print("Wrote STL  ->", stl_path)
print("  bbox (mm):", cantilever.BoundBox)
print("  volume (mm^3): %.1f" % cantilever.Volume)

# DAE (Collada) — needs pycollada; try, but don't fail the run if missing
try:
    import Mesh, MeshPart
    doc = App.newDocument("uvc")
    mesh = MeshPart.meshFromShape(Shape=cantilever, LinearDeflection=2.0, AngularDeflection=0.5)
    mo = doc.addObject("Mesh::Feature", "uvc_cantilever")
    mo.Mesh = mesh
    import importDAE
    importDAE.export([mo], dae_path)
    print("Wrote DAE  ->", dae_path)
except Exception as e:
    print("DAE export skipped (", type(e).__name__, ":", e, ") — STL is fine for URDF")
