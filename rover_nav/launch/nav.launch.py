import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('rover_nav')
    rover_params_file = os.path.join(pkg_share, 'config', 'rover_params.yaml')
    return LaunchDescription([Node(package = 'rover_nav', executable = 'drive_node', name = 'drive_node', parameters = [rover_params_file]), 
                              Node(package = 'rover_nav', executable = 'odom_node', name = 'odom_node', parameters = [rover_params_file]),
                              Node(package = 'rover_nav', executable = 'navigator_node', name = 'navigator_node', parameters = [rover_params_file])])