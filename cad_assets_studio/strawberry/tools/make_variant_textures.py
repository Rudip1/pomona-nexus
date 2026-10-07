#!/usr/bin/env python3
# Generate recolored strawberry textures for plant-state variants from the
# base diffuse maps, by selective HSV manipulation (only the target hues move).
import os, numpy as np
from PIL import Image

TEX = os.path.expanduser("~/pomona_nexus/cad_assets_studio/strawberry/extracted/textures")
berry = os.path.join(TEX, "Strawberry_diffuse.jpg")
leaf  = os.path.join(TEX, "Strawberry_leaf_diffuse.jpg")


def load_hsv(p):
    rgb = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) / 255.0
    return rgb


def rgb_to_hsv(rgb):
    return np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).convert("HSV"),
                      dtype=np.float32) / 255.0


def hsv_to_rgb(hsv):
    img = Image.fromarray((hsv * 255).astype(np.uint8), mode="HSV").convert("RGB")
    return np.asarray(img, dtype=np.float32) / 255.0


def save(rgb, name):
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(TEX, name), quality=92)
    print("WROTE", name)


# ---------------- BERRIES ----------------
rgb = load_hsv(berry)
hsv = rgb_to_hsv(rgb)
H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
# "red" pixels = hue near 0/1 (wraps) and reasonably saturated
red = ((H < 0.06) | (H > 0.94)) & (S > 0.25)

# UNRIPE: red -> green
h = H.copy()
h[red] = 0.30                      # green hue
out = hsv.copy(); out[..., 0] = h
out[..., 1] = np.where(red, np.clip(S * 0.9, 0, 1), S)
save(hsv_to_rgb(out), "berry_unripe.jpg")

# HALF-RIPE: red -> pink/white (desaturate + brighten the red areas)
out = hsv.copy()
out[..., 1] = np.where(red, S * 0.35, S)
out[..., 2] = np.where(red, np.clip(V * 1.25, 0, 1), V)
save(hsv_to_rgb(out), "berry_halfripe.jpg")

# FLOWERING: berries -> whitish with yellow tint (approx blossoms)
out = hsv.copy()
out[..., 0] = np.where(red, 0.15, H)      # yellow
out[..., 1] = np.where(red, S * 0.25, S)
out[..., 2] = np.where(red, np.clip(V * 1.3, 0, 1), V)
save(hsv_to_rgb(out), "berry_flower.jpg")

# ---------------- LEAVES (diseased) ----------------
rgb = load_hsv(leaf)
hsv = rgb_to_hsv(rgb)
H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
green = (H > 0.18) & (H < 0.45)
out = hsv.copy()
out[..., 0] = np.where(green, 0.12, H)    # green -> yellow
out[..., 1] = np.where(green, np.clip(S * 1.1, 0, 1), S)
out[..., 2] = np.where(green, V * 0.85, V)
dis = hsv_to_rgb(out)
# add random brown necrotic spots
rng = np.random.default_rng(7)
hh, ww = dis.shape[:2]
yy, xx = np.mgrid[0:hh, 0:ww]
for _ in range(40):
    cy, cx = rng.integers(0, hh), rng.integers(0, ww)
    r = rng.integers(4, 14)
    m = (yy - cy) ** 2 + (xx - cx) ** 2 < r * r
    dis[m] = dis[m] * 0.35 + np.array([0.30, 0.18, 0.05]) * 0.65
save(dis, "leaf_diseased.jpg")
print("DONE")
