#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
#
# Pomona Nav2 bringup — single entry point. Three orthogonal axes compose into
# a full stack:   controller:= {mppi|dwb}   planner:= NavFn   localization:= {amcl|slam|none}
#
#   nav2_base.yaml ⊕ controllers/<ctrl>.yaml ⊕ planners/<planner>.yaml
#     ⊕ localization/amcl.yaml (amcl only) ⊕ robots/pomona_uvc.yaml rewrites
#     → /tmp/nav2_<ctrl>_<planner>_<loc>.yaml  → passed to every Nav2 node
#   (merged by pomona_navigation/launch_utils/compose_params.py)
#
# Examples
#   # Map first (SLAM), drive with Nav2 goals
#   ros2 launch pomona_navigation bringup.launch.py localization:=slam controller:=mppi
#   # Localize on a saved map (default strawberry_farm), navigate
#   ros2 launch pomona_navigation bringup.launch.py localization:=amcl controller:=dwb

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            OpaqueFunction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from pomona_navigation.launch_utils.compose_params import compose, load_robot_profile


def _launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory("pomona_navigation")
    cfg = os.path.join(pkg, "config")
    nav2 = os.path.join(cfg, "nav2")
    bt_dir = os.path.join(pkg, "behavior_trees")

    controller = LaunchConfiguration("controller").perform(context)
    planner = LaunchConfiguration("planner").perform(context)
    localization = LaunchConfiguration("localization").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)

    if controller not in ("mppi", "dwb"):
        raise RuntimeError(f"controller:={controller} — choose 'mppi' or 'dwb'")
    if planner != "NavFn":
        raise RuntimeError(f"planner:={planner} — only 'NavFn' is configured")
    if localization not in ("amcl", "slam", "none"):
        raise RuntimeError(f"localization:={localization} — 'amcl' | 'slam' | 'none'")

    # Robot rewrites (+ inject absolute BT XML paths over the base placeholders).
    rewrites = load_robot_profile(
        os.path.join(cfg, "robots", "pomona_uvc.yaml"),
        controller_family=controller,
    )
    rewrites["bt_navigator.ros__parameters.default_nav_to_pose_bt_xml"] = \
        os.path.join(bt_dir, "navigate_w_replanning_and_recovery.xml")
    rewrites["bt_navigator.ros__parameters.default_nav_through_poses_bt_xml"] = \
        os.path.join(bt_dir, "navigate_through_poses.xml")

    params_file = compose(
        base_path=os.path.join(nav2, "nav2_base.yaml"),
        controller_path=os.path.join(nav2, "controllers", f"{controller}.yaml"),
        planner_path=os.path.join(nav2, "planners", f"{planner}.yaml"),
        localization_path=(os.path.join(nav2, "localization", "amcl.yaml")
                           if localization == "amcl" else None),
        robot_rewrites=rewrites,
        label=f"pomona_{controller}_{planner}_{localization}",
    )
    print(f"[bringup] controller={controller} planner={planner} "
          f"localization={localization}")
    print(f"[bringup] composed params: {params_file}")

    nav_args = {"params_file": params_file, "use_sim_time": use_sim_time}

    actions = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg, "launch", "navigation.launch.py")),
            launch_arguments=nav_args.items()),
    ]

    if localization == "amcl":
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg, "launch", "localization.launch.py")),
            launch_arguments={
                **nav_args,
                "map": LaunchConfiguration("map").perform(context),
                "map_name": LaunchConfiguration("map_name").perform(context),
            }.items()))
    elif localization == "slam":
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg, "launch", "slam.launch.py")),
            launch_arguments={"use_sim_time": use_sim_time}.items()))

    return actions


def generate_launch_description():
    pkg = get_package_share_directory("pomona_navigation")
    return LaunchDescription([
        DeclareLaunchArgument("controller", default_value="mppi",
                              description="Local controller: mppi | dwb"),
        DeclareLaunchArgument("planner", default_value="NavFn",
                              description="Global planner: NavFn"),
        DeclareLaunchArgument("localization", default_value="amcl",
                              description="map→odom source: amcl | slam | none"),
        DeclareLaunchArgument("map", default_value="",
                              description="Full path to map .yaml (amcl)"),
        DeclareLaunchArgument("map_name", default_value="strawberry_farm",
                              description="Map basename under pomona_slam/maps/ (amcl)"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("rviz", default_value="true"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg, "launch", "rviz.launch.py")),
            launch_arguments={
                "use_sim_time": LaunchConfiguration("use_sim_time")}.items(),
            condition=IfCondition(LaunchConfiguration("rviz"))),
        OpaqueFunction(function=_launch_setup),
    ])
