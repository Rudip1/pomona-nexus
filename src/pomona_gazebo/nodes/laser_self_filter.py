#!/usr/bin/env python3
# Copyright 2026 Pravin Oli
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author:  Pravin Oli
# Project: Pomona Nexus

"""Laser self-return filter for the low 360 deg 2D rslidar.

The pomona_uvc rslidar sits low (~0.351 m AGL) at the FRONT of the mounting
box and sweeps a full 360 deg plane. At that height the only on-board part that
intersects the plane is the rear operator display (display_link, ~0.40 m behind
the sensor): a 360 deg scan therefore paints a phantom obstacle that drags along
with the robot and smears the slam_toolbox map.

This node converts each beam's (angle, range) reading into an (x, y) endpoint in
the base_footprint frame and, if that endpoint lands inside the robot footprint
box, replaces the reading with +inf. slam_toolbox (use of max-range/inf readings)
then ray-traces those directions as FREE space up to max range instead of marking
an occupied endpoint -- so the robot's own body reads as free / explored rather
than as an obstacle. Readings that land OUTSIDE the footprint are passed through
untouched, so real obstacles (including ones directly behind the display, beyond
the body) are still mapped. Keeping the full 360 deg sweep, no angular trimming.

The sensor pose is a fixed, known transform (rslidar has zero rotation w.r.t.
base_footprint), so it is supplied as parameters rather than via a TF lookup.
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class LaserSelfFilter(Node):
    """Replace LiDAR returns that land on the robot body with ``+inf``.

    Subscribes to ``scan_raw`` and republishes on ``scan`` (both
    ``sensor_msgs/LaserScan``, sensor-data QoS).

    Parameters:
        sensor_x, sensor_y, sensor_yaw (float): LiDAR pose in
            ``base_footprint`` (defaults 0.37655, 0.0, 0.0).
        fp_x_min, fp_x_max, fp_y_min, fp_y_max (float): axis-aligned
            self-return box in ``base_footprint`` [m]
            (defaults -0.55, 0.52, -0.28, 0.28).
    """

    def __init__(self):
        super().__init__("laser_self_filter")

        # rslidar origin in base_footprint (box_link 0,0 + 0.37655 0 fwd offset;
        # zero yaw). Override per-model if the mount moves.
        self.declare_parameter("sensor_x", 0.37655)
        self.declare_parameter("sensor_y", 0.0)
        self.declare_parameter("sensor_yaw", 0.0)

        # Robot footprint box in base_footprint (axis-aligned). Defaults cover the
        # Scout V2 base (0.925 x 0.380) plus the rear display overhang, with a
        # small margin. Endpoints inside this box are treated as self-returns.
        self.declare_parameter("fp_x_min", -0.55)
        self.declare_parameter("fp_x_max", 0.52)
        self.declare_parameter("fp_y_min", -0.28)
        self.declare_parameter("fp_y_max", 0.28)

        self.sx = self.get_parameter("sensor_x").value
        self.sy = self.get_parameter("sensor_y").value
        self.syaw = self.get_parameter("sensor_yaw").value
        self.x_min = self.get_parameter("fp_x_min").value
        self.x_max = self.get_parameter("fp_x_max").value
        self.y_min = self.get_parameter("fp_y_min").value
        self.y_max = self.get_parameter("fp_y_max").value
        self._cos = math.cos(self.syaw)
        self._sin = math.sin(self.syaw)

        self.pub = self.create_publisher(LaserScan, "scan", qos_profile_sensor_data)
        self.sub = self.create_subscription(
            LaserScan, "scan_raw", self._on_scan, qos_profile_sensor_data
        )
        self.get_logger().info(
            "laser_self_filter: clearing self-returns inside footprint "
            f"x[{self.x_min},{self.x_max}] y[{self.y_min},{self.y_max}] "
            f"(sensor @ {self.sx:.4f},{self.sy:.4f}); scan_raw -> scan"
        )

    def _on_scan(self, msg: LaserScan):
        """Filter one scan in place and republish it."""
        ranges = list(msg.ranges)
        rmin, rmax = msg.range_min, msg.range_max
        for i, r in enumerate(ranges):
            if not math.isfinite(r) or r < rmin or r > rmax:
                continue
            ang = msg.angle_min + i * msg.angle_increment
            lx = r * math.cos(ang)
            ly = r * math.sin(ang)
            # laser frame -> base_footprint
            bx = self.sx + self._cos * lx - self._sin * ly
            by = self.sy + self._sin * lx + self._cos * ly
            if self.x_min <= bx <= self.x_max and self.y_min <= by <= self.y_max:
                ranges[i] = math.inf  # self-return -> free/explored, not occupied
        msg.ranges = ranges
        self.pub.publish(msg)


def main(args=None):
    """Entry point: spin a :class:`LaserSelfFilter` until interrupted."""
    rclpy.init(args=args)
    node = LaserSelfFilter()
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
