#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # build the base configurations
    moveit_config = (
        MoveItConfigsBuilder("aloha_vx300s", package_name="follower_left_moveit_config")
        .planning_pipelines(pipelines=["ompl"])
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .to_moveit_configs()
    )

    moveit_py_dict = moveit_config.to_dict()
    
    # inject the STRICTLY NESTED parameters that MoveItCpp demands
    moveit_py_dict.update({
        "planning_pipelines": {
            "pipeline_names": ["ompl"]
        },
        "plan_request_params": {
            "planning_attempts": 1,
            "planning_pipeline": "ompl",
            "max_velocity_scaling_factor": 1.0,
            "max_acceleration_scaling_factor": 1.0
        }
    })

    planner_node = Node(
        package="follower_left_moveit_config",
        executable="aloha_grasp_planner.py",
        name="aloha_moveit_py",
        parameters=[moveit_py_dict],
        # remappings=[
        #     ('/interbotix_arm_controller/follow_joint_trajectory', '/follower_left/interbotix_arm_controller/follow_joint_trajectory'),
        #     ('/interbotix_gripper_controller/follow_joint_trajectory', '/follower_left/interbotix_gripper_controller/follow_joint_trajectory'),
        #     ('/joint_states', '/follower_left/joint_states'),
        # ],
        output="screen",
    )

    return LaunchDescription([planner_node])