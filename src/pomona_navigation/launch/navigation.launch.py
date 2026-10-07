#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Nav2 navigation stack — INCLUDE-ONLY (started by bringup.launch.py).
#
# Brings up the full Nav2 pipeline against a single composed params file:
#   controller · planner · smoother · behaviors · bt_navigator ·
#   waypoint_follower · velocity_smoother · collision_monitor · lifecycle_manager
#
# cmd_vel chain:
#   controller_server → cmd_vel_nav → velocity_smoother → cmd_vel_smoothed
#                     → collision_monitor → cmd_vel  (Gazebo diff_drive / robot)

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")

    common = dict(output="screen", respawn=True, respawn_delay=2.0,
                  parameters=[params_file, {"use_sim_time": use_sim_time}])

    controller_server = Node(
        package="nav2_controller", executable="controller_server",
        name="controller_server",
        remappings=[("cmd_vel", "cmd_vel_nav")], **common,
    )
    planner_server = Node(
        package="nav2_planner", executable="planner_server",
        name="planner_server", **common,
    )
    smoother_server = Node(
        package="nav2_smoother", executable="smoother_server",
        name="smoother_server", **common,
    )
    behavior_server = Node(
        package="nav2_behaviors", executable="behavior_server",
        name="behavior_server", **common,
    )
    bt_navigator = Node(
        package="nav2_bt_navigator", executable="bt_navigator",
        name="bt_navigator", **common,
    )
    waypoint_follower = Node(
        package="nav2_waypoint_follower", executable="waypoint_follower",
        name="waypoint_follower", **common,
    )
    velocity_smoother = Node(
        package="nav2_velocity_smoother", executable="velocity_smoother",
        name="velocity_smoother",
        remappings=[("cmd_vel", "cmd_vel_nav"),
                    ("cmd_vel_smoothed", "cmd_vel_smoothed")], **common,
    )
    collision_monitor = Node(
        package="nav2_collision_monitor", executable="collision_monitor",
        name="collision_monitor", **common,
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager", executable="lifecycle_manager",
        name="lifecycle_manager_navigation", output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
            "autostart": True,
            "node_names": [
                "controller_server", "smoother_server", "planner_server",
                "behavior_server", "bt_navigator", "waypoint_follower",
                "velocity_smoother", "collision_monitor",
            ],
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument("params_file", description="Composed Nav2 params YAML"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        controller_server, planner_server, smoother_server, behavior_server,
        bt_navigator, waypoint_follower, velocity_smoother, collision_monitor,
        lifecycle_manager,
    ])
