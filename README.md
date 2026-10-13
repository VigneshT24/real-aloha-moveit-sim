# Mobile ALOHA with ROS 2 MoveIt

This project uses ROS 2 MoveIt and the Trossen Robotics Mobile ALOHA to turn code into physical robot actions.

> **Note:** This README is a work in progress. Project details, tech stack, setup instructions, and other key information will be added once testing is complete and the source code has been verified.

## Instructions

### 1. Set up the terminals

1. Open the **Terminator** application in Linux and maximize the window.
2. Press `Ctrl + Shift + O` to split the window into a second terminal.
3. Click inside the new terminal, then press `Ctrl + Shift + E` to split it again.

You should now have three terminals.

### 2. Run the commands

Run the commands below, one set per terminal.

**Terminal 1**

```bash
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
ros2 launch aloha aloha_bringup.launch.py robot:=aloha_stationary use_cameras:=false
```

**Terminal 2**

```bash
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
ros2 launch follower_left_moveit_config run_planner.launch.py
```

**Terminal 3**

```bash
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
ros2 topic pub --once /grasp_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.3, y: 0.0, z: 0.2}, orientation: {w: 1.0}}}"
```

You should now see the left-follower arm successfully move.

## After changing the code

If you modify the code, rebuild the package in any free terminal:

```bash
cd ~/interbotix_ws
colcon build --packages-select aloha
```

Then clear all three terminals and re-run the commands from Step 2.