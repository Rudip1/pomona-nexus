#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Real-robot top-level launch — Pomona full hardware stack           ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Prerequisites on the robot:
#   1. bash scripts/setup_can.sh  (brings up can0 @ 500k)
#   2. bash scripts/install_udev.sh  (one-time, installs udev rules)
#   3. ros-humble drivers installed (scout_ros2, xarm_ros2, realsense2_camera,
#      rslidar_sdk, xsens_mti_driver, pointcloud_to_laserscan).
#
# Run:  ros2 launch pomona_bringup pomona_bringup.launch.py
#       ros2 launch pomona_bringup pomona_bringup.launch.py use_rviz:=true

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("pomona_bringup")
    launch_dir = os.path.join(pkg_share, "launch")

    declare_use_rviz = DeclareLaunchArgument("use_rviz", default_value="false")
    declare_enable_base    = DeclareLaunchArgument("enable_base",    default_value="true")
    declare_enable_arm     = DeclareLaunchArgument("enable_arm",     default_value="true")
    declare_enable_gripper = DeclareLaunchArgument("enable_gripper", default_value="true")
    declare_enable_lidar   = DeclareLaunchArgument("enable_lidar",   default_value="true")
    declare_enable_camera  = DeclareLaunchArgument("enable_camera",  default_value="true")
    declare_enable_imu     = DeclareLaunchArgument("enable_imu",     default_value="true")

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, "pomona_state_publisher.launch.py")
        )
    )

    base = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "base.launch.py")),
        condition=IfCondition(LaunchConfiguration("enable_base")),
    )
    arm = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "arm.launch.py")),
        condition=IfCondition(LaunchConfiguration("enable_arm")),
    )
    gripper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "gripper.launch.py")),
        condition=IfCondition(LaunchConfiguration("enable_gripper")),
    )
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "lidar.launch.py")),
        condition=IfCondition(LaunchConfiguration("enable_lidar")),
    )
    camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "camera.launch.py")),
        condition=IfCondition(LaunchConfiguration("enable_camera")),
    )
    imu = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "imu.launch.py")),
        condition=IfCondition(LaunchConfiguration("enable_imu")),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(pkg_share, "rviz", "real.rviz")],
        condition=IfCondition(LaunchConfiguration("use_rviz")),
    )

    return LaunchDescription(
        [
            declare_use_rviz,
            declare_enable_base,
            declare_enable_arm,
            declare_enable_gripper,
            declare_enable_lidar,
            declare_enable_camera,
            declare_enable_imu,
            rsp,
            base,
            arm,
            gripper,
            lidar,
            camera,
            imu,
            rviz,
        ]
    )
