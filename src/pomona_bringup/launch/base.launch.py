#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# AgileX Scout V2 mobile base over CAN.
# Run scripts/setup_can.sh first to ensure can0 is up @ 500 kbps.
#
# TODO  wire to AgileX scout_ros2 once installed:
#   sudo apt install ros-humble-scout-base ros-humble-scout-bringup  (when packaged)
#   or vcs import < src/scout_ros2.repos

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    declare_port_name      = DeclareLaunchArgument("port_name",      default_value="can0")
    declare_odom_topic     = DeclareLaunchArgument("odom_topic",     default_value="odom")
    declare_is_scout_mini  = DeclareLaunchArgument("is_scout_mini",  default_value="false")
    declare_pub_tf         = DeclareLaunchArgument("pub_tf",         default_value="true")

    # TODO  swap to the actual scout_base_node from scout_ros2 when installed.
    placeholder = Node(
        package="ros2",
        executable="echo",
        name="scout_base_placeholder",
        output="screen",
        arguments=["[pomona_bringup] base.launch.py is a stub — install scout_ros2"],
        # condition: never run — placeholder only documents intent
    )

    return LaunchDescription(
        [
            declare_port_name,
            declare_odom_topic,
            declare_is_scout_mini,
            declare_pub_tf,
            # placeholder,   # leave commented: prevents launch errors before scout_ros2 is wired
        ]
    )
