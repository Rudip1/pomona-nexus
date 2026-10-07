<!--
  Copyright 2026 Pravin Oli

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Author:  Pravin Oli
  Project: Pomona Nexus
-->

# Simulation runbook — empty_world

How to bring up Pomona in Gazebo Classic 11, what should happen, how to verify
each subsystem, and how to fix the failures we have already hit.

This runbook covers **pomona_original** (the full robot: xArm6 + AG95 + D435 +
ros2_control), since arm/gripper verification is the interesting part.
**pomona_uvc** is the same base with the arm replaced by a fixed UV-C boom — no
arm, gripper, camera, or controllers — so skip sections 2's arm/gripper/camera
steps for it; everything else (base, lidar, IMU) is identical.

## 1. Launch

```bash
cd ~/pomona_nexus
colcon build --symlink-install
source install/setup.bash

ros2 launch pomona_gazebo empty_world_pomona_original_xacro.launch.py
```

Launch timeline (delays are intentional, to avoid startup races):

| t (s) | what starts |
|------|--------------|
| 0    | `gzserver` (physics) + `robot_state_publisher` (xacro → `/robot_description`) |
| 3    | `gzclient` (GUI) |
| 5    | `spawn_entity` reads `/robot_description`, inserts Pomona |
| 8    | controller spawners (`joint_state_broadcaster`, `xarm6_traj_controller`, `ag95_gripper_controller`) |
| 14   | one-shot **go-home** trajectory → arm rises to its ready fold |

Expected end state: Scout + white mounting box + xArm6 + AG95 spawned at the
origin, the arm holding the home pose (not drooping), and `rqt_robot_steering`
open. Dragging the slider drives the base.

Useful args: `use_teleop:=false` (no steering GUI), `x_pose/y_pose/theta`
(spawn pose), `use_sim_time` (default true).

## 2. Verify each subsystem

```bash
# Base steering — must show Subscription count: 1
ros2 topic info /cmd_vel
ros2 topic echo /odom --once

# Controllers — all three must be "active"
ros2 control list_controllers

# Arm holds home pose (j2≈-0.5, j3≈-0.6, j5≈1.1), stable over time
ros2 topic echo /joint_states --once

# Move the arm
ros2 action send_goal /xarm6_traj_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [joint1,joint2,joint3,joint4,joint5,joint6], \
   points: [{positions: [0,-0.6,0,0,0,0], time_from_start: {sec: 2}}]}}"

# Close the gripper (mimic fingers follow finger_joint)
ros2 action send_goal /ag95_gripper_controller/gripper_cmd \
  control_msgs/action/GripperCommand "{command: {position: 0.5, max_effort: 20.0}}"

# Sensors
ros2 topic hz /scan          # rslidar
ros2 topic hz /imu/data      # Xsens IMU
ros2 topic hz /camera/depth/points
```

## 3. Headless / parallel testing

When testing without disturbing a running instance, isolate the session:

```bash
export ROS_DOMAIN_ID=91
export GAZEBO_MASTER_URI=http://localhost:11347
unset DISPLAY                       # gzclient exits, gzserver runs headless
export GAZEBO_MODEL_DATABASE_URI="" # avoid the slow online model fetch
ros2 launch pomona_gazebo empty_world_pomona_original_xacro.launch.py use_teleop:=false
```

Different `GAZEBO_MASTER_URI` + `ROS_DOMAIN_ID` keep test runs from colliding
with each other or with a real session on the default domain.

## 4. Known failures and fixes

**Base will not move / `/cmd_vel` has 0 subscribers.**
`gazebo_ros_diff_drive` defaults to one wheel pair (two joints) but the Scout
has four wheel joints. Without `<num_wheel_pairs>2</num_wheel_pairs>` the plugin
logs *"Inconsistent number of joints specified. Plugin will not work."* and
never subscribes. Fixed in `gazebo_plugins.xacro`.

**Controllers never load; gzserver logs "Couldn't parse parameter override
rule: '--param robot_description:=<?xml ...'".**
`gazebo_ros2_control` re-passes the URDF to the controller_manager as a CLI
param, and rcl rejects the non-ASCII box-drawing characters in our xacro
comment headers. `pomona_state_publisher_{original,uvc}.launch.py` strip XML
comments from the description before publishing — keep that strip in place (see
the file's header note). This only affects the sim path; the real robot has no
`gazebo_ros2_control`.

**Arm holds a drooped pose instead of the intended home.**
Controllers activate ~8 s after spawn; gravity pulls the arm down in that gap
and the trajectory controller then holds whatever it finds. The launch sends a
one-shot go-home trajectory (~t=14 s) to actively raise it. Tune the home pose
in `ros2_control.xacro` (`initial` args) and the launch's `home_pose` command.

**gzserver segfaults (exit -11) right after spawn — especially on pomona_uvc.**
The crash backtrace is the rslidar sensor:
`RaySensor::UpdateImpl → MultiRayShape::Update → ODEMultiRayShape::UpdateRays →
dSpaceCollide2()` inside `libgazebo_ode`. The CPU `ray` sensor's ODE raycast
segfaults when gzserver has **no rendering context**. pomona_original dodged it
only because its D435 camera initializes the render engine; pomona_uvc has no
camera, so it crashed every launch. Fix: the `rslidar` sensor uses
`type="gpu_ray"` (not `type="ray"`) in `gazebo_plugins.xacro` for both models —
it renders the scan instead of ODE-raycasting, avoiding the bug (and it's
faster). Don't revert to `type="ray"`. (Diagnosed 2026-06-06.)

**LiDAR appears in the wrong place.**
`rslidar` is mounted on `box_link` (front of the mounting box), not on
`base_link`. If the box geometry changes, re-check `rslidar_joint` in
`sensors.xacro`.
