#!/usr/bin/env python3
import rclpy
import time
from geometry_msgs.msg import PoseStamped
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState

class AlohaGraspPlanner:
    def __init__(self):
        # create a separate rclpy node for the YOLO subscriber
        self.node = rclpy.create_node('grasp_subscriber', use_global_arguments=False)
        self.node.get_logger().info("Initializing MoveIt 2 Python API.")

        # initialize the MoveIt environment (c++ node under the hood)
        self.aloha_moveit = MoveItPy(node_name="aloha_moveit_py")

        # load the planning groups from setup assistant
        self.arm = self.aloha_moveit.get_planning_component("interbotix_arm")
        self.gripper = self.aloha_moveit.get_planning_component("interbotix_gripper")

        # sub to yolo perception node output using self.node
        self.subscription = self.node.create_subscription(
            PoseStamped, '/grasp_pose', self.grasp_callback, 10
        )

        self.node.get_logger().info("Grasp Planner Ready. Waiting for YOLO detections on /grasp_pose.")
        self.node.get_logger().info("UPDATED CODE IS RUNNING!")

    def grasp_callback(self, msg: PoseStamped):
        self.node.get_logger().info(f"Target Acquired := X: {msg.pose.position.x:.3f}, Y: {msg.pose.position.y:.3f}, Z: {msg.pose.position.z:.3f}")

        self.node.get_logger().info("Performing basic open gripper action.")

        # create arm wake up state
        arm_state = RobotState(self.aloha_moveit.get_robot_model())
        arm_state.set_to_default_values()
        arm_state.set_joint_group_positions("interbotix_arm", [0.0, -0.8, 0.0, 0.0, 0.8, 0.0])

        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(robot_state=arm_state)

        arm_state_plan = self.arm.plan()

        if arm_state_plan:
            self.aloha_moveit.execute("interbotix_arm", arm_state_plan.trajectory, blocking=True)
            self.node.get_logger().info("Successfully moved the entire arm")
        else:
            self.node.get_logger().error("Arm unable to move to goal position")

def main(args=None):
    # initialize the ros2
    rclpy.init(args=args)

    # instantiate the custom planner
    planner = AlohaGraspPlanner()

    try:
        # spin the specific subscriber node, not the class
        rclpy.spin(planner.node)
    except KeyboardInterrupt:
        planner.node.get_logger().info("Shutting down planner node.")
    finally:
        # clean up node safely when Ctrl-C is pressed
        planner.node.destroy_node()
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()