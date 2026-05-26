# Smart Warehouse Robot - Architecture & Run Guide

## Table of Contents

1. [Project Overview](#project-overview)
2. [Internal Architecture](#internal-architecture)
3. [Component Structure](#component-structure)
4. [Data Flow](#data-flow)
5. [Setup Instructions](#setup-instructions)
6. [Running the Project](#running-the-project)
7. [3D Visualization with Gazebo](#3d-visualization-with-gazebo)
8. [Testing & Validation](#testing--validation)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

**Smart Warehouse Mobility Robot** is a ROS 1 Noetic-based simulation of an autonomous warehouse robot that:

- Receives and queues warehouse tasks
- Navigates between warehouse zones
- Detects obstacles and triggers emergency stops
- Monitors battery state and returns for charging
- Handles package pickup/dropoff operations
- Publishes robot status and diagnostics
- Provides an advanced CLI interface
- Validates behavior through pytest scenarios
- Records ROS bag data for review
- Includes 3D Gazebo simulation with physics and collisions

**Technology Stack:**
- Ubuntu 20.04
- ROS 1 Noetic
- Python 3 (3.6+)
- catkin (build system)
- pytest (testing - requires Python 3)
- click (CLI)
- rosbag (recording)
- Gazebo (3D simulation with physics)

---

## Internal Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                   SMART WAREHOUSE ROBOT                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           ROS 1 Noetic Message Bus                  │  │
│  │  (Topics & Services via std_msgs/String & Trigger)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ▲                                   │
│         ┌────────────────┼────────────────┐                │
│         │                │                │                │
│    ┌────▼──────┐  ┌─────▼────┐  ┌───────▼────┐            │
│    │ Task Flow │  │ Safety   │  │ Battery    │            │
│    │ Subsystem │  │ Subsystem│  │ Subsystem  │            │
│    └────┬──────┘  └─────┬────┘  └───────┬────┘            │
│         │                │                │                │
│    ┌────▼──────┐  ┌─────▼────┐  ┌───────▼────┐            │
│    │Navigation │  │ Package  │  │ Status &   │            │
│    │ Subsystem │  │ Subsystem│  │ Diagnostics│            │
│    └───────────┘  └──────────┘  └────────────┘            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         CLI Interface & ROS Bag Recording            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure Explanation

```
smart_warehouse_robot/
│
├── src/smart_warehouse_robot/          # Main Python package
│   ├── common/                         # Shared utilities
│   │   ├── models.py                  # Data models (Task, Goal, etc.)
│   │   ├── constants.py               # Configuration constants
│   │   └── helpers.py                 # Utility functions
│   │
│   ├── services/                       # Pure business logic
│   │   ├── task_queue.py              # Task queue management
│   │   ├── navigation.py              # Navigation logic
│   │   ├── safety.py                  # Safety classification
│   │   ├── battery.py                 # Battery state logic
│   │   ├── package_handler.py         # Package operations
│   │   └── status.py                  # Status aggregation
│   │
│   ├── nodes/                          # ROS node implementations
│   │   ├── task_publisher.py          # Creates new tasks
│   │   ├── task_queue_manager.py      # Manages task queue
│   │   ├── waypoint_goal_publisher.py # Convert tasks → navigation goals
│   │   ├── path_progress_monitor.py   # Simulate movement
│   │   ├── obstacle_detector.py       # Simulate obstacles
│   │   ├── emergency_stop.py          # Safety trigger
│   │   ├── battery_publisher.py       # Battery state simulation
│   │   ├── charging_controller.py     # Return-to-charge logic
│   │   ├── package_handler.py         # Package services
│   │   ├── status_publisher.py        # Aggregate robot status
│   │   └── diagnostic_logger.py       # Generate diagnostics
│   │
│   └── cli.py                         # Advanced Click CLI
│
├── scripts/                            # Executable node scripts
│   ├── *_node.py                      # ROS node wrappers
│   ├── smart_warehouse_cli.py         # CLI interface
│   ├── record_demo_bag.sh             # Record ROS bag
│   ├── replay_demo_bag.sh             # Replay ROS bag
│   ├── check_demo_bag.sh              # Inspect ROS bag
│   └── run_demo_instructions.sh       # Print demo steps
│
├── launch/
│   ├── warehouse_demo.launch          # Launch all nodes
│   └── gazebo_warehouse.launch        # Launch Gazebo world and robot
│
├── config/
│   ├── warehouse_map.yaml             # Zone definitions
│   └── robot_config.yaml              # Robot parameters
│
├── tests/                              # Test suite
│   ├── test_full_*.py                 # Scenario tests
│   ├── test_*_logic.py                # Unit tests
│   └── test_*.py                      # Model & service tests
│
└── docs/                               # Documentation
    ├── architecture_overview.md       # System design
    └── testing_guide.md               # Test documentation
```

---

## Component Structure

### 1. Common Module (`src/smart_warehouse_robot/common/`)

**Purpose:** Shared data models and utilities

- **models.py**: Defines data structures (Task, NavigationGoal, BatteryState, etc.)
- **constants.py**: Warehouse zones, default parameters, message types
- **helpers.py**: JSON serialization, zone distance calculation, classification

### 2. Services Module (`src/smart_warehouse_robot/services/`)

**Purpose:** Pure business logic (testable without ROS)

| Service | Responsibility |
|---------|-----------------|
| `task_queue.py` | Queue operations, task lifecycle |
| `navigation.py` | Distance calculations, zone validation |
| `safety.py` | Obstacle classification (safe/warning/critical) |
| `battery.py` | Battery state tracking, thresholds |
| `package_handler.py` | Pickup/dropoff state management |
| `status.py` | Aggregate robot status from all subsystems |

### 3. Nodes Module (`src/smart_warehouse_robot/nodes/`)

**Purpose:** ROS node wrappers that use services and publish/subscribe to topics

Each node:
1. Imports service logic from `services/`
2. Subscribes to ROS topics
3. Processes messages through service logic
4. Publishes results to ROS topics
5. Implements ROS services (for package handler)

### 4. Script Entries (`scripts/`)

Each script is an executable entry point:
```python
#!/usr/bin/env python3
import rospy
from smart_warehouse_robot.nodes import TaskPublisherNode

if __name__ == '__main__':
    rospy.init_node('task_publisher')
    node = TaskPublisherNode()
    node.run()
```

---

## Data Flow

### Complete Workflow Chain

```
1. TASK CREATION & QUEUEING
   ├─ TaskPublisherNode publishes sample tasks
   └─ → /warehouse/tasks/new (JSON payload)
        └─ TaskQueueManagerNode receives, queues, manages
           └─ → /warehouse/tasks/status (updated task status)

2. NAVIGATION CONVERSION
   ├─ WaypointGoalPublisherNode converts started tasks to goals
   └─ → /warehouse/navigation/goal (JSON payload)
        └─ PathProgressMonitorNode simulates movement
           └─ → /warehouse/navigation/progress (% complete)

3. SAFETY MONITORING
   ├─ ObstacleDetectorNode simulates sensor readings
   └─ → /warehouse/safety/obstacle (distance & zone)
        └─ EmergencyStopNode classifies & triggers
           └─ → /warehouse/safety/emergency_stop (alert)
                └─ PathProgressMonitorNode halts if emergency

4. BATTERY MANAGEMENT
   ├─ BatteryPublisherNode tracks battery from navigation progress
   └─ → /warehouse/battery/state (percentage & zone)
        └─ ChargingControllerNode detects low battery
           ├─ → /warehouse/battery/return_to_charge (command)
           └─ → /warehouse/navigation/goal (return to charging_station)

5. PACKAGE OPERATIONS
   ├─ rosservice call /warehouse/package/pickup
   ├─ → PackageHandlerNode processes
   └─ → /warehouse/package/status (pickup confirmed)
   
   ├─ rosservice call /warehouse/package/dropoff
   ├─ → PackageHandlerNode processes
   └─ → /warehouse/package/status (dropoff confirmed)

6. STATUS AGGREGATION
   ├─ StatusPublisherNode collects from all subsystems
   └─ → /warehouse/robot/status (complete robot state)
        └─ DiagnosticLoggerNode analyzes & logs
           └─ → /warehouse/robot/diagnostics (diagnostic events)
```

### Topic Summary

| Topic | Publisher | Subscriber | Payload |
|-------|-----------|------------|---------|
| `/warehouse/tasks/new` | TaskPublisher | TaskQueueManager | Task(JSON) |
| `/warehouse/tasks/status` | TaskQueueManager | Waypoint, Status | Task(JSON) |
| `/warehouse/navigation/goal` | Waypoint, Charging | PathMonitor | Goal(JSON) |
| `/warehouse/navigation/progress` | PathMonitor | Battery, Status | Progress(JSON) |
| `/warehouse/safety/obstacle` | ObstacleDetector | EmergencyStop | Obstacle(JSON) |
| `/warehouse/safety/emergency_stop` | EmergencyStop | PathMonitor, Status | Alert(JSON) |
| `/warehouse/battery/state` | BatteryPublisher | ChargingController, Status | Battery(JSON) |
| `/warehouse/battery/return_to_charge` | ChargingController | Status | Command(JSON) |
| `/warehouse/package/status` | PackageHandler | Status | Package(JSON) |
| `/warehouse/robot/status` | StatusPublisher | DiagnosticLogger | RobotStatus(JSON) |
| `/warehouse/robot/diagnostics` | DiagnosticLogger | (logged) | Diagnostic(JSON) |

---─ c

## Setup Instructions

### Prerequisites

```bash
# Ubuntu 20.04 with ROS 1 Noetic installed
source /opt/ros/noetic/setup.bash

# Python 3 development tools
sudo apt update
sudo apt install -y python3-pip python3-pytest python3-click
sudo apt install -y ros-noetic-std-msgs ros-noetic-std-srvs
```

### 1. Create catkin Workspace

```bash
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
```

### 2. Clone Repository

```bash
git clone <your-github-repo-url> smart_warehouse_robot
cd ~/catkin_ws
```

### 3. Build Project

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

**Expected output:**
```
[100%] Built target smart_warehouse_robot
```

### 4. Verify Installation

```bash
# Check Python package
python3 -c "from smart_warehouse_robot.common import models; print('✓ Package imported')"

# Check nodes are available (run from the catkin workspace root)
# Preferred: workspace-relative path so this works from any shell
ls src/smart_warehouse_robot/scripts/*_node.py | wc -l  # Should show 11 nodes

# Alternative (absolute) if you followed the guide and used ~/catkin_ws
ls ~/catkin_ws/src/smart_warehouse_robot/scripts/*_node.py | wc -l  # Should show 11 nodes
```

---

## Running the Project

### Option A: Full Automated Demo (Recommended)

**Terminal 1: Start ROS master**
```bash
roscore
```

**Terminal 2: Launch all nodes**
```bash
cd ~/catkin_ws
source devel/setup.bash
roslaunch smart_warehouse_robot warehouse_demo.launch
```

**Expected output:**
```
[ INFO] [1234567890.123456]: Task publisher publishing sample task...
[ INFO] [1234567890.234567]: Task queue manager started
[ INFO] [1234567890.345678]: Status publisher initialized
...
```

**Terminal 3: Monitor topics (optional)**
```bash
source ~/catkin_ws/devel/setup.bash
rostopic list  # View all topics
rostopic echo /warehouse/robot/status  # Watch aggregated status
```

### Option B: Individual Node Testing

**Terminal 1: Start ROS master**
```bash
roscore
```

**Terminal 2: Run specific nodes**
```bash
source ~/catkin_ws/devel/setup.bash

# Task system
rosrun smart_warehouse_robot task_publisher_node.py

# In another terminal:
rosrun smart_warehouse_robot task_queue_manager_node.py

# In another terminal:
rosrun smart_warehouse_robot waypoint_goal_publisher_node.py
```

### Option C: CLI Interface

```bash
source ~/catkin_ws/devel/setup.bash

# View CLI help
rosrun smart_warehouse_robot smart_warehouse_cli.py --help

# Run overview
rosrun smart_warehouse_robot smart_warehouse_cli.py overview

# Create sample task
rosrun smart_warehouse_robot smart_warehouse_cli.py create-task \
  --type pickup \
  --source receiving \
  --destination storage_a \
  --priority 3

# Run scenario
rosrun smart_warehouse_robot smart_warehouse_cli.py scenario happy-path

# View member contributions
rosrun smart_warehouse_robot smart_warehouse_cli.py member-summary
```

---

## 3D Visualization with RViz and URDF

### Quick Start with RViz (Recommended)

RViz is lightweight and works reliably. It shows the robot model, TF tree, and sensor frames.

**Terminal 1: Start ROS master**
```bash
roscore
```

**Terminal 2: Launch simulation logic**
```bash
cd ~/catkin_ws
source devel/setup.bash
roslaunch smart_warehouse_robot warehouse_demo.launch
```

**Terminal 3: Launch RViz with robot visualization**
```bash
cd ~/catkin_ws
source devel/setup.bash
roslaunch smart_warehouse_robot rviz_with_gui.launch
# This starts a helper launch that:
#  - loads `robot_description` into /robot_description
#  - starts `robot_state_publisher`
#  - publishes a static map->base_link TF
#  - launches RViz with a preconfigured view showing RobotModel + TF
```

In RViz:
1. Set **Fixed Frame** to `map` (under Global Options)
2. Click **Add** → **RobotModel** → set Param Name to `robot_description`
3. Click **Add** → **TF** to see frame tree
4. You should see the robot model at origin with wheels and sensor mast

### Advanced: Gazebo 3D Physics Simulation

Gazebo provides full physics simulation with collisions. If you want to use it:

**Step 1: Fix held packages (if needed)**
```bash
# If you get "held broken packages" errors:
sudo apt install -y policykit-1
sudo apt --fix-broken install
sudo apt install -y gazebo9 ros-noetic-gazebo-dev ros-noetic-gazebo-plugins
```

**Step 2: Install Gazebo**
```bash
sudo apt update
sudo apt install -y gazebo9 ros-noetic-gazebo-dev ros-noetic-gazebo-plugins
```

**Step 3: Launch with Gazebo** (once installed)
```bash
# Terminal 1: Gazebo
roslaunch smart_warehouse_robot gazebo_warehouse.launch

# Terminal 2: Simulation logic
roslaunch smart_warehouse_robot warehouse_demo.launch
```

### Choosing Between RViz and Gazebo

| Feature | RViz | Gazebo |
|---------|------|--------|
| **Setup** | Easy, works immediately | Requires Gazebo install |
| **Physics** | TF visualization only | Full ODE physics |
| **Visualization** | Robot model + frames | Warehouse world + zones |
| **Performance** | Very fast | More CPU/GPU |
| **Best for** | Debugging, monitoring | Full simulation |

**Start with RViz.** If you want full physics simulation later, use Gazebo.

### Gazebo Features

- **Warehouse Zones** (color-coded):
  - Receiving (blue): 2, 2
  - Storage A (green): -2, 2
  - Storage B (green): -2, -2
  - Packing (yellow): 2, -2
  - Charging Station (red): 0, -4.5

- **Physics**: ODE engine with collisions, gravity, and realistic robot dynamics
- **Robot Model**: Mobile base with:
  - Differential drive base (0.5m × 0.5m)
  - Two powered wheels + caster wheel
  - Sensor mast with LIDAR frame
  - Collision geometry for obstacle detection

- **Walls**: Boundary walls at perimeter for collision testing

### Gazebo Controls

**In the Gazebo window:**
- **Pan**: Right-click + drag
- **Zoom**: Scroll wheel
- **Rotate view**: Middle-click + drag
- **Select object**: Left-click

**Play/Pause simulation:** Click play/pause buttons in toolbar

### Monitor Simulation Data

```bash
# View all published topics
rostopic list

# Watch robot position/odometry (if nav stack available)
rostopic echo /odom

# View robot status
rostopic echo /warehouse/robot/status

# Record bag during simulation
rosbag record -O bags/gazebo_demo.bag /warehouse/tasks/new /warehouse/robot/status

# Replay recorded bag
rosbag play bags/gazebo_demo.bag
```

### TF (Transform) Visualization

To see the robot's frame tree in RViz:

```bash
# In the Gazebo window, open RViz (Tools → RViz in older versions)
# Or launch RViz separately:
rosrun rviz rviz

# In RViz:
# 1. Set Fixed Frame to "map"
# 2. Add TF display (Add → TF)
# 3. You should see: map → base_link → wheels, sensor_mast, lidar_link
```

### Troubleshooting Gazebo

**Problem:** `Error [gazebo_ros]: The specified model path is invalid`
```bash
# Solution: Ensure paths exist and are readable
ls -la src/smart_warehouse_robot/urdf/
ls -la src/smart_warehouse_robot/worlds/

# Rebuild if needed
cd ~/catkin_ws && catkin_make
```

**Problem:** Gazebo window is black or takes forever to startup
```bash
# Solution: First launch can be slow; be patient
# On slower machines, reduce GUI rendering:
roslaunch smart_warehouse_robot gazebo_warehouse.launch gui:=false

# Use headless mode and view in RViz:
roslaunch smart_warehouse_robot gazebo_warehouse.launch gui:=false paused:=false
# Then in another terminal, launch RViz to visualize
```

**Problem:** Robot doesn't spawn in Gazebo
```bash
# Solution: Check spawn_model output for errors
# Ensure URDF is valid:
check_urdf src/smart_warehouse_robot/urdf/warehouse_robot.urdf

# Manually test spawn:
rosrun gazebo_ros spawn_model -urdf -file src/smart_warehouse_robot/urdf/warehouse_robot.urdf -model test_robot
```

**Problem:** Simulation runs but robot doesn't move
```bash
# Solution: Check that warehouse_demo.launch is running
rosnode list  # Should see task_publisher, path_monitor, etc.

# Also check that navigation messages are being published:
rostopic echo /warehouse/navigation/goal -n 1
```

---

## Testing & Validation

### Run All Tests

```bash
cd ~/catkin_ws
source devel/setup.bash
python3 -m pytest  # Runs all tests with Python 3
```

### Run Specific Test Suites

```bash
# Scenario tests (use python3 -m pytest to ensure Python 3)
python3 -m pytest tests/test_full_happy_path_scenario.py -v
python3 -m pytest tests/test_full_emergency_stop_scenario.py -v
python3 -m pytest tests/test_full_low_battery_scenario.py -v

# Service logic tests
python3 -m pytest tests/test_battery_service.py -v
python3 -m pytest tests/test_task_queue_manager_logic.py -v

# Validation tests
python3 -m pytest tests/test_ros1_compatibility.py -v
python3 -m pytest tests/test_project_structure_validation.py -v
```

### Syntax Validation

```bash
python3 -m compileall src scripts tests
```

---

## ROS Bag Recording

### Record Demo Bag

**Terminal 1: Start ROS master**
```bash
roscore
```

**Terminal 2: Launch all nodes**
```bash
source ~/catkin_ws/devel/setup.bash
roslaunch smart_warehouse_robot warehouse_demo.launch
```

**Terminal 3: Record topics**
```bash
mkdir -p ~/catkin_ws/bags
source ~/catkin_ws/devel/setup.bash

rosbag record -O ~/catkin_ws/bags/final_demo.bag \
  /warehouse/tasks/new \
  /warehouse/tasks/status \
  /warehouse/navigation/goal \
  /warehouse/navigation/progress \
  /warehouse/safety/obstacle \
  /warehouse/safety/emergency_stop \
  /warehouse/battery/state \
  /warehouse/battery/return_to_charge \
  /warehouse/package/status \
  /warehouse/robot/status \
  /warehouse/robot/diagnostics
```

Press `Ctrl+C` to stop recording after ~1-2 minutes.

### Or Use Helper Script

```bash
bash scripts/record_demo_bag.sh
```

### Check Bag Info

```bash
rosbag info bags/final_demo.bag
bash scripts/check_demo_bag.sh
```

### Replay Bag

```bash
rosbag play bags/final_demo.bag
bash scripts/replay_demo_bag.sh
```

---

## Troubleshooting

### Build Failures

**Problem:** `catkin_make` fails silently
```bash
# Solutions:
cd ~/catkin_ws
rm -rf build devel
catkin_make -DCMAKE_BUILD_TYPE=Release
catkin_make --make-jobs 1  # Single threaded
```

**Problem:** `CMake Error: Could not find ROS`
```bash
# Solution: Source ROS before building
source /opt/ros/noetic/setup.bash
cd ~/catkin_ws && catkin_make
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'smart_warehouse_robot'`
```bash
# Solution: Source catkin workspace
source ~/catkin_ws/devel/setup.bash

# Verify package is in PYTHONPATH
python3 -c "import sys; print('\\n'.join(sys.path))"
```

**Problem:** `Cannot import click or pytest`
```bash
# Solution: Install Python dependencies
pip install click pytest rosbag
# Or use system packages:
sudo apt install python3-click python3-pytest
```

### ROS Runtime Errors

**Problem:** `roslaunch` can't find `warehouse_demo.launch`
```bash
# Solution: Source workspace
source ~/catkin_ws/devel/setup.bash
roslaunch smart_warehouse_robot warehouse_demo.launch
```

**Problem:** Nodes crash immediately with `rospy` errors
```bash
# Solution: Start roscore first
roscore  # In separate terminal

# Wait 1-2 seconds, then launch nodes
roslaunch smart_warehouse_robot warehouse_demo.launch
```

**Problem:** No messages on topics
```bash
# Check nodes are running:
rosnode list
rosnode info /task_publisher  # View node info

# Check topic subscriptions:
rostopic info /warehouse/tasks/new

# Echo raw messages:
rostopic echo /warehouse/tasks/new -n 5
```

### Package Service Issues

**Problem:** `rosservice call /warehouse/package/pickup` fails
```bash
# Check service exists:
rosservice list | grep package

# Test service manually:
rosservice call /warehouse/package/pickup '{}'

# View service definition:
rossrv info std_srvs/Trigger
```

### Test Failures

**Problem:** `pytest` tests fail
```bash
# Run with verbose output (ensure Python 3):
python3 -m pytest -v --tb=short

# Run single test file:
python3 -m pytest tests/test_models.py -v

# Run with coverage:
pip install pytest-cov
python3 -m pytest --cov=src --cov-report=term-missing
```

### Performance Issues

**Problem:** Nodes publishing very frequently
```bash
# Check parameter values in launch file:
# Reduce publish_interval_seconds in warehouse_demo.launch
# Or adjust navigation_update_seconds

# Monitor CPU:
top
ps aux | grep python
```

---

## Quick Reference Commands

```bash
# Build and setup
cd ~/catkin_ws && catkin_make && source devel/setup.bash

# ROS Core
roscore

# Launch demo
roslaunch smart_warehouse_robot warehouse_demo.launch

# Monitor topics
rostopic list
rostopic echo /warehouse/robot/status

# Call services
rosservice call /warehouse/package/pickup '{}'
rosservice call /warehouse/package/dropoff '{}'

# Run CLI
rosrun smart_warehouse_robot smart_warehouse_cli.py overview

# Test
python3 -m pytest -v

# Record bag
rosbag record -O bags/demo.bag /warehouse/tasks/new /warehouse/robot/status

# Replay bag
rosbag play bags/demo.bag

# Clean build
cd ~/catkin_ws && rm -rf build devel && catkin_make
```

---

## Environment Setup (Add to `.bashrc`)

```bash
# Add to ~/.bashrc for convenience
export ROS_MASTER_URI=http://localhost:11311
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
alias cw='cd ~/catkin_ws'
alias smart_launch='roslaunch smart_warehouse_robot warehouse_demo.launch'
alias smart_test='cd ~/catkin_ws && pytest'
alias smart_bag_record='bash ~/catkin_ws/scripts/record_demo_bag.sh'
alias smart_bag_replay='rosbag play ~/catkin_ws/bags/final_demo.bag'
```

Then reload:
```bash
source ~/.bashrc
```

---

## Next Steps

1. **Explore Source Code**: Review `src/smart_warehouse_robot/` structure
2. **Run Demo**: Follow "Running the Project" section
3. **Read Services**: Study `services/` modules for logic
4. **Run Tests**: Execute `pytest` to validate
5. **Try CLI**: Use `smart_warehouse_cli.py` to understand features
6. **Record Bag**: Capture topics for demonstration
7. **Review Docs**: Check `docs/` folder for detailed design

