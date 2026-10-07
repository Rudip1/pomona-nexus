#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pravin Oli
#
# Pomona UV-C controller.
#
#   * Owns the on/off state of the 12 UV-C lamps (left_0..5, right_0..5).
#   * Exposes std_srvs/SetBool services to switch them:
#         /uvc/all          all 12
#         /uvc/left         left panel (6)
#         /uvc/right        right panel (6)
#         /uvc/lamp/<side>_<i>   one lamp        (e.g. /uvc/lamp/left_3)
#   * Publishes /uvc/lamp_states (std_msgs/Int8MultiArray) which the Gazebo
#     plugin (pomona_uvc_toggle) consumes to enable/disable the blue ray sensors.
#   * Accumulates a UV-C *dose* grid where lit lamps dwell and publishes it as a
#     nav_msgs/OccupancyGrid on /uvc/dose — the disinfection "blobs" in RViz.
#     Dose-rate vs distance reuses the vf_robot_disinfection model.

import math

import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

from std_msgs.msg import Int8MultiArray
from std_srvs.srv import SetBool
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import Pose

import tf2_ros


class UvcController(Node):
    """ROS 2 node that switches the 12 UV-C lamps and integrates a dose map.

    Lamp state is held in memory (all OFF at start) and changed only through
    ``std_srvs/SetBool`` services. Every ``dt`` = 0.1 s the node publishes the
    lamp states and, for each lit lamp, deposits dose into a square grid
    centred on the lamp's ground position (looked up via TF
    ``dose_frame`` <- ``base_frame``). The grid is published at 2 Hz as an
    ``OccupancyGrid`` normalised to ``sufficient_dose``.

    Parameters:
        lamps_per_side (int, 6): lamps on each panel.
        dose_frame (str, 'odom'): fixed frame of the dose grid.
        base_frame (str, 'base_footprint'): robot frame the lamps are attached to.
        dose_resolution (float, 0.05): grid cell size [m].
        dose_size_m (float, 24.0): grid side length [m], centred on the origin.
        max_radiation_distance (float, 0.6): footprint radius per lamp [m].
        sufficient_dose (float, 800.0): dose that maps to 100 in the grid.
        dose_rate_scale (float, 10.0): multiplier on the per-tick dose rate.

    Publishes:
        /uvc/lamp_states (std_msgs/Int8MultiArray): 1 = lit, ordered
            left_0..left_{n-1}, right_0..right_{n-1}.
        /uvc/dose (nav_msgs/OccupancyGrid): -1 undosed, 1..100 dose fraction.

    Services (std_srvs/SetBool):
        /uvc/all, /uvc/left, /uvc/right, /uvc/lamp/<side>_<i>.

    TODO: the dose units are not calibrated; document the physical meaning of
    ``sufficient_dose`` and ``dose_rate_scale``.
    """

    def __init__(self):
        super().__init__('uvc_controller')

        # ── lamp geometry (base_footprint frame) — matches uvc_emit_* joints ──
        n = self.declare_parameter('lamps_per_side', 6).value
        panel_x_c, panel_len, inset = 0.065, 0.73, 0.08
        step = (panel_len - 2 * inset) / (n - 1)
        x0 = panel_x_c - panel_len / 2 + inset           # = -0.22
        xs = [x0 + i * step for i in range(n)]
        self.lamp_xy = [(x, 1.0) for x in xs] + [(x, -1.0) for x in xs]   # left, right
        self.names = [f'left_{i}' for i in range(n)] + [f'right_{i}' for i in range(n)]
        self.n_lamps = len(self.names)

        # default OFF — lamps come on only via a service call
        self.state = [False] * self.n_lamps

        # ── dose map params ──────────────────────────────────────────────────
        self.frame = self.declare_parameter('dose_frame', 'odom').value
        self.base_frame = self.declare_parameter('base_frame', 'base_footprint').value
        self.res = self.declare_parameter('dose_resolution', 0.05).value
        size_m = self.declare_parameter('dose_size_m', 24.0).value
        self.cells = int(size_m / self.res)
        self.origin = -size_m / 2.0                       # grid origin x=y=-size/2
        self.dose = np.zeros((self.cells, self.cells), dtype=np.float32)
        self.max_dist = self.declare_parameter('max_radiation_distance', 0.6).value
        self.threshold = self.declare_parameter('sufficient_dose', 800.0).value
        self.dose_rate_scale = self.declare_parameter('dose_rate_scale', 10.0).value

        # ── pubs / subs / services ───────────────────────────────────────────
        self.state_pub = self.create_publisher(Int8MultiArray, '/uvc/lamp_states', 10)
        self.dose_pub = self.create_publisher(OccupancyGrid, '/uvc/dose', 1)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self._make_service('/uvc/all', lambda v: self._set(range(self.n_lamps), v))
        self._make_service('/uvc/left', lambda v: self._set(range(0, n), v))
        self._make_service('/uvc/right', lambda v: self._set(range(n, 2 * n), v))
        for idx, name in enumerate(self.names):
            self._make_service(f'/uvc/lamp/{name}',
                               (lambda i: (lambda v: self._set([i], v)))(idx))

        self.dt = 0.1
        self.create_timer(self.dt, self._tick)            # dose accumulation + state pub (10 Hz)
        self.create_timer(0.5, self._publish_dose)        # dose grid (2 Hz)

        self.get_logger().info(
            f'UV-C controller up: {self.n_lamps} lamps (default OFF). '
            f'Services: /uvc/all /uvc/left /uvc/right /uvc/lamp/<name>. '
            f'Dose grid {self.cells}x{self.cells}@{self.res} m in [{self.frame}].')
        self._publish_states()

    # ── services ─────────────────────────────────────────────────────────────
    def _make_service(self, name, apply_fn):
        """Create a SetBool service ``name`` that calls ``apply_fn(data)``."""
        def cb(req, resp):
            apply_fn(req.data)
            self._publish_states()
            on = sum(self.state)
            resp.success = True
            resp.message = f'{name.split("/")[-1]} -> {"ON" if req.data else "OFF"} ({on}/{self.n_lamps} lit)'
            self.get_logger().info(resp.message)
            return resp
        self.create_service(SetBool, name, cb)

    def _set(self, indices, value):
        """Set the lamps at ``indices`` to ``value`` (True = lit)."""
        for i in indices:
            self.state[i] = bool(value)

    def _publish_states(self):
        """Publish the current lamp states on ``/uvc/lamp_states``."""
        msg = Int8MultiArray()
        msg.data = [1 if s else 0 for s in self.state]
        self.state_pub.publish(msg)

    # ── periodic ─────────────────────────────────────────────────────────────
    def _tick(self):
        """10 Hz timer: publish lamp states and deposit dose for lit lamps."""
        self._publish_states()
        if not any(self.state):
            return
        try:
            tf = self.tf_buffer.lookup_transform(
                self.frame, self.base_frame, rclpy.time.Time(),
                timeout=Duration(seconds=0.05))
        except Exception:
            return
        t = tf.transform.translation
        q = tf.transform.rotation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        c, s = math.cos(yaw), math.sin(yaw)
        for i, on in enumerate(self.state):
            if not on:
                continue
            lx, ly = self.lamp_xy[i]
            wx = t.x + lx * c - ly * s
            wy = t.y + lx * s + ly * c
            self._deposit(wx, wy)

    def _deposit(self, wx, wy):
        """Add one tick of dose around world point (``wx``, ``wy``)."""
        # accumulate dose in the lamp's ground footprint, distance-falloff per
        # the vf_robot_disinfection model: f = 0.577 d^2 - 3.21 d + 4.843
        gx = int((wx - self.origin) / self.res)
        gy = int((wy - self.origin) / self.res)
        r = int(math.ceil(self.max_dist / self.res))
        x0, x1 = max(0, gx - r), min(self.cells, gx + r + 1)
        y0, y1 = max(0, gy - r), min(self.cells, gy + r + 1)
        if x0 >= x1 or y0 >= y1:
            return
        ys, xs = np.mgrid[y0:y1, x0:x1]
        cxw = self.origin + (xs + 0.5) * self.res
        cyw = self.origin + (ys + 0.5) * self.res
        d = np.sqrt((cxw - wx) ** 2 + (cyw - wy) ** 2)
        mask = d <= self.max_dist
        f = (0.577 * d * d - 3.21 * d + 4.843)
        f = np.clip(f, 0.0, None) * self.dt * self.dose_rate_scale
        self.dose[y0:y1, x0:x1][mask] += f[mask]

    def _publish_dose(self):
        """2 Hz timer: publish the dose grid on ``/uvc/dose``."""
        grid = OccupancyGrid()
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.header.frame_id = self.frame
        grid.info.resolution = self.res
        grid.info.width = self.cells
        grid.info.height = self.cells
        grid.info.origin.position.x = self.origin
        grid.info.origin.position.y = self.origin
        grid.info.origin.orientation.w = 1.0
        norm = np.clip(self.dose / self.threshold, 0.0, 1.0)
        data = np.full(self.dose.shape, -1, dtype=np.int16)          # undosed = unknown (transparent)
        lit = self.dose > 0.0
        data[lit] = np.maximum(1, (norm[lit] * 100).astype(np.int16))
        grid.data = data.flatten().astype(np.int8).tolist()
        self.dose_pub.publish(grid)


def main():
    """Entry point: spin a :class:`UvcController` until interrupted."""
    rclpy.init()
    node = UvcController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
