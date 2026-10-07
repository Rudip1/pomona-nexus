# pomona_moveit_config

MoveIt 2 configuration for **Pomona's xArm6 + AG95 gripper**.

## Status

Skeleton only. The config files are valid placeholders, the launch files
are stubs. To bring this online, the cleanest path is to **run MoveIt
Setup Assistant** against the URDF and regenerate.

## Recommended setup

```bash
# Load Pomona into Setup Assistant
ros2 launch moveit_setup_assistant setup_assistant.launch.py
# → "Edit Existing MoveIt Config Package"
# → point at ~/pomona_nexus/src/pomona_moveit_config
# → load URDF: pomona_description/urdf/pomona_original/xacro/pomona.xacro  (use_sim:=false)
# → generate Self-Collisions, Planning Groups (arm / gripper), Group States,
#   End Effectors, Controllers, ROS 2 Controllers
# → "Generate Package" overwrites config/ and launch/ with proper content
```

## Manual contents (until Setup Assistant runs)

- `config/pomona.srdf` — groups `arm`, `gripper`, `arm_with_gripper` + home/open/closed states
- `config/kinematics.yaml` — KDL for both arm groups
- `config/joint_limits.yaml` — velocity / acceleration limits
- `config/ompl_planning.yaml` — RRTConnect default
- `config/moveit_controllers.yaml` — bindings to JointTrajectoryController + GripperCommand
- `config/pilz_cartesian_limits.yaml` — Pilz industrial planner limits

## Launch (once filled in)

```bash
ros2 launch pomona_moveit_config demo.launch.py                     # mock controllers
ros2 launch pomona_moveit_config move_group.launch.py use_sim_time:=true   # against pomona_gazebo
ros2 launch pomona_moveit_config move_group.launch.py use_sim_time:=false  # against pomona_bringup
```
