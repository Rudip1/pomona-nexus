#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Autonomous UV-C bed-disinfection mission — SLAM mode.
#
# Brings up the full Nav2 stack ON SLAM (online slam_toolbox builds the map while
# driving) and runs the bed_disinfection_mission node, which drives every bed-pair
# lane across all four quadrants of the pinwheel farm and returns to the origin.
# One pass per bed pair (the UV-C boom covers two beds at once) → 3 passes/quadrant
# → 12 lanes. The robot explores and GENERATES the map as it goes; save it after
# with pomona_slam/save_map.launch.py.
#
# Prereq (other terminal):
#   ros2 launch pomona_gazebo strawberry_farm.launch.py
#
#   ros2 launch pomona_navigation autonomous_waypoint.launch.py controller:=mppi

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            OpaqueFunction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory("pomona_navigation")
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)

    # Full stack on SLAM: slam_toolbox provides map→odom and grows /map live.
    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg, "launch", "bringup.launch.py")),
        launch_arguments={
            "localization": "slam",
            "controller": LaunchConfiguration("controller").perform(context),
            "planner": "NavFn",
            "use_sim_time": use_sim_time,
            "rviz": LaunchConfiguration("rviz").perform(context),
        }.items(),
    )

    # Mission node — SLAM starts the robot at map origin = spawn, so no AMCL
    # initial-pose seeding is needed (set_initial_pose defaults off).
    mission = Node(
        package="pomona_navigation",
        executable="bed_disinfection_mission.py",
        name="bed_disinfection_mission",
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time == "true",
            "set_initial_pose": LaunchConfiguration("set_initial_pose").perform(context) == "true",
            "start_delay": float(LaunchConfiguration("start_delay").perform(context)),
        }],
    )

    return [bringup, mission]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("controller", default_value="mppi",
                              description="Local controller: mppi | dwb"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("rviz", default_value="true"),
        DeclareLaunchArgument("set_initial_pose", default_value="false",
                              description="Seed an initial pose (SLAM starts at origin, so off)"),
        DeclareLaunchArgument("start_delay", default_value="10.0",
                              description="Seconds to wait for SLAM + Nav2 before sending waypoints"),
        OpaqueFunction(function=_launch_setup),
    ])
