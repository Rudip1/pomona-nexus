#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# RViz2 with the Pomona navigation config (costmaps, path, 2D Pose Estimate,
# Nav2 Goal). Standalone, or included by bringup.launch.py when rviz:=true.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("pomona_navigation")
    default_rviz = os.path.join(pkg_share, "rviz", "navigation.rviz")

    rviz2 = Node(
        package="rviz2", executable="rviz2", name="rviz2", output="screen",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    return LaunchDescription([
        DeclareLaunchArgument("rviz_config", default_value=default_rviz,
                              description="Full path to the .rviz config"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        rviz2,
    ])
