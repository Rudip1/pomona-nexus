#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# SLAM Toolbox in pure-localization mode against a saved map.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("pomona_slam")

    declare_use_sim_time = DeclareLaunchArgument("use_sim_time", default_value="false")
    declare_params = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(pkg_share, "config", "slam_toolbox_localization.yaml"),
    )
    declare_map = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(pkg_share, "maps", "placeholder"),
        description="Map file basename (no extension) under maps/",
    )

    slam_node = Node(
        package="slam_toolbox",
        executable="localization_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[
            LaunchConfiguration("params_file"),
            {
                "use_sim_time": LaunchConfiguration("use_sim_time"),
                "map_file_name": LaunchConfiguration("map"),
            },
        ],
    )

    return LaunchDescription(
        [declare_use_sim_time, declare_params, declare_map, slam_node]
    )
