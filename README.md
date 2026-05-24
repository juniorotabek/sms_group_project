# Smart Warehouse Mobility Robot

## Project Title
Smart Warehouse Mobility Robot

## Objective
This project is a ROS 1 Noetic university group project for Smart Mobility Engineering. It simulates warehouse robot task flow, waypoint navigation, obstacle safety, emergency stop behavior, and robot status reporting while keeping the logic simple, well commented, and easy to extend.

## Current Implemented Scope
Implemented parts:

- Part 1: Base project foundation
- Part 2: Member 1 Task Management
- Part 3: Member 2 Navigation / Waypoint Simulation
- Part 4: Member 3 Obstacle Safety / Emergency Stop
- Part 5: Member 4 Battery System / Charging Behavior
- Part 6: Member 5 Package Handling
- Part 7: Member 6 Robot Status + Diagnostics
- Part 8: Member 7 Advanced CLI + Operations
- Part 9: Member 8 Testing + ROS Bag + Launch Validation

Coding status:

- Parts 1 to 9 are complete

## ROS 1 Noetic Package Overview
Package name: `smart_warehouse_robot`

Key folders:

- `src/smart_warehouse_robot/`
  - reusable Python package code
- `src/smart_warehouse_robot/nodes/`
  - ROS 1 node implementations using `rospy`
- `src/smart_warehouse_robot/services/`
  - pure task, navigation, safety, battery, package, and status simulation logic
- `scripts/`
  - thin ROS 1 executable wrappers for `rosrun`
- `launch/warehouse_demo.launch`
  - ROS 1 XML launch file
- `config/`
  - warehouse map and robot defaults
- `tests/`
  - pytest scenarios that do not require `roscore`
- `docs/`
  - architecture, member plan, and rosbag guide

## Setup on Ubuntu 20.04 with ROS Noetic
Create or use a catkin workspace:

```bash
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
git clone <repo-url>
cd ..
catkin_make
source devel/setup.bash
```

Install Python tools if needed:

```bash
sudo apt update
sudo apt install -y python3-pip python3-pytest python3-click
```

## Run the System
Start the ROS master:

```bash
roscore
```

In another terminal:

```bash
cd ~/catkin_ws
source devel/setup.bash
roslaunch smart_warehouse_robot warehouse_demo.launch
```

## Run Individual Nodes
```bash
rosrun smart_warehouse_robot task_publisher_node.py
rosrun smart_warehouse_robot task_queue_manager_node.py
rosrun smart_warehouse_robot waypoint_goal_publisher_node.py
rosrun smart_warehouse_robot path_progress_monitor_node.py
rosrun smart_warehouse_robot obstacle_detector_node.py
rosrun smart_warehouse_robot emergency_stop_node.py
rosrun smart_warehouse_robot battery_publisher_node.py
rosrun smart_warehouse_robot charging_controller_node.py
rosrun smart_warehouse_robot package_handler_node.py
rosrun smart_warehouse_robot status_publisher_node.py
rosrun smart_warehouse_robot diagnostic_logger_node.py
```

## Run the CLI
The CLI works without ROS running:

```bash
rosrun smart_warehouse_robot smart_warehouse_cli.py zones
rosrun smart_warehouse_robot smart_warehouse_cli.py create-task --type pickup --source receiving --destination storage_a --priority 3
rosrun smart_warehouse_robot smart_warehouse_cli.py nav-demo
rosrun smart_warehouse_robot smart_warehouse_cli.py safety-demo
rosrun smart_warehouse_robot smart_warehouse_cli.py battery-sample --percentage 20 --zone storage_a
rosrun smart_warehouse_robot smart_warehouse_cli.py charge-command-sample --percentage 20 --zone storage_a --reason "Low battery"
rosrun smart_warehouse_robot smart_warehouse_cli.py battery-demo
rosrun smart_warehouse_robot smart_warehouse_cli.py classify-battery --percentage 20
rosrun smart_warehouse_robot smart_warehouse_cli.py validate-battery --battery-json '{"battery_id":"BAT-001","robot_name":"warehouse_bot_01","percentage":20,"level":"low","charging_status":"not_charging","current_zone":"storage_a"}'
rosrun smart_warehouse_robot smart_warehouse_cli.py package-sample --source storage_a --destination shipping
rosrun smart_warehouse_robot smart_warehouse_cli.py package-demo
rosrun smart_warehouse_robot smart_warehouse_cli.py package-ros-commands
rosrun smart_warehouse_robot smart_warehouse_cli.py validate-package --package-json '{"package_id":"PKG-001","source_zone":"storage_a","destination_zone":"shipping","state":"waiting_for_pickup"}'
rosrun smart_warehouse_robot smart_warehouse_cli.py robot-status-sample --battery-percentage 80 --zone receiving
rosrun smart_warehouse_robot smart_warehouse_cli.py diagnostic-sample --source battery --level warning --message "Battery below threshold"
rosrun smart_warehouse_robot smart_warehouse_cli.py status-demo
rosrun smart_warehouse_robot smart_warehouse_cli.py diagnostics-demo
rosrun smart_warehouse_robot smart_warehouse_cli.py status-ros-commands
rosrun smart_warehouse_robot smart_warehouse_cli.py ros1-commands
```

