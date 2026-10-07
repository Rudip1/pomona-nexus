#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Shared SDF-spawn helper (SDF pipeline). Takes an `sdf_file` arg; the
# per-model launches (empty_world_pomona_{original,uvc}_sdf.launch.py) pass
# their own models/pomona_<model>/model.sdf. Default below is pomona_original.
#
# Regenerate the SDFs by running:
#   bash $(ros2 pkg prefix pomona_description)/share/pomona_description/scripts/xacro_to_urdf.sh
# then converting each *_sim.urdf to SDF (e.g. with `gz sdf -p`).

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("pomona_gazebo")
    sdf_file  = os.path.join(pkg_share, "models", "pomona_original", "model.sdf")

    x_pose = LaunchConfiguration("x_pose", default="0.0")
    y_pose = LaunchConfiguration("y_pose", default="0.0")
    z_pose = LaunchConfiguration("z_pose", default="0.1")
    theta  = LaunchConfiguration("theta",  default="0.0")

    return LaunchDescription(
        [
            DeclareLaunchArgument("x_pose", default_value="0.0"),
            DeclareLaunchArgument("y_pose", default_value="0.0"),
            DeclareLaunchArgument("z_pose", default_value="0.1"),
            DeclareLaunchArgument("theta",  default_value="0.0"),
            DeclareLaunchArgument(
                "sdf_file",
                default_value=sdf_file,
                description="Path to SDF model file",
            ),
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                output="screen",
                arguments=[
                    "-entity", "pomona",
                    "-file",   LaunchConfiguration("sdf_file"),
                    "-x", x_pose,
                    "-y", y_pose,
                    "-z", z_pose,
                    "-Y", theta,
                ],
            ),
        ]
    )
