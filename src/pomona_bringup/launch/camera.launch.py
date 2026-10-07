#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Intel RealSense D435 on xArm6 end-effector.
#
# TODO  install ros-humble-realsense2-camera and include rs_launch.py:
#   sudo apt install ros-humble-realsense2-camera
# then IncludeLaunchDescription(realsense2_camera/launch/rs_launch.py)

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("camera_name", default_value="camera"),
            DeclareLaunchArgument("enable_color", default_value="true"),
            DeclareLaunchArgument("enable_depth", default_value="true"),
            DeclareLaunchArgument("align_depth.enable", default_value="true"),
        ]
    )
