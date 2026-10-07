#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
# Licensed under the Apache License, Version 2.0.

"""Autonomous UV-C bed-disinfection mission for the strawberry farm.

Drives the robot down the centre of every bed-pair lane across all four
quadrants of the pinwheel farm and returns to the spawn origin — one pass per
bed pair (the UV-C boom covers two beds at once), three passes per quadrant.
Waypoints come from pomona_navigation.launch_utils.bed_waypoints, derived from
the same constants as the world generator.

Flow:
  1. (optional) seed AMCL with the spawn pose on /initialpose so it localizes
     without a manual RViz "2D Pose Estimate".
  2. wait for the Nav2 'follow_waypoints' action server.
  3. send the full lane sequence as a FollowWaypoints goal and report progress.

Run via autonomous_waypoint.launch.py (which also brings up Nav2 + AMCL).
"""

import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import FollowWaypoints

from pomona_navigation.launch_utils.bed_waypoints import mission_waypoints, HOME


def _yaw_to_quat(yaw):
    """Return the (x, y, z, w) quaternion for a rotation of ``yaw`` about Z."""
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


class BedDisinfectionMission(Node):
    """Send the bed-sweep route to Nav2 as one ``FollowWaypoints`` goal.

    After ``start_delay`` seconds the node optionally publishes the spawn pose
    on ``initialpose``, waits up to 30 s for the ``follow_waypoints`` action
    server, then sends the poses from
    :func:`pomona_navigation.launch_utils.bed_waypoints.mission_waypoints`.

    Parameters:
        frame_id (str, 'map'): frame of the waypoints and initial pose.
        set_initial_pose (bool, True): publish ``initial_pose`` before starting.
        initial_pose (list[float], [0, 0, 0]): ``[x, y, yaw]`` for AMCL seeding.
        start_delay (float, 5.0): seconds to wait before starting [s].
        return_home (bool, True): append the spawn pose as the last waypoint.
    """

    def __init__(self):
        super().__init__("bed_disinfection_mission")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("set_initial_pose", True)
        self.declare_parameter("initial_pose", list(HOME))   # [x, y, yaw]
        self.declare_parameter("start_delay", 5.0)           # s, let the stack settle
        self.declare_parameter("return_home", True)

        self.frame_id = self.get_parameter("frame_id").value
        self._client = ActionClient(self, FollowWaypoints, "follow_waypoints")
        self._init_pub = self.create_publisher(
            PoseWithCovarianceStamped, "initialpose", 10)

        delay = float(self.get_parameter("start_delay").value)
        self._timer = self.create_timer(delay, self._start)

    # ── build PoseStamped list ───────────────────────────────────────────
    def _pose(self, x, y, yaw):
        """Build a ``PoseStamped`` in ``frame_id`` from planar (x, y, yaw)."""
        p = PoseStamped()
        p.header.frame_id = self.frame_id
        p.header.stamp = self.get_clock().now().to_msg()
        p.pose.position.x = float(x)
        p.pose.position.y = float(y)
        qx, qy, qz, qw = _yaw_to_quat(yaw)
        p.pose.orientation.x, p.pose.orientation.y = qx, qy
        p.pose.orientation.z, p.pose.orientation.w = qz, qw
        return p

    def _publish_initial_pose(self):
        """Publish the ``initial_pose`` parameter on ``initialpose``."""
        x, y, yaw = self.get_parameter("initial_pose").value
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = self.frame_id
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = float(x)
        msg.pose.pose.position.y = float(y)
        qx, qy, qz, qw = _yaw_to_quat(float(yaw))
        msg.pose.pose.orientation.z, msg.pose.pose.orientation.w = qz, qw
        # modest covariance — AMCL will tighten as it converges
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.07
        self._init_pub.publish(msg)
        self.get_logger().info(f"Seeded AMCL initial pose at ({x}, {y}, {yaw} rad)")

    # ── mission ──────────────────────────────────────────────────────────
    def _start(self):
        """One-shot timer callback: seed the pose, wait for Nav2, send the goal."""
        self._timer.cancel()
        if self.get_parameter("set_initial_pose").value:
            self._publish_initial_pose()

        self.get_logger().info("Waiting for 'follow_waypoints' action server…")
        if not self._client.wait_for_server(timeout_sec=30.0):
            self.get_logger().error("follow_waypoints server not available — is Nav2 up?")
            return

        wps = mission_waypoints(return_home=self.get_parameter("return_home").value)
        goal = FollowWaypoints.Goal()
        goal.poses = [self._pose(x, y, yaw) for (x, y, yaw) in wps]
        self.get_logger().info(
            f"Sending {len(goal.poses)} bed-disinfection waypoints "
            "(Q1→Q2→Q3→Q4→home)…")

        fut = self._client.send_goal_async(goal, feedback_callback=self._on_feedback)
        fut.add_done_callback(self._on_goal_response)

    def _on_feedback(self, feedback):
        """Log the index of the waypoint currently being approached."""
        cur = feedback.feedback.current_waypoint
        self.get_logger().info(f"→ heading to waypoint {cur}", throttle_duration_sec=2.0)

    def _on_goal_response(self, future):
        """Handle goal acceptance and register the result callback."""
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error("FollowWaypoints goal REJECTED")
            return
        self.get_logger().info("Mission accepted — disinfecting beds.")
        handle.get_result_async().add_done_callback(self._on_result)

    def _on_result(self, future):
        """Log mission completion and any missed waypoints."""
        missed = future.result().result.missed_waypoints
        if missed:
            self.get_logger().warn(f"Mission done, missed waypoints: {list(missed)}")
        else:
            self.get_logger().info("Mission COMPLETE — all lanes covered, back home. ✅")


def main(args=None):
    """Entry point: spin a :class:`BedDisinfectionMission` until interrupted."""
    rclpy.init(args=args)
    node = BedDisinfectionMission()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
