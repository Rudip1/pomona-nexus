#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Robosense LiDAR (rslidar) + pointcloud_to_laserscan for Nav2.
# TODO  add Robosense rslidar_sdk Node + pointcloud_to_laserscan Node here.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("pomona_bringup")
    declare_pc2scan_params = DeclareLaunchArgument(
        "pc2scan_params",
        default_value=os.path.join(pkg_share, "config", "pointcloud_to_laserscan.yaml"),
        description="pointcloud_to_laserscan params",
    )

    pc2scan = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan",
        output="screen",
        remappings=[("cloud_in", "/rslidar_points"), ("scan", "/scan")],
        parameters=[LaunchConfiguration("pc2scan_params")],
    )

    return LaunchDescription(
        [
            declare_pc2scan_params,
            # TODO  rslidar_sdk Node here once installed
            pc2scan,
        ]
    )
