#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Convention-named entry point for the strawberry world (xacro pipeline).
# The real launch is strawberry_farm.launch.py (10-row farm + pomona_uvc spawn
# + teleop); this just delegates to it so `..._xacro.launch.py` matches the
# per-world×model naming used elsewhere.
#
# Run:  ros2 launch pomona_gazebo strawberry_xacro.launch.py
#   (equivalent to: ros2 launch pomona_gazebo strawberry_farm.launch.py)

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg = get_package_share_directory("pomona_gazebo")
    farm = os.path.join(pkg, "launch", "strawberry", "strawberry_farm.launch.py")
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(farm)),
    ])
