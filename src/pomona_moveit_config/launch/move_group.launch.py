#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# move_group node launch — STUB.
# Real implementation needs MoveItConfigsBuilder; for now this is a marker.
#
# TODO  use moveit_configs_utils.MoveItConfigsBuilder to assemble parameters
# from config/ + pomona_description/urdf/pomona_original/xacro/pomona.xacro.
# See https://moveit.picknik.ai/main/doc/examples/moveit_configs_builder/

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false",
                                  description="True for sim, false for real robot"),
            # TODO MoveIt move_group Node + all parameter dicts
        ]
    )
