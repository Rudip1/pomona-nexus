#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Spawn Pomona in Gazebo by reading /robot_description published by the
# pomona_state_publisher launch (xacro pipeline).

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    x_pose = LaunchConfiguration("x_pose", default="0.0")
    y_pose = LaunchConfiguration("y_pose", default="0.0")
    z_pose = LaunchConfiguration("z_pose", default="0.1")
    theta  = LaunchConfiguration("theta",  default="0.0")

    return LaunchDescription(
        [
            DeclareLaunchArgument("x_pose", default_value="0.0"),
            DeclareLaunchArgument("y_pose", default_value="0.0"),
            DeclareLaunchArgument(
                "z_pose",
                default_value="0.1",
                description="Spawn height — bump up on rough mesh floors",
            ),
            DeclareLaunchArgument("theta", default_value="0.0"),
            Node(
                package="gazebo_ros",
                executable="spawn_entity.py",
                output="screen",
                arguments=[
                    "-entity", "pomona",
                    "-topic", "robot_description",
                    "-x", x_pose,
                    "-y", y_pose,
                    "-z", z_pose,
                    "-Y", theta,
                ],
            ),
        ]
    )
