#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Empty world, xacro pipeline — UV-C sim model
# (oversized wheels + cantilever UV-C boom).
#
# Launch graph:
#   gzserver / gzclient        → Gazebo physics + GUI
#   robot_state_publisher      → pomona_state_publisher_uvc (use_sim:=true)
#   spawn_entity               → reads /robot_description (delayed 5 s)
#   rqt_robot_steering         → /cmd_vel teleop
# (No arm in pomona_uvc → no ros2_control, no controller spawners, no go-home
#  trajectory. The UV-C boom is fixed geometry; only the base is actuated.)
#
# Run:  ros2 launch pomona_gazebo empty_world_pomona_uvc_xacro.launch.py

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
        "use_teleop", default_value="true",
        description="Start rqt_robot_steering for /cmd_vel",
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose       = LaunchConfiguration("x_pose")
    y_pose       = LaunchConfiguration("y_pose")
    theta        = LaunchConfiguration("theta")

    world_file = os.path.join(pkg_pomona_gazebo, "worlds", "empty_world.world")

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
                    os.path.join(launch_dir, "spawn_xacro.launch.py")
                ),
                launch_arguments={"x_pose": x_pose, "y_pose": y_pose,
                                  "theta": theta,
                                  # spawn above ground so the robot drops onto
                                  # its wheels (URDF spawn doesn't resolve an
                                  # initial ground penetration cleanly).
                                  "z_pose": "0.30"}.items(),
            )
        ],
    )

    # No ros2_control in pomona_uvc (arm removed) → no controller spawners and
    # no go-home trajectory. The base drives via the diff-drive plugin; wheel
    # joint states come from the gazebo joint_state_publisher plugin.

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
