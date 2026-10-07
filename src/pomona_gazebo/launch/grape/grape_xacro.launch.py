#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Placeholder — clones empty_world_pomona_uvc_xacro.launch.py with the world file
# swapped to worlds/grape/grape_vineyard.world. Replace this with a real launch when the
# grape vineyard environment is built.

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetLaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg = get_package_share_directory("pomona_gazebo")
    inner = os.path.join(pkg, "launch", "empty_world", "empty_world_pomona_uvc_xacro.launch.py")
    return LaunchDescription([
        # SetLaunchConfiguration only affects substitutions that read it.
        # The launch we're including hard-codes the world path, so for now
        # this placeholder will boot empty_world; replace with a copy of
        # the empty_world launch that points at worlds/grape/grape_vineyard.world once
        # the environment is ready.
        IncludeLaunchDescription(PythonLaunchDescriptionSource(inner)),
    ])
