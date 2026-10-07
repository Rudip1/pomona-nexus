#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Pomona SLAM — online async mapping with SLAM Toolbox.
# Works against sim (use_sim_time:=true) or real (use_sim_time:=false).
#
# Run with sim:   ros2 launch pomona_slam slam.launch.py use_sim_time:=true
# Run on robot:   ros2 launch pomona_slam slam.launch.py use_sim_time:=false

#       ros2 launch pomona_gazebo strawberry_farm.launch.py            # farm + uvc + teleop
#       ros2 launch pomona_slam slam.launch.py use_sim_time:=true use_rviz:=true

# drive furrows + the cross-aisle for loop closure
#       ros2 launch pomona_slam save_map.launch.py map_name:=strawberry_farm

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("pomona_slam")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="True for Gazebo sim, false for real robot",
    )
    declare_params = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(
            pkg_share, "config", "slam_toolbox_online_async.yaml"
        ),
        description="SLAM Toolbox parameter file",
    )
    declare_use_rviz = DeclareLaunchArgument("use_rviz", default_value="false")

    slam_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[
            LaunchConfiguration("params_file"),
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(pkg_share, "rviz", "slam.rviz")],
        condition=IfCondition(LaunchConfiguration("use_rviz")),
    )

    return LaunchDescription(
        [declare_use_sim_time, declare_params, declare_use_rviz, slam_node, rviz_node]
    )
