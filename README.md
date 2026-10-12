The focus is on using ROS 2 Moveit and Trossen Robotics Mobile ALOHA to perform code to physical actions.

The README will be completed with more information about the project details, tech-stack used, setup instructions, and other critical information once enough testing has been conducted and the source code has been verified.

Commands:

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
ros2 launch aloha aloha_bringup.launch.py robot:=aloha_stationary use_cameras:=false
```

Terminal 2:

```bash
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
ros2 launch follower_left_moveit_config run_planner.launch.py
```

Terminal 3:

```bash
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
ros2 topic pub --once /grasp_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'world'}, pose: {position: {x: 0.3, y: 0.0, z: 0.2}, orientation: {w: 1.0}}}"
```

The instruction NEEDS to be updated in the future so that other users can run it after cloning the repo!