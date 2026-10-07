#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# AMCL localization — map_server + amcl + lifecycle_manager.
#
# Loads a saved 2D map (default: the map saved by pomona_slam, under
# pomona_slam/maps/<map_name>.yaml) and localizes the robot against /scan,
# publishing the map→odom transform. Provide an initial pose in RViz
# ("2D Pose Estimate"). Started by bringup.launch.py (localization:=amcl), or
# standalone for debugging.
#
#   map      : full path to a map .yaml (wins over map_name)
#   map_name : basename under pomona_slam/maps/  (default: strawberry_farm)

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    map_arg = LaunchConfiguration("map").perform(context)
    map_name = LaunchConfiguration("map_name").perform(context)
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")

    if map_arg:
        map_yaml = os.path.expanduser(map_arg)
    else:
        maps_dir = os.path.join(get_package_share_directory("pomona_slam"), "maps")
        map_yaml = os.path.join(maps_dir, f"{map_name}.yaml")

    if not os.path.exists(map_yaml):
        raise RuntimeError(
            f"[localization] Map not found: {map_yaml}\n"
            "Build a map first:  ros2 launch pomona_slam slam.launch.py "
            "use_sim_time:=true  →  ros2 launch pomona_slam save_map.launch.py "
            f"map_name:={map_name}\n"
            "or pass map:=/abs/path/to/map.yaml"
        )
    print(f"[localization] Loading map: {map_yaml}")

    map_server = Node(
        package="nav2_map_server", executable="map_server", name="map_server",
        output="screen",
        parameters=[params_file,
                    {"use_sim_time": use_sim_time, "yaml_filename": map_yaml}],
    )
    amcl = Node(
        package="nav2_amcl", executable="amcl", name="amcl", output="screen",
        parameters=[params_file, {"use_sim_time": use_sim_time}],
    )
    lifecycle = Node(
        package="nav2_lifecycle_manager", executable="lifecycle_manager",
        name="lifecycle_manager_localization", output="screen",
        parameters=[{"use_sim_time": use_sim_time, "autostart": True,
                     "node_names": ["map_server", "amcl"]}],
    )
    return [map_server, amcl, lifecycle]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("map", default_value="",
                              description="Full path to map .yaml (wins over map_name)"),
        DeclareLaunchArgument("map_name", default_value="strawberry_farm",
                              description="Map basename under pomona_slam/maps/"),
        DeclareLaunchArgument("params_file", description="Composed Nav2 params YAML"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        OpaqueFunction(function=_launch_setup),
    ])
