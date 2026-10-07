# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Pravin Oli
#
# Brings up the UV-C controller (lamp on/off services + disinfection dose map).
# Run alongside the pomona_uvc Gazebo sim. Optionally opens RViz with the dose
# "blobs" pre-configured.
#
#   ros2 launch pomona_uvc uvc_control.launch.py            # node only
#   ros2 launch pomona_uvc uvc_control.launch.py rviz:=true # + RViz dose view

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = get_package_share_directory('pomona_uvc')

    rviz = LaunchConfiguration('rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='false',
                              description='Open RViz with the UV-C dose display'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        Node(
            package='pomona_uvc',
            executable='uvc_controller.py',
            name='uvc_controller',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            condition=IfCondition(rviz),
            arguments=['-d', os.path.join(pkg, 'rviz', 'uvc.rviz')],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ])
