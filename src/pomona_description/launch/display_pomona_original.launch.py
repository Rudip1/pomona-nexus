#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Standalone URDF viewer for the ORIGINAL model (stock Scout V2 wheels, no UV-C).
# Loads urdf/pomona_original/xacro/pomona.xacro (use_sim:=false) through
# robot_state_publisher, joint_state_publisher_gui sliders, and RViz2.
#
# Run:  ros2 launch pomona_description display_pomona_original.launch.py
#       ros2 launch pomona_description display_pomona_original.launch.py use_gui:=false

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = get_package_share_directory("pomona_description")

    declare_use_gui = DeclareLaunchArgument(
        "use_gui", default_value="true",
        description="Launch joint_state_publisher_gui (sliders) instead of headless",
    )
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz", default_value="true", description="Launch RViz2",
    )
    declare_rviz_config = DeclareLaunchArgument(
        "rviz_config",
        default_value=os.path.join(pkg_share, "rviz", "model.rviz"),
        description="Path to RViz config file",
    )

    xacro_path = PathJoinSubstitution(
        [FindPackageShare("pomona_description"),
         "urdf", "pomona_original", "xacro", "pomona.xacro"]
    )

    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_path, " use_sim:=false"]),
        value_type=str,
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description, "use_sim_time": False}],
    )

    jsp_gui_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_gui")),
    )

    jsp_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        condition=UnlessCondition(LaunchConfiguration("use_gui")),
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        condition=IfCondition(LaunchConfiguration("use_rviz")),
    )

    return LaunchDescription(
        [
            declare_use_gui,
            declare_use_rviz,
            declare_rviz_config,
            robot_state_publisher_node,
            jsp_gui_node,
            jsp_node,
            rviz_node,
        ]
    )
