# pomona_gazebo

Gazebo Classic 11 simulation package for Pomona. **Sim only** — real-robot
launches live in `pomona_bringup`. URDF and meshes come from
`pomona_description`.

## Worlds

Naming: one **crop key** (`strawberry maize tomato apple grape mushroom`) used
identically across `models/<crop>/`, `launch/<crop>/`, and
`cad_assets_studio/<crop>/`. The **scene** appears only in the world filename,
`worlds/<crop>_<scene>.world`.

| World | Status | Launch (under `launch/<crop>/`) |
|---|---|---|
| `empty_world.world` | ★ working | `empty_world_pomona_{original,uvc}_{xacro,sdf}.launch.py` |
| `strawberry_farm.world` | in progress | `strawberry/strawberry_{xacro,sdf}.launch.py` → `strawberry_farm.launch.py` |
| `apple_orchard.world` | placeholder | `apple/apple_{xacro,sdf}.launch.py` |
| `grape_vineyard.world` | placeholder | `grape/grape_{xacro,sdf}.launch.py` |
| `mushroom_greenhouse.world` | placeholder | `mushroom/mushroom_{xacro,sdf}.launch.py` |
| `maize_field.world` | empty | — |
| `tomato_greenhouse.world` | empty | — |

Crop plant/prop models live in `models/<crop>/<crop>_<variant>/` (built from
`cad_assets_studio/<crop>/` with the asset tools there); shared props
in `models/environment/`. Because crop models sit two levels under `models/`, the
crop launch must add `models/<crop>` to `GAZEBO_MODEL_PATH`.

## Pipelines

Two parallel ways to spawn Pomona — pick one per session:

There are two robot models — `pomona_original` (stock wheels, full xArm6 +
AG95 + D435 camera + ros2_control) and `pomona_uvc` (stock wheels + UV-C
boom + 2 D455 cams, no arm/gripper/ros2_control). Each has both an xacro and an sdf
launch: `empty_world_pomona_<model>_{xacro,sdf}.launch.py`.

### Xacro pipeline (recommended)
- `robot_state_publisher` processes `pomona_<model>/xacro/pomona.xacro` (use_sim:=true).
- `/robot_description` carries the full URDF *with* Gazebo plugins.
- `spawn_entity.py -topic robot_description` spawns into Gazebo.
- Edit xacro → relaunch → changes picked up immediately.

### SDF pipeline
- `spawn_entity.py -file models/pomona_<model>/model.sdf` spawns a pre-baked SDF.
- The SDFs are **generated**, not placeholders. Regenerate after editing xacro:
  ```bash
  bash $(ros2 pkg prefix pomona_description)/share/pomona_description/scripts/xacro_to_urdf.sh
  # then per model (run from the pomona_description source dir):
  gz sdf -p urdf/pomona_original/urdf/pomona_original_sim.urdf > <pomona_gazebo>/models/pomona_original/model.sdf
  gz sdf -p urdf/pomona_uvc/urdf/pomona_uvc_sim.urdf           > <pomona_gazebo>/models/pomona_uvc/model.sdf
  ```

## Day-1 verification

```bash
cd ~/pomona_nexus
colcon build --symlink-install
source install/setup.bash

ros2 launch pomona_gazebo empty_world_pomona_uvc_xacro.launch.py
# → gzserver+gzclient open, Pomona spawns at origin, rqt_robot_steering pops up.
# Slide forward/turn — base should drive on the empty plane.
```

## Topics in sim

Base/lidar/IMU topics are present for **both** models. The **D435** camera and
`joint_states`-from-ros2_control rows are **pomona_original only**. **pomona_uvc**
has no arm/gripper/ros2_control, but its UV-C boom carries **two D455 cameras**
(`/uvc_cam_left/*`, `/uvc_cam_right/*`) looking down at the beds.

| Topic | Type | Publisher | Models |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | `rqt_robot_steering` → diff_drive plugin | both |
| `/odom` | `nav_msgs/Odometry` | diff_drive plugin | both |
| `/scan` | `sensor_msgs/LaserScan` | rslidar `gpu_ray` sensor (`libgazebo_ros_ray_sensor.so`), 5 m max | both |
| `/imu/data` | `sensor_msgs/Imu` | imu plugin | both |
| `/tf`, `/tf_static` | TF | robot_state_publisher + diff_drive plugin | both |
| `/camera/color/image_raw`, `/camera/depth/{image_rect_raw,points}` | `Image`/`PointCloud2` | D435 camera plugin | original |
| `/joint_states` | `sensor_msgs/JointState` | `joint_state_broadcaster` (ros2_control) | original |
| `/uvc_cam_left/{color,depth}/*`, `/uvc_cam_right/{color,depth}/*` | `Image`/`PointCloud2` | 2× D455 boom cameras (looking down) | **uvc** |

> The lidar uses `type="gpu_ray"` (not CPU `ray`): the CPU ray path segfaults
> gzserver when there's no rendering context. This first bit pomona_uvc (it had
> no camera then); it now has D455 cameras that init the render engine, but
> `gpu_ray` stays — it's the robust, faster choice. See `docs/sim_runbook.md`.

## Arm + gripper control (gazebo_ros2_control) — pomona_original only

`pomona_uvc` has no arm, so it loads no ros2_control and spawns no controllers.
For **pomona_original**, the xacro pipeline includes `ros2_control.xacro` (sim
only) and the `libgazebo_ros2_control.so` plugin, which runs a
`controller_manager` inside Gazebo. `empty_world_pomona_original_xacro.launch.py`
spawns three controllers and then sends a one-shot trajectory to raise the arm
to its home fold.

| Controller | Type | Interface |
|---|---|---|
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | publishes `/joint_states` |
| `xarm6_traj_controller` | `joint_trajectory_controller/JointTrajectoryController` | `/xarm6_traj_controller/follow_joint_trajectory` (action) |
| `ag95_gripper_controller` | `position_controllers/GripperActionController` | `/ag95_gripper_controller/gripper_cmd` (action); AG95 fingers follow `finger_joint` via URDF `<mimic>` |

Controller params: `config/gazebo_ros2_control_sim.yaml`. Quick checks and the
full failure catalogue (diff-drive `num_wheel_pairs`, the rcl comment-parse
issue, arm droop) are in **`docs/sim_runbook.md`**.

> Note: `pomona_state_publisher_{original,uvc}.launch.py` strip XML comments
> from the URDF before publishing — required so `gazebo_ros2_control` can parse
> it. Do not revert to a plain `Command([xacro …])` value.
