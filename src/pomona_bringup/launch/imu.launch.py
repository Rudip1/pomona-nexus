#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Xsens MTi IMU over USB (/dev/xsens_imu, 115200 baud).
# Requires udev rule (install_udev.sh).
#
# TODO  download Xsens MT Software Suite ROS2 driver from movella.com
# and include xsens_mti_driver/launch/xsens_mti_node.launch.py.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("port",     default_value="/dev/xsens_imu"),
            DeclareLaunchArgument("baudrate", default_value="115200"),
            DeclareLaunchArgument("frame_id", default_value="imu_link"),
        ]
    )
