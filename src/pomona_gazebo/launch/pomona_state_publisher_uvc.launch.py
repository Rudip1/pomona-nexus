#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Robot state publisher for the Gazebo pipeline — UV-C sim model
# (urdf/pomona_uvc/xacro/pomona.xacro, oversized wheels + cantilever UV-C boom).
# Processes the xacro with use_sim:=true and publishes /robot_description.
#
# NOTE: XML comments are stripped from the generated URDF before publishing.
# gazebo_ros2_control (Humble) re-passes robot_description to the
# controller_manager as a `--param` CLI override; rcl rejects the non-ASCII
# box-drawing characters in our xacro comment headers. Stripping keeps the
# source style intact while making the runtime URDF safe.

import os
import re
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    xacro_path = os.path.join(
        get_package_share_directory("pomona_description"),
        "urdf", "pomona_uvc", "xacro", "pomona.xacro",
    )
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)

    urdf = subprocess.check_output(["xacro", xacro_path, "use_sim:=true"], text=True)
    urdf = re.sub(r"<!--.*?-->", "", urdf, flags=re.DOTALL)

    return [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": urdf,
                         "use_sim_time": use_sim_time == "true"}],
        ),
        # The low 360° 2D rslidar (gazebo_plugins.xacro) publishes /scan_raw,
        # which clips the rear display as a phantom obstacle. This node nulls the
        # beams whose endpoint falls inside the robot footprint (→ +inf, traced as
        # free/explored by slam_toolbox) and republishes /scan. Keeps full 360°.
        Node(
            package="pomona_gazebo",
            executable="laser_self_filter.py",
            name="laser_self_filter",
            output="screen",
            parameters=[{"use_sim_time": use_sim_time == "true"}],
        ),
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time", default_value="true", description="Use Gazebo clock"
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )
