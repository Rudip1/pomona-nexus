#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# RViz with MotionPlanning plugin pointed at move_group — STUB.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            # TODO add rviz2 Node with config/moveit.rviz once Setup Assistant runs
        ]
    )
