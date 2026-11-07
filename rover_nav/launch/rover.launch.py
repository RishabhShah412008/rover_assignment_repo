from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='r1'),
        DeclareLaunchArgument('params_file', default_value=''),
        DeclareLaunchArgument('rover_id', default_value='972'),
        Node(
            package='rover_nav',
            executable='drive_node',
            name='drive_node',
            namespace=LaunchConfiguration('namespace'),
            parameters=[
            LaunchConfiguration('params_file'), 
            {'rover_id': LaunchConfiguration('rover_id')}
        ],
        ),
        Node(
            package='rover_nav',
            executable='odom_node',
            name='odom_node',
            namespace=LaunchConfiguration('namespace'),
            parameters=[
            LaunchConfiguration('params_file'), 
            {'rover_id': LaunchConfiguration('rover_id')}
        ],
        ),
        Node(
            package='rover_nav',
            executable='navigator_node',
            name='navigator_node',
            namespace=LaunchConfiguration('namespace'),
            parameters=[
            LaunchConfiguration('params_file'), 
            {'rover_id': LaunchConfiguration('rover_id')}
        ],
        ),
        Node(
            package='rover_power',
            executable='monitor_node',
            name='monitor_node',
            namespace=LaunchConfiguration('namespace'),
            parameters=[
            LaunchConfiguration('params_file'), 
            {'rover_id': LaunchConfiguration('rover_id')},
        ],
            output = 'screen'
        ),
        Node(
            package='rover_power',
            executable='power_node',
            name='power_node',
            namespace=LaunchConfiguration('namespace'),
            parameters=[
            LaunchConfiguration('params_file'), 
            {'rover_id': LaunchConfiguration('rover_id')}
        ],
        ),
        Node(
            package='rover_power',
            executable='health_node',
            name='health_node',
            namespace=LaunchConfiguration('namespace'),
            parameters=[
            LaunchConfiguration('params_file'), 
            {'rover_id': LaunchConfiguration('rover_id')}
        ],
        ),
    ])