#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Empty world, SDF pipeline — UV-C sim model (oversized wheels + UV-C boom).
# Spawns from models/pomona_uvc/model.sdf (pre-baked). RSP still runs
# (pomona_state_publisher_uvc) so the TF tree is published.
#
# Run:  ros2 launch pomona_gazebo empty_world_pomona_uvc_sdf.launch.py
#
# NOTE: models/pomona_uvc/model.sdf is generated from
# urdf/pomona_uvc/xacro/pomona.xacro (xacro_to_urdf.sh + `gz sdf -p`).
# Regenerate it after editing the xacro so this pipeline stays in sync.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_pomona_gazebo = get_package_share_directory("pomona_gazebo")
    pkg_gazebo_ros    = get_package_share_directory("gazebo_ros")
    pkg_pomona_desc   = get_package_share_directory("pomona_description")
    launch_dir        = os.path.join(pkg_pomona_gazebo, "launch")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time", default_value="true", description="Use Gazebo clock"
    )
    declare_x_pose = DeclareLaunchArgument("x_pose", default_value="0.0")
    declare_y_pose = DeclareLaunchArgument("y_pose", default_value="0.0")
    declare_theta  = DeclareLaunchArgument("theta",  default_value="0.0")
    declare_use_teleop = DeclareLaunchArgument(
        "use_teleop", default_value="true", description="Start rqt_robot_steering",
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose       = LaunchConfiguration("x_pose")
    y_pose       = LaunchConfiguration("y_pose")
    theta        = LaunchConfiguration("theta")

    world_file = os.path.join(pkg_pomona_gazebo, "worlds", "empty_world.world")
    sdf_file   = os.path.join(pkg_pomona_gazebo, "models", "pomona_uvc", "model.sdf")

    gazebo_resource_path = SetEnvironmentVariable(
        name="GAZEBO_RESOURCE_PATH",
        value=os.pathsep.join(
            [os.path.dirname(pkg_pomona_desc), "/usr/share/gazebo-11",
             "/opt/ros/humble/share"]
        ),
    )
    gazebo_model_path = SetEnvironmentVariable(
        name="GAZEBO_MODEL_PATH",
        value=os.pathsep.join(
            [os.path.join(pkg_pomona_gazebo, "models"),
             os.path.dirname(pkg_pomona_desc), "/usr/share/gazebo-11/models"]
        ),
    )
    gazebo_plugin_path = SetEnvironmentVariable(
        name="GAZEBO_PLUGIN_PATH",
        value=os.pathsep.join(
            ["/opt/ros/humble/lib", "/usr/lib/x86_64-linux-gnu/gazebo-11/plugins"]
        ),
    )

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gzserver.launch.py")
        ),
        launch_arguments={"world": world_file}.items(),
    )
    gzclient = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_gazebo_ros, "launch", "gzclient.launch.py")
                )
            )
        ],
    )

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, "pomona_state_publisher_uvc.launch.py")
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    spawn = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(launch_dir, "spawn_sdf.launch.py")
                ),
                launch_arguments={"x_pose": x_pose, "y_pose": y_pose,
                                  "theta": theta, "sdf_file": sdf_file,
                                  "z_pose": "0.30"}.items(),
            )
        ],
    )

    teleop = Node(
        package="rqt_robot_steering",
        executable="rqt_robot_steering",
        name="rqt_robot_steering",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(LaunchConfiguration("use_teleop")),
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_x_pose,
            declare_y_pose,
            declare_theta,
            declare_use_teleop,
            gazebo_resource_path,
            gazebo_model_path,
            gazebo_plugin_path,
            gzserver,
            gzclient,
            rsp,
            spawn,
            teleop,
        ]
    )
