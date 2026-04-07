import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('amr_rl_navigation')
    
    # Paths to the world and URDF files we created
    world_path = os.path.join(pkg_share, 'worlds', 'rl_arena.world')
    urdf_path = os.path.join(pkg_share, 'urdf', 'amr.urdf')

    # Start Gazebo and load the empty arena world
    gazebo_pkg_share = get_package_share_directory('gazebo_ros')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_pkg_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_path}.items()
    )

    # Spawn the AMR robot inside the Gazebo world
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'amr_robot', '-file', urdf_path, '-x', '0', '-y', '0', '-z', '0.1'],
        output='screen'
    )

    # Publish the robot's state (transforms)
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()
        
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher_node,
        spawn_entity
    ])
