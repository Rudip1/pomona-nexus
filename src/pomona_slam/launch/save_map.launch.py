#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Save the current SLAM Toolbox map to disk, into pomona_slam/maps/ by default
# (so the map lives with the package and is version-controllable), instead of
# whatever directory you happened to launch from.
#
# Equivalent to:
#   ros2 run nav2_map_server map_saver_cli -f <maps_dir>/<name>
#
#   ros2 launch pomona_slam save_map.launch.py map_name:=strawberry_farm
#   ros2 launch pomona_slam save_map.launch.py map_name:=strawberry_farm \
#        maps_dir:=/some/other/dir

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.substitutions import LaunchConfiguration


def _default_maps_dir():
    """pomona_slam/maps/ next to this package's source tree.

    With ``colcon build --symlink-install`` the installed launch file is a
    symlink back to source, so realpath() lands in src/pomona_slam/launch/ and
    the maps/ sibling is the version-controlled one. Falls back to the share
    copy otherwise.
    """
    launch_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.normpath(os.path.join(launch_dir, "..", "maps"))


def _save_map(context, *args, **kwargs):
    maps_dir = LaunchConfiguration("maps_dir").perform(context)
    map_name = LaunchConfiguration("map_name").perform(context)
    os.makedirs(maps_dir, exist_ok=True)
    out = os.path.join(maps_dir, map_name)
    saver = ExecuteProcess(
        cmd=["ros2", "run", "nav2_map_server", "map_saver_cli", "-f", out],
        output="screen",
    )
    return [saver]


def generate_launch_description():
    declare_name = DeclareLaunchArgument(
        "map_name", default_value="pomona_map",
        description="Output map basename (creates <name>.pgm + <name>.yaml)",
    )
    declare_maps_dir = DeclareLaunchArgument(
        "maps_dir", default_value=_default_maps_dir(),
        description="Directory to write the map into (default: pomona_slam/maps/)",
    )

    return LaunchDescription(
        [declare_name, declare_maps_dir, OpaqueFunction(function=_save_map)]
    )
