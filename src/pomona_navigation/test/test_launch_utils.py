# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.
"""Smoke tests for the pure-Python launch utilities (no ROS runtime needed)."""

import os

import pytest
import yaml

from pomona_navigation.launch_utils import bed_waypoints
from pomona_navigation.launch_utils.compose_params import (
    ComposeError,
    compose,
    load_robot_profile,
)

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(PKG, "config")
NAV2 = os.path.join(CFG, "nav2")
PROFILE = os.path.join(CFG, "robots", "pomona_uvc.yaml")


def test_lane_centres():
    assert bed_waypoints.LANES == [2.5, 6.5, 10.5]


def test_mission_length():
    # 4 quadrants x 3 lanes x (entry, exit) + return home
    wps = bed_waypoints.mission_waypoints()
    assert len(wps) == 25
    assert wps[-1] == bed_waypoints.HOME
    assert len(bed_waypoints.mission_waypoints(return_home=False)) == 24


@pytest.mark.parametrize("controller", ["mppi", "dwb"])
@pytest.mark.parametrize("amcl", [True, False])
def test_compose_strict(controller, amcl):
    rewrites = load_robot_profile(PROFILE, controller_family=controller)
    out = compose(
        base_path=os.path.join(NAV2, "nav2_base.yaml"),
        controller_path=os.path.join(NAV2, "controllers", f"{controller}.yaml"),
        planner_path=os.path.join(NAV2, "planners", "NavFn.yaml"),
        localization_path=os.path.join(NAV2, "localization", "amcl.yaml") if amcl else None,
        robot_rewrites=rewrites,
        label=f"test_{controller}",
    )
    try:
        with open(out) as f:
            merged = yaml.safe_load(f)
    finally:
        os.remove(out)
    vs = merged["velocity_smoother"]["ros__parameters"]
    assert vs["max_velocity"] == rewrites["velocity_smoother.ros__parameters.max_velocity"]
    assert ("amcl" in merged) == amcl


def test_compose_rejects_unknown_key():
    with pytest.raises(ComposeError):
        compose(
            base_path=os.path.join(NAV2, "nav2_base.yaml"),
            controller_path=os.path.join(NAV2, "controllers", "mppi.yaml"),
            planner_path=None,
            localization_path=None,
            robot_rewrites={"velocity_smoother.ros__parameters.max_velocty": [0.1]},
        )
