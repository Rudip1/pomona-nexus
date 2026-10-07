#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# UFactory xArm6 over Ethernet (default IP 192.168.1.219).
#
# TODO  wire to xarm_ros2 once installed:
#   git clone https://github.com/xArm-Developer/xarm_ros2.git src/xarm_ros2
#   rosdep install --from-paths src --ignore-src -r -y
#   colcon build
# then include xarm_api/launch/xarm6_driver.launch.py here.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    declare_robot_ip   = DeclareLaunchArgument("robot_ip",   default_value="192.168.1.219")
    declare_report_type = DeclareLaunchArgument("report_type", default_value="normal")
    declare_use_moveit = DeclareLaunchArgument("use_moveit", default_value="false")

    return LaunchDescription(
        [
            declare_robot_ip,
            declare_report_type,
            declare_use_moveit,
            # TODO add IncludeLaunchDescription(xarm_api/launch/xarm6_driver.launch.py)
        ]
    )
