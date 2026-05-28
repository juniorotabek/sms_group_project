# Sensors Used in the Smart Warehouse Robot

This file lists the sensors and sensor-like inputs currently used by the robot based on the URDF, ROS nodes, and runtime topics in this workspace.

## Physical Sensors

### 1. LiDAR
- **URDF frame:** `lidar_link`
- **Mounted on:** `sensor_mast`
- **Purpose:** Used as the robot's primary perception sensor for obstacle detection.
- **Notes:** The robot model defines a LiDAR frame in the URDF, and the safety/obstacle pipeline uses obstacle readings derived from this sensor path.

## Simulated Sensor Inputs

These are not physical hardware sensors in the model, but they behave like sensor feeds in the ROS demo.

### 2. Obstacle Detection Input
- **Topic:** `/warehouse/safety/obstacle`
- **Node:** `obstacle_detector_node.py`
- **Purpose:** Simulates obstacle readings and triggers safety logic.
- **Data type:** `std_msgs/String` carrying JSON obstacle readings.

### 3. LiDAR Scan Data
- **Topic:** `/warehouse/lidar/scan`
- **Node:** `rviz_delivery_visualizer_node.py`
- **Purpose:** Publishes a synthetic 2D LiDAR scan so RViz can display the robot's sensing field.
- **Data type:** `sensor_msgs/LaserScan`

### 4. LiDAR Analysis Overlay
- **Topic:** `/warehouse/lidar/analysis`
- **Node:** `rviz_delivery_visualizer_node.py`
- **Purpose:** Shows a live RViz text summary of the LiDAR scan, including min range, average hit range, and hit count.
- **Data type:** `visualization_msgs/Marker` text marker

### 5. Battery State Input
- **Topic:** `/warehouse/battery/state`
- **Node:** `battery_publisher_node.py`
- **Purpose:** Simulates battery percentage and charging status.
- **Data type:** `std_msgs/String` carrying JSON battery state.

### 6. Navigation Progress Input
- **Topic:** `/warehouse/navigation/progress`
- **Node:** `path_progress_monitor_node.py`
- **Purpose:** Simulates motion progress and arrival status for the robot.
- **Data type:** `std_msgs/String` carrying JSON progress updates.

### 7. Package Status Input
- **Topic:** `/warehouse/package/status`
- **Node:** `package_handler_node.py`
- **Purpose:** Simulates package pickup, carrying, delivered, and reset states.
- **Data type:** `std_msgs/String` carrying JSON package events.

### 8. Robot Status Aggregation
- **Topic:** `/warehouse/robot/status`
- **Node:** `status_publisher_node.py`
- **Purpose:** Aggregates battery, navigation, package, and safety state into one status stream.
- **Data type:** `std_msgs/String` carrying JSON robot status snapshots.

## Not Present as Dedicated Sensors

The current robot model and demo do **not** define these as dedicated sensors:
- Camera
- IMU
- GPS
- Wheel encoders
- Depth sensor

## Summary

If you want the strict physical-sensor list only, the current robot has:
- **LiDAR** (`lidar_link`)

If you want the full runtime sensing pipeline used by the demo, include:
- Obstacle detection input
- Battery state input
- Navigation progress input
- Package status input
- Robot status aggregation
