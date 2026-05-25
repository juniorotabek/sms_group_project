# RViz - Quick Reference

## TL;DR: Get Visualization Running Right Now (RViz)

```bash
# Terminal 1
roscore

# Terminal 2
cd ~/catkin_ws && source devel/setup.bash && roslaunch smart_warehouse_robot demo_with_rviz_delivery.launch

# Terminal 3
rosrun rviz rviz

# In RViz: Set Fixed Frame → map, Add → RobotModel (robot_description param), Add → TF
```

You'll see the robot moving between zones while the package marker travels from pickup to delivery.
You will also see distinct location markers: an orange pickup cylinder and a green dropoff sphere.

If you want the delivery demo in one command, use:

```bash
cd ~/catkin_ws && source devel/setup.bash && roslaunch smart_warehouse_robot demo_with_rviz_delivery.launch
```


## RViz

| Use Case | Tool |
| Monitor robot state, debug, TF tree | **RViz** |
| Quick setup, no simulation dependencies | **RViz** |
| See the robot model, wheels, mast, and TF tree | **RViz** |



---

## Files Overview

- **warehouse_robot.urdf** - 3D robot model (mobile base + wheels + sensor)
- **demo_with_rviz_delivery.launch** - Starts the full RViz delivery simulation

This workspace is configured for RViz-based 3D visualization.
