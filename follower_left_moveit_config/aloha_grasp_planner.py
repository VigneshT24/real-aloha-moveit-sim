=#!/usr/bin/env python3
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

        self.arm_planner = self.aloha_moveit.get_planning_component("interbotix_arm")

        # prevent the commands from running in parallel and sequential instead
        self.is_executing = False

        # load the planning groups from setup assistant
        self.gripper_pub = self.node.create_publisher(JointSingleCommand, '/follower_left/commands/joint_single', 10)
        self.arm_pub = self.node.create_publisher(JointGroupCommand, '/follower_left/commands/joint_group', 10)

        # sub to yolo perception node output using self.node
        self.subscription = self.node.create_subscription(PoseStamped, '/grasp_pose', self.grasp_callback, 10)

        self.node.get_logger().info("Grasp Planner Ready. Waiting for YOLO detections on /grasp_pose.")
        self.node.get_logger().info("(18!) UPDATED CODED (18!)")

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

            # grab a fresh copy of the robot's mathematical state
            robot_model = self.aloha_moveit.get_robot_model()
            robot_state = RobotState(robot_model)
            robot_state.update() # syncs MoveIt with the real physical arm
            
            self.node.get_logger().info("Calculating Inverse Kinematics for target pose...")
            
            # ask MoveIt to solve the exact joint angles for this X/Y/Z coordinate
            ik_success = robot_state.set_from_ik("interbotix_arm", msg.pose, "follower_left/gripper_link", timeout=0.5)
            
            if not ik_success:
                self.node.get_logger().error("MoveIt IK failed to find a valid joint solution for this coordinate!")
                return
                
            # extract the calculated 6-DOF float array
            final_waypoint = robot_state.get_joint_group_positions("interbotix_arm")
            
            self.node.get_logger().info("IK solution found! Publishing JointGroupCommand to hardware...")
            
            # 4. Command the arm hardware to move to those calculated angles
            arm_msg = JointGroupCommand()
            arm_msg.name = 'arm'
            arm_msg.cmd = list(final_waypoint)
            self.arm_pub.publish(arm_msg)

            # wait for physical arm to complete for 4 seconds
            time.sleep(4.0)

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
            "\"{name: 'arm', cmd: [-0.016, -1.850, 1.595, 0.010, -1.8675, -0.011]}\""
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