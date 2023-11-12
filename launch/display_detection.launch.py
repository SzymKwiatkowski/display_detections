from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='display_detections',
            executable='display_detections',
            name='display_detections',
            remappings=[
                ('~/image', '/color/image'),
                ('~/detections', '/color/mobilenet_detections'),
            ]
        )
    ])