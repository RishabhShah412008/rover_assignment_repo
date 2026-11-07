from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('rover_nav'), 'launch'])
    
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([launch_dir, 'rover.launch.py'])
            ),
            launch_arguments={
                'namespace': 'r1',
                'rover_id': '972'
            }.items()
        ),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([launch_dir, 'rover.launch.py'])
            ),
            launch_arguments={
                'namespace': 'r2',
                'rover_id': '397'
            }.items()
        )
    ])