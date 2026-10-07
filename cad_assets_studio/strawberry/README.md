# Strawberry plant assets

Textured strawberry plants for the Pomona greenhouse sim — multiple ripeness
states and two diseases, for fruit-picking and **UV-C disinfection** scenarios.

Each plant is a single low-overhead mesh (~17k verts, one visual) so a whole
field instances cheaply. Origin is centered in X/Y with the **base at z = 0**, so
a plant drops straight onto a bed.

## What is (and isn't) in this repository

The plant geometry and its diffuse/normal maps are extracted from a third-party
BlenderKit model ("Strawberry Garden Planter"). Its licence does not permit
redistributing the asset, so **only the processing scripts and render previews
are tracked here**. The generated folders below are listed in `.gitignore`;
rebuild them locally from your own copy of the source model.

## Folder layout

```
strawberry/
├── previews/    preview_<state>.png        render previews (tracked)
├── tools/       strawberry-specific scripts (tracked)
│
│  generated locally, not tracked:
├── extracted/   output of extract_plants_textured.py (+ textures/)
├── source/      strawberry_plants.blend    rebuilt clean master
├── meshes/      strawberry_plant_01..08    the 8 plant SHAPES (obj+mtl+dae+stl)
├── variants/    strawberry_<state>         textured STATE skins (obj+mtl+dae+stl)
└── textures/    master texture set (see below)
```

## Rebuilding

```bash
cd cad_assets_studio
# 1. extract plants + packed textures (never run embedded scripts)
blender --background --disable-autoexec /path/to/source_planter.blend \
  --python strawberry/tools/extract_plants_textured.py -- strawberry/extracted
# 2. recolour berries / generate disease leaves
python3 strawberry/tools/make_variant_textures.py
python3 strawberry/tools/make_disease_powdery.py
# 3. build a clean .blend from the safe OBJ output
blender --background --python tools/obj_to_blend.py -- \
  strawberry/meshes strawberry/source/strawberry_plants.blend "strawberry_plant_0*.obj"
```

TODO: the exact sequence used to produce `variants/` and copy them into
`src/pomona_gazebo/models/strawberry/*/{meshes,textures}` was not recorded;
document it end-to-end.

## Variants (states)

| Variant | Berries | Leaves | Use |
|---|---|---|---|
| `strawberry_ripe`       | red            | healthy green | pickable |
| `strawberry_halfripe`   | pink-white     | healthy green | ripening |
| `strawberry_unripe`     | green          | healthy green | early fruit |
| `strawberry_flower`     | pale (approx*) | healthy green | pre-fruit |
| `strawberry_mildew`     | red            | **powdery mildew** (white dusting + spots) | 🎯 UV-C target |
| `strawberry_leafscorch` | red            | **leaf scorch** (yellow + dark spots) | 2nd disease |

\* `flower` recolors the fruit as an approximation — there is no true blossom
geometry in the source asset (would need new geometry).

### Diseases
- **Powdery mildew** (*Podosphaera aphanis*) — the disease real UV-C robots
  treat on strawberries. White flour-like patches over ~50% of the foliage.
- **Leaf scorch** (*Diplocarpon earlianum*) — yellowing leaves with dark spots.

## Textures (`<part>_<type>`, all lowercase)

```
berry_ripe.jpg  berry_halfripe.jpg  berry_unripe.jpg  berry_flower.jpg
berry_norm.png  berry_ref.jpg
leaf_healthy.jpg  leaf_mildew.jpg  leaf_scorch.jpg  leaf_alpha.jpg  leaf_norm.png
branch_diffuse.jpg  branch_norm.png
```
Material slots inside the meshes: `Branches`, `Leaves`, `Strawberry_1/2/3` (berries).

## Orientation

The source mesh exports Y-up; Gazebo is Z-up. Apply this in the SDF `<pose>`
(rpy) to stand a plant upright (axis map X→Y, Y→Z, Z→X):

```
<pose>0 0 0 1.5708 0 1.5708</pose>
```

## Format notes

- **OBJ + MTL** → textured via `../textures/`. Primary textured format.
- **DAE** → textured, self-contained (references local copies in `variants/`).
- **STL** → geometry only (no color).
- For a Gazebo model, copy the chosen mesh + the textures it uses into
  `src/pomona_gazebo/models/<name>/meshes/` and use `textures/...` paths so it's
  self-contained.

## Tools (`tools/`)

| Script | Does |
|---|---|
| `extract_plants_textured.py` | extract plants from the source planter, re-texture, export |
| `extract_plants.py`          | earlier untextured extract (superseded) |
| `export_textured_obj.py`     | wire diffuse → base color, export textured OBJ+MTL |
| `make_variant_textures.py`   | recolor berries (unripe/half-ripe/flower) |
| `make_disease_powdery.py`    | generate the powdery-mildew leaf texture |
| `regenerate_dark_diseases.py`| regenerate the mildew / scorch leaf textures from `leaf_healthy.jpg` |

(Shared scripts — `render_preview.py`, `obj_to_blend.py`, `obj_to_dae_stl.py`,
`blend_export.py`, `blend_inspect.py` — live in `cad_assets_studio/tools/`.)

## Security note

The original downloaded planter `.blend` contained an auto-running script.
Always open third-party `.blend` files with `--disable-autoexec`, and build the
working `.blend` from the code-free OBJ output (`tools/obj_to_blend.py`).
