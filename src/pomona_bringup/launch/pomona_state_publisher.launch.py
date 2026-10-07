#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Real-robot RSP. Same pomona.xacro as sim, but use_sim:=false so the
# Gazebo plugin block is NOT included.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    xacro_path = PathJoinSubstitution(
        [FindPackageShare("pomona_description"), "urdf", "pomona_original", "xacro", "pomona.xacro"]
    )

    use_sim_time = LaunchConfiguration("use_sim_time", default="false")

    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_path, " use_sim:=false"]),
        value_type=str,
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": use_sim_time,
                        "publish_frequency": 50.0,
                    }
                ],
            ),
        ]
    )
