#!/usr/bin/env python3
import rclpy
import time
import subprocess
from geometry_msgs.msg import PoseStamped
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState
from interbotix_xs_msgs.msg import JointSingleCommand, JointGroupCommand

class AlohaGraspPlanner:
    def __init__(self):
        # create a separate rclpy node for the YOLO subscriber
        self.node = rclpy.create_node('grasp_subscriber', use_global_arguments=False)
        self.node.get_logger().info("Initializing MoveIt 2 Python API.")

        # initialize the MoveIt environment (c++ node under the hood)
        self.aloha_moveit = MoveItPy(node_name="aloha_moveit_py")

        # load the planning groups from setup assistant
        self.gripper_pub = self.node.create_publisher(JointSingleCommand, '/follower_left/commands/joint_single', 10)
        self.arm_pub = self.node.create_publisher(JointGroupCommand, '/follower_left/commands/joint_group', 10)

        # sub to yolo perception node output using self.node
        self.subscription = self.node.create_subscription(PoseStamped, '/grasp_pose', self.grasp_callback, 10)

        self.node.get_logger().info("Grasp Planner Ready. Waiting for YOLO detections on /grasp_pose.")
        self.node.get_logger().info("(6!) UPDATED CODED (6!)")

    def grasp_callback(self, msg: PoseStamped):
        self.node.get_logger().info(f"Target Acquired := X: {msg.pose.position.x:.3f}, Y: {msg.pose.position.y:.3f}, Z: {msg.pose.position.z:.3f}")
        self.node.get_logger().info("Publishing raw OPEN command directly to LEFT FOLLOWER ARM ALOHA")

        up_msg = JointSingleCommand()
        up_msg.name = 'shoulder'
        up_msg.cmd = 0.05
        self.gripper_pub.publish(up_msg)

        self.node.get_logger().info("Shoulder up command executed.")
        time.sleep(3)
        # self.node.get_logger().info("Publishing raw OPEN commmand directly to LEFT FOLLOWER ARM ALOHA")

        # down_msg = JointSingleCommand()
        # down_msg.name = 'shoulder'
        # down_msg.cmd = -0.1
        # self.gripper_pub.publish(down_msg)

        # self.node.get_logger().info("Gripper close command executed.")

def main(args=None):
    # initialize the ros2
    rclpy.init(args=args)

    # instantiate the custom planner
    planner = AlohaGraspPlanner()

    try:
        # spin the specific subscriber node, not the class
        rclpy.spin(planner.node)
    except KeyboardInterrupt:
        planner.node.get_logger().warn("Ctrl+C detected! MoveIt context dying, using CLI override to save arm...")

        emergency_cmd = (
            "ros2 topic pub --once /follower_left/commands/joint_group "
            "interbotix_xs_msgs/msg/JointGroupCommand "
            "\"{name: 'arm', cmd: [-0.066, -1.850, 1.595, 0.094, -1.913, -0.081]}\""
        )
        subprocess.run(emergency_cmd, shell=True)
        
        print("Emergency CLI command sent. Safely shutting down.")
    finally:
        # clean up node safely when Ctrl-C is pressed
        planner.node.destroy_node()
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()