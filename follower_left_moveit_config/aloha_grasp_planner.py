#!/usr/bin/env python3
import rclpy
import time
import subprocess
import threading
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

        # prevent the commands from running in parallel and sequential instead
        self.is_executing = False

        # load the planning groups from setup assistant
        self.gripper_pub = self.node.create_publisher(JointSingleCommand, '/follower_left/commands/joint_single', 10)
        self.arm_pub = self.node.create_publisher(JointGroupCommand, '/follower_left/commands/joint_group', 10)

        # sub to yolo perception node output using self.node
        self.subscription = self.node.create_subscription(PoseStamped, '/grasp_pose', self.grasp_callback, 10)

        self.node.get_logger().info("Grasp Planner Ready. Waiting for YOLO detections on /grasp_pose.")

    def grasp_callback(self, msg: PoseStamped):
        if self.is_executing:
            self.node.get_logger().warn("Finishing the current action before moving onto the next one.")
            return

        self.is_executing = True

        sequence_thread = threading.Thread(target=self.execute_sequence, args=(msg,), daemon=True)
        sequence_thread.start()

    def execute_sequence(self, msg:PoseStamped):
        try:
            self.node.get_logger().info(f"Target Acquired := X: {msg.pose.position.x:.3f}, Y: {msg.pose.position.y:.3f}, Z: {msg.pose.position.z:.3f}")
            self.node.get_logger().info("Publishing raw OPEN command directly to LEFT FOLLOWER ARM ALOHA")

            up_msg = JointSingleCommand()
            up_msg.name = 'wrist_angle'
            up_msg.cmd = 0.01
            self.gripper_pub.publish(up_msg)

            self.node.get_logger().info("Wrist up command executed.")
            time.sleep(4.0)

            open_gripper = JointSingleCommand()
            open_gripper.name = 'gripper'
            open_gripper.cmd = 1.50
            self.gripper_pub.publish(open_gripper)

            self.node.get_logger().info("Gripper open up command executed.")
            time.sleep(4.0)

            close_gripper = JointSingleCommand()
            close_gripper.name = 'gripper'
            close_gripper.cmd = 0.6
            self.gripper_pub.publish(close_gripper)
            time.sleep(4.0)

            self.node.get_logger().info("Gripper close command executed.")
        finally:
            self.is_executing = False

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
            "\"{name: 'arm', cmd: [-0.066, -1.850, 1.595, 0.094, -1.8675, -0.081]}\""
        )
        subprocess.run(emergency_cmd, shell=True)
        time.sleep(5)
        print("Emergency CLI command sent. Safely shutting down.")
    finally:
        # clean up node safely when Ctrl-C is pressed
        planner.node.destroy_node()
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()