#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# DH Robotics AG95 gripper over FTDI USB (/dev/DH_hand, 115200 8N1).
# Requires udev rule /etc/udev/rules.d/99-dh_hand.rules (install_udev.sh).
#
# TODO  port dh_gripper_driver from goldmines (ROS1) to ROS2,
# or use DH Robotics' upstream ROS2 driver when released.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("port",         default_value="/dev/DH_hand"),
            DeclareLaunchArgument("baudrate",     default_value="115200"),
            DeclareLaunchArgument("gripper_id",   default_value="1"),
            DeclareLaunchArgument("gripper_model", default_value="AG95_MB"),
        ]
    )
