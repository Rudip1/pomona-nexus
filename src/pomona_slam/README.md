<div align="center">

# 🍓 pomona_slam

### 2D LiDAR mapping & localization for the **Pomona** greenhouse robot

*Drive the furrows, build the map, then relocalize on it — in Gazebo or on the real Scout V2.*

[![ROS 2](https://img.shields.io/badge/ROS%202-Humble-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![SLAM Toolbox](https://img.shields.io/badge/SLAM-Toolbox-5B8DEF)](https://github.com/SteveMacenski/slam_toolbox)
[![Gazebo](https://img.shields.io/badge/Gazebo-Classic%2011-FF6C2C?logo=gazebo&logoColor=white)](https://classic.gazebosim.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE)

<br/>

![Pomona mapping the strawberry farm in Gazebo](../../media/slam_demo.gif)

<sub>Live online mapping — <code>pomona_uvc</code> driving the strawberry farm while SLAM Toolbox grows the occupancy grid in RViz.</sub>

</div>

---

## ✨ What's inside

`pomona_slam` wraps [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox) (Ceres backend)
into three ready-to-run modes, each backed by a tuned config:

| Mode | Launch | Config | Use it for |
|---|---|---|---|
| 🗺️ **Online mapping** | `slam.launch.py` | `slam_toolbox_online_async.yaml` | Drive around live and build the map |
| 📍 **Localization** | `localization.launch.py` | `slam_toolbox_localization.yaml` | Relocalize on a *saved* map (no re-mapping) |
| 🎞️ **Offline replay** | `slam.launch.py params_file:=…offline.yaml` | `slam_toolbox_offline.yaml` | Re-process a recorded rosbag, fast |

One knob switches sim ↔ real for **every** mode:

```bash
use_sim_time:=true     # Gazebo  (clock from /clock)
use_sim_time:=false    # real robot (system clock)
```

The input is always **`/scan`** (a 360° 2D `sensor_msgs/LaserScan`) — published by the
`gazebo_ros_ray_sensor` plugin in sim, and by the Robosense driver on hardware — so the
SLAM side is identical in both worlds.

---

## 🚀 Quickstart — map the farm in Gazebo

Three terminals, each `source install/setup.bash` first.

```bash
# 1 — World + robot + teleop  (Scout V2 + UV-C boom on the strawberry beds)
ros2 launch pomona_gazebo strawberry_farm.launch.py

# 2 — SLAM Toolbox + RViz (preloaded slam.rviz view)
ros2 launch pomona_slam slam.launch.py use_sim_time:=true use_rviz:=true

# 3 — Save the map once you're happy with the coverage
ros2 launch pomona_slam save_map.launch.py map_name:=strawberry_farm
```

> 💡 **Drive for loop closure.** Sweep *down each furrow and back along the cross-aisle*
> so the graph revisits earlier poses — that's what lets SLAM Toolbox snap the map
> straight instead of letting odometry drift bend the rows.

### The result

<div align="center">

<img src="../../media/strawberry_farm_map.png" alt="Occupancy grid of the strawberry farm" width="60%"/>

<sub>`maps/strawberry_farm.pgm` rendered as PNG — 563 × 401 cells at 0.05 m/cell.</sub>

</div>

---

## 💾 Saving maps

Maps are written into **`pomona_slam/maps/`** by default (so they live with the package
and can be committed), regardless of which directory you launch from:

```bash
ros2 launch pomona_slam save_map.launch.py map_name:=strawberry_farm
#   → maps/strawberry_farm.pgm   (occupancy image)
#   → maps/strawberry_farm.yaml  (resolution, origin, thresholds)

# Override the destination if you need to:
ros2 launch pomona_slam save_map.launch.py map_name:=demo maps_dir:=/tmp/maps
```

| Arg | Default | Meaning |
|---|---|---|
| `map_name` | `pomona_map` | Output basename → `<name>.pgm` + `<name>.yaml` |
| `maps_dir` | `pomona_slam/maps/` | Directory to write into |

---

## 📍 Localizing on a saved map

Bring up the world (or the real robot), then start SLAM Toolbox in **localization** mode
against a map you saved earlier:

```bash
ros2 launch pomona_slam localization.launch.py \
    use_sim_time:=true \
    map:=$PWD/src/pomona_slam/maps/strawberry_farm
```

It loads the serialized pose-graph, matches incoming `/scan` against it, and publishes the
`map → odom` correction — **no new map is built**. Give it an initial pose in RViz
(*2D Pose Estimate*) if it starts away from where the robot really is.

| Arg | Default | Meaning |
|---|---|---|
| `map` | `maps/placeholder` | Saved map basename (no extension) |
| `use_sim_time` | `false` | `true` in Gazebo |
| `params_file` | `…localization.yaml` | Override the SLAM config |

---

## 🌳 TF tree

SLAM Toolbox consumes `odom → base_footprint` (from the diff-drive plugin / wheel
odometry) and publishes the `map → odom` correction on top:

```
  map ──(slam_toolbox)──► odom ──► base_footprint ──► base_link ──┬─► rslidar   (/scan)
                                                                  ├─► imu_link
                                                                  └─► …
```

| Frame | Param | Value |
|---|---|---|
| Map | `map_frame` | `map` |
| Odom | `odom_frame` | `odom` |
| Robot | `base_frame` | `base_footprint` |
| Scan topic | `scan_topic` | `/scan` |

> ⚠️ `base_footprint` must be the **root** of the robot TF chain (the diff-drive plugin
> publishes `odom → base_footprint`). If it's inverted, it gets two parents and SLAM
> Toolbox silently drops every scan.

---

## 🎛️ Key parameters (online mapping)

Tuned for a **5 m** indoor LiDAR and tight greenhouse furrows — see
`config/slam_toolbox_online_async.yaml`:

| Parameter | Value | Why |
|---|---|---|
| `solver_plugin` | `CeresSolver` (Schur-Jacobi / LM) | Fast, robust 2D pose-graph backend |
| `resolution` | `0.05` m/cell | 5 cm grid — resolves bed walls & furrows |
| `max_laser_range` | `5.0` m | Matches the sim/real LiDAR's usable range |
| `minimum_travel_distance` | `0.5` m | Add a node every ½ m of travel |
| `minimum_travel_heading` | `0.5` rad | …or every ~29° of turn |
| `do_loop_closing` | `true` | Closes the loop on the cross-aisle |
| `loop_search_maximum_distance` | `3.0` m | Search radius for loop candidates |

---

## 🤖 On the real robot

Identical commands, just flip the clock and start `pomona_bringup` (Robosense driver →
`/scan`) instead of Gazebo:

```bash
ros2 launch pomona_slam slam.launch.py use_sim_time:=false use_rviz:=true
```

---

## 🧯 Troubleshooting

| Symptom | Likely cause → fix |
|---|---|
| **Map never appears / "message filter dropping"** | No TF or `use_sim_time` mismatch. In sim, *every* node needs `use_sim_time:=true`. |
| **Map smears / rows bend** | Odometry drift with no loop closure → drive back over visited area; check `/odom`. |
| **Rotated / garbage map** | `base_footprint` not the TF root (see TF note above). |
| **`map_saver_cli` hangs** | No `/map` yet — let SLAM run a few `map_update_interval` (5 s) cycles first. |
| **Robot's own body shows as an obstacle** | Sim lidar self-returns — handled upstream by `pomona_gazebo`'s `laser_self_filter`. |

---

## 🗂️ Layout

```
pomona_slam/
├── launch/
│   ├── slam.launch.py            # online mapping  (+ optional RViz)
│   ├── localization.launch.py    # localize on a saved map
│   └── save_map.launch.py        # → maps/<name>.{pgm,yaml}
├── config/
│   ├── slam_toolbox_online_async.yaml
│   ├── slam_toolbox_localization.yaml
│   └── slam_toolbox_offline.yaml
├── maps/                         # saved maps live here (committable)
└── rviz/slam.rviz                # preconfigured mapping view
```

---

<div align="center">
<sub>

Part of **[Pomona Nexus](../../README.md)** · ROS 2 Humble greenhouse-picking robot ·
Author **Pravin Oli** · Licensed **Apache-2.0**

</sub>
</div>
