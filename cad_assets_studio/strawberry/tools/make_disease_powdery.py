#!/usr/bin/env python3
# Realistic strawberry POWDERY MILDEW (Podosphaera aphanis) leaf texture:
# white/grey powdery patches over ~50% of the foliage + reddish-purple blotches,
# built from the healthy green leaf diffuse.
import os, numpy as np
from PIL import Image, ImageFilter

TEX = os.path.expanduser("~/pomona_nexus/cad_assets_studio/strawberry/extracted/textures")
leaf = Image.open(os.path.join(TEX, "Strawberry_leaf_diffuse.jpg")).convert("RGB")
arr = np.asarray(leaf, dtype=np.float32) / 255.0
h, w = arr.shape[:2]
rng = np.random.default_rng(11)

# Two-scale powder: COARSE patches (where infection sits, ~55% of area) x
# FINE speckle (the flour-dusting texture). This dusts the leaf itself, not
# just the background, so it's clearly visible on geometry.
def blurred(seed, radius):
    n = np.random.default_rng(seed).random((h, w)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(radius=radius))
    a = np.asarray(im, dtype=np.float32) / 255.0
    return (a - a.min()) / (a.max() - a.min() + 1e-6)

coarse = blurred(11, max(6, w // 18))        # infection patches
fine = blurred(23, 1.2)                       # fine flour speckle
patch = (coarse > np.quantile(coarse, 0.45)).astype(np.float32)   # ~55% area
speckle = np.clip((fine - 0.35) / 0.65, 0, 1)                     # speckly within
alpha = patch * (0.45 + 0.55 * speckle) * 0.95                    # strong on leaf

# powdery white/grey coating
powder = np.array([0.95, 0.96, 0.92], dtype=np.float32)
out = arr * (1 - alpha[..., None]) + powder[None, None, :] * alpha[..., None]

# reddish-purple necrotic blotches scattered around
yy, xx = np.mgrid[0:h, 0:w]
for _ in range(28):
    cy, cx = rng.integers(0, h), rng.integers(0, w)
    r = rng.integers(3, 10)
    m = (yy - cy) ** 2 + (xx - cx) ** 2 < r * r
    out[m] = out[m] * 0.45 + np.array([0.40, 0.12, 0.20]) * 0.55   # purple-red

Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(
    os.path.join(TEX, "leaf_powdery_mildew.jpg"), quality=92)
print("WROTE leaf_powdery_mildew.jpg  (~50% powdery coverage)")
