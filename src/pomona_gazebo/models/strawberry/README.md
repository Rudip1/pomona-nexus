# strawberry — Gazebo models

Six **static, textured** strawberry plant models, promoted from
`cad_assets_studio/strawberry`. Each is `model.config` + `model.sdf` + `meshes/`
+ `textures/`, upright (pose `1.5708 0 1.5708` baked in), no collision.

| Model | State |
|---|---|
| `strawberry_ripe` | red berries (pickable) |
| `strawberry_halfripe` | pink-white berries |
| `strawberry_unripe` | green berries |
| `strawberry_flower` | flowering |
| `strawberry_mildew` | powdery mildew — UV-C target |
| `strawberry_leafscorch` | leaf scorch |

> **Meshes and textures are not included in this repository.** They are
> derived from a third-party BlenderKit model whose licence does not allow
> redistribution of the asset itself. Only `model.config` / `model.sdf` are
> tracked. Rebuild `meshes/` and `textures/` locally with the scripts in
> `cad_assets_studio/strawberry/tools/` from your own copy of the source model
> (see `cad_assets_studio/strawberry/README.md`). Without them the plants in
> `strawberry_farm.world` have no geometry; the beds, ground and hedge are
> generated procedurally and are included.

Reference as `model://strawberry_<state>` (add this dir to `GAZEBO_MODEL_PATH` —
it is two levels under `models/`). Scene world: `worlds/strawberry_farm.world`.
Pipeline + sources: `cad_assets_studio/strawberry/`.