## Advanced CLI and Operations
These commands support the mandatory Click CLI requirement and make the project easier to demonstrate and evaluate:

```bash
rosrun smart_warehouse_robot smart_warehouse_cli.py overview
rosrun smart_warehouse_robot smart_warehouse_cli.py demo-plan
rosrun smart_warehouse_robot smart_warehouse_cli.py ros-commands
rosrun smart_warehouse_robot smart_warehouse_cli.py member-summary
rosrun smart_warehouse_robot smart_warehouse_cli.py scenario full-json --json-output
rosrun smart_warehouse_robot smart_warehouse_cli.py scenario happy-path
rosrun smart_warehouse_robot smart_warehouse_cli.py scenario emergency-stop
rosrun smart_warehouse_robot smart_warehouse_cli.py scenario low-battery
rosrun smart_warehouse_robot smart_warehouse_cli.py validate all-samples
rosrun smart_warehouse_robot smart_warehouse_cli.py validate project-structure
rosrun smart_warehouse_robot smart_warehouse_cli.py validate no-ros2
rosrun smart_warehouse_robot smart_warehouse_cli.py bag record-command
rosrun smart_warehouse_robot smart_warehouse_cli.py launch-command
```

You can also run it directly during local development:

```bash
python3 scripts/smart_warehouse_cli.py zones
```

## Useful Topic Checks
```bash
rostopic list
rostopic echo /warehouse/tasks/new
rostopic echo /warehouse/tasks/status
rostopic echo /warehouse/navigation/goal
rostopic echo /warehouse/navigation/progress
rostopic echo /warehouse/safety/obstacle
rostopic echo /warehouse/safety/emergency_stop
rostopic echo /warehouse/battery/state
rostopic echo /warehouse/battery/return_to_charge
rostopic echo /warehouse/package/status
rostopic echo /warehouse/robot/status
rostopic echo /warehouse/robot/diagnostics
```

## Package Services
The package handler exposes ROS 1 Trigger services:

```bash
rosservice list
rosservice call /warehouse/package/pickup
rosservice call /warehouse/package/dropoff
rosservice call /warehouse/package/reset
```

## Run Pytest
The pytest suite is designed to run without `roscore`:

```bash
cd ~/catkin_ws/src/smart_warehouse_robot
pytest
```

## Final Coding Validation
Run important scenario tests:

```bash
pytest tests/test_full_happy_path_scenario.py
pytest tests/test_full_emergency_stop_scenario.py
pytest tests/test_full_low_battery_scenario.py
```

Run launch validation:

```bash
pytest tests/test_launch_file_validation.py
```

Run ROS 1 compatibility validation:

```bash
pytest tests/test_ros1_compatibility.py
```

Run project structure validation:

```bash
pytest tests/test_project_structure_validation.py
```

## ROS Bag Recording
Record the full demo topic set:

```bash
mkdir -p bags
rosbag record -O bags/final_demo.bag /warehouse/tasks/new /warehouse/tasks/status /warehouse/navigation/goal /warehouse/navigation/progress /warehouse/safety/obstacle /warehouse/safety/emergency_stop /warehouse/battery/state /warehouse/battery/return_to_charge /warehouse/package/status /warehouse/robot/status /warehouse/robot/diagnostics
```

Replay:

```bash
rosbag play bags/final_demo.bag
```

Inspect:

```bash
rosbag info bags/final_demo.bag
```

Bag helper scripts:

```bash
bash scripts/record_demo_bag.sh
bash scripts/check_demo_bag.sh
bash scripts/replay_demo_bag.sh
bash scripts/run_demo_instructions.sh
```

## Final Implemented Members
- Member 1 Task Management
- Member 2 Navigation
- Member 3 Obstacle Safety
- Member 4 Battery System
- Member 5 Package Handling
- Member 6 Robot Status + Diagnostics
- Member 7 Advanced CLI + Operations
- Member 8 Testing + ROS Bag + Launch Validation

## Git and Repository Hygiene
Do not commit generated or compiled files such as:

- `build/`
- `devel/`
- `install/`
- `logs/`
- `__pycache__/`
- `*.pyc`

Large bag files are normally ignored in `.gitignore`. Keep only the final required demo bag if your instructor specifically asks for it.
