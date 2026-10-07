<div align="center">

# 🤖 pomona_description

### URDF / xacro / meshes for **Pomona** — shared by `pomona_gazebo` (sim) and `pomona_bringup` (real robot)

[![ROS 2](https://img.shields.io/badge/ROS%202-Humble-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE)

<br/>

![Pomona UV-C robot model in the description viewer](../../media/robot_demo.gif)

<sub>The <code>pomona_uvc</code> model — Scout V2 base, deck box, and the cantilever UV-C boom. ·
<code>ros2 launch pomona_description display_pomona_uvc.launch.py</code></sub>

</div>

---

URDF / xacro / meshes for **Pomona** — shared by `pomona_gazebo` (sim) and
`pomona_bringup` (real robot). Launch-only package, no nodes.

## Two robot models

The description ships **two self-contained models**, each under
`urdf/<model>/{xacro,urdf}` (xacro source + generated flat URDF):

| Model | Folder | Wheels | UV-C | Used by |
|-------|--------|--------|------|---------|
| **pomona_original** | `urdf/pomona_original/` | stock Scout V2 (radius 0.165, wheelbase 0.498) | none | `pomona_bringup` (real), `display_pomona_original.launch.py`, MoveIt |
| **pomona_uvc** | `urdf/pomona_uvc/` | stock (scale 1.0, wheelbase 0.498 m, track 0.583 m) | front bar + cantilever boom | `pomona_gazebo` (sim) |

Each folder is a full copy of the xacro set, so the two evolve independently.
Regenerate the flat URDFs with `bash scripts/xacro_to_urdf.sh`.

## Robot composition

| Component        | Make / Model            | Xacro file              |
|------------------|-------------------------|-------------------------|
| Mobile base      | AgileX Scout V2         | `scout_v2.xacro`        |
| Wheels (4×)      | scout type1 / type2     | `scout_wheel_type{1,2}.xacro` |
| Mounting box     | white deck cuboid + display | `mount.xacro`       |
| Manipulator      | UFactory xArm6 (6-DOF)  | `xarm6.xacro` (original only) |
| Gripper          | DH Robotics AG95        | `ag95_gripper.xacro` (original only) |
| UV-C boom        | cantilever + lamps      | `uvc_cantilever.xacro` (uvc only) |
| Sensors          | rslidar / Xsens (+ D435 on original) | `sensors.xacro` |
| Sim plugins      | gazebo_ros classic 11   | `gazebo_plugins.xacro`  |
| Sim control      | gazebo_ros2_control     | `ros2_control.xacro` (original, sim only) |
| Root             | combines all above      | `pomona.xacro`          |

> The two models share most of the set. **pomona_original** carries the arm
> (`xarm6.xacro`), gripper (`ag95_gripper.xacro`), D435 camera, and
> `ros2_control.xacro`. **pomona_uvc** drops all of those and adds
> `uvc_cantilever.xacro` instead — so it has no controllers; the boom adds 2 downward D455 cameras over the beds.

`mount.xacro` adds the white box (`box_link`) that physically carries the arm,
LiDAR, and display — ported from the goldmines `scout_xarm_base` package.
`ros2_control.xacro` is included only under `use_sim:=true`; it declares the
`GazeboSystem` hardware and the gazebo_ros2_control plugin (controllers
themselves are configured in `pomona_gazebo/config/gazebo_ros2_control_sim.yaml`).
The real robot (`use_sim:=false`) carries neither plugin block — the physical
arm is driven by vendor `xarm_ros2`.

## Use

### Standalone viewer (no Gazebo, no real robot)
```bash
ros2 launch pomona_description display_pomona_original.launch.py   # stock, no UV-C
ros2 launch pomona_description display_pomona_uvc.launch.py        # stock wheels + UV-C boom
```

### From another package (xacro at launch time)
```python
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

xacro_path = PathJoinSubstitution([
    FindPackageShare("pomona_description"), "urdf", "pomona_original", "xacro", "pomona.xacro"
])
robot_description = ParameterValue(
    Command([FindExecutable(name="xacro"), " ", xacro_path, " use_sim:=true"]),
    value_type=str,
)
```

The single `use_sim:=true/false` switch toggles whether the Gazebo plugin
block is included.

### Pre-baked URDF (for SDF pipeline)
```bash
bash scripts/xacro_to_urdf.sh
# generates, per model, urdf/<model>/urdf/{<model>.urdf, <model>_sim.urdf}
# e.g. urdf/pomona_original/urdf/pomona_original_sim.urdf
```

## Geometry reference

- Scout V2 base: 0.925 × 0.380 × 0.210 m, wheelbase 0.498, track 0.583
- Wheel radius 0.165 m, wheel length 0.117 m, 4 wheels skid-steer
- Mounting box (`box_link`): base_link + xyz=(0,0,0.113)
- xArm6 mount on Scout base: xyz=(0.212, 0, 0.26) — from real robot
- AG95 gripper mount: xArm6 link_eef, zero offset
- D435 camera mount: link_eef + xyz=(0,0,0.06) rpy=(0,-1.57,3.14) (real-robot calibration)
- rslidar mount: box_link + xyz=(0.37655, 0, 0.003) (front of the box)
