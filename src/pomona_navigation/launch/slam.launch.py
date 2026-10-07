#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Online SLAM for navigation — thin wrapper that includes pomona_slam's
# slam.launch.py (SLAM Toolbox online async), the single source of truth for
# mapping. Used by bringup.launch.py (localization:=slam) to build a map while
# driving; save it afterwards with pomona_slam/save_map.launch.py.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_slam = get_package_share_directory("pomona_slam")

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_slam, "launch", "slam.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "use_rviz": "false",        # bringup owns RViz
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        slam,
    ])
