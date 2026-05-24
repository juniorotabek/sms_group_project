# Member Functionality Plan

This project is being implemented as a ROS 1 Noetic package. Parts 1 to 9 are implemented.

## Member 1: Task Management

Implemented ROS Function 1:
TaskPublisherNode using `rospy`
- publishes new warehouse tasks
- topic: `/warehouse/tasks/new`
- message: `std_msgs/String` JSON

Implemented ROS Function 2:
TaskQueueManagerNode using `rospy`
- subscribes to new tasks
- manages queue
- starts/completes tasks
- publishes task status
- topic: `/warehouse/tasks/status`

Additional contribution:
- CLI commands for task creation, validation, sample task preview, and queue demo
- pytest coverage for task models, queue logic, publisher logic, and queue manager logic

## Member 2: Navigation

Implemented ROS Function 1:
WaypointGoalPublisherNode using `rospy`
- subscribes to task status events
- creates navigation goals
- publishes to `/warehouse/navigation/goal`

Implemented ROS Function 2:
PathProgressMonitorNode using `rospy`
- subscribes to navigation goals
- simulates movement progress
- publishes to `/warehouse/navigation/progress`

Additional contribution:
- CLI commands for navigation-goal creation, navigation demo, goal validation, and zone-distance checks
- pytest coverage for navigation models, simulator logic, waypoint-goal conversion, and progress publishing

## Member 3: Obstacle Safety

Implemented ROS Function 1:
ObstacleDetectorNode using `rospy`
- simulates obstacle readings
- publishes to `/warehouse/safety/obstacle`

Implemented ROS Function 2:
EmergencyStopNode using `rospy`
- subscribes to obstacle readings
- decides whether emergency stop is required
- publishes to `/warehouse/safety/emergency_stop`

Additional contribution:
- CLI commands for obstacle sampling, emergency-stop sampling, obstacle classification, validation, and safety demo
- pytest coverage for safety models, safety monitor logic, obstacle simulation, and emergency-stop conversion

## Member 4: Battery System

Implemented ROS Function 1:
BatteryPublisherNode
- uses `rospy`
- simulates robot battery state
- publishes BatteryState JSON to `/warehouse/battery/state`

Implemented ROS Function 2:
ChargingControllerNode
- uses `rospy`
- subscribes to `/warehouse/battery/state`
- detects low battery
- publishes ChargeCommand JSON to `/warehouse/battery/return_to_charge`
- publishes NavigationGoal JSON to `/warehouse/navigation/goal` so the robot returns to `charging_station`

Additional contribution:
- CLI commands for battery sampling, charge-command sampling, battery classification, validation, and battery demo
- pytest coverage for battery models, battery simulator logic, battery publisher helpers, and charging controller helpers

## Member 5: Package Handling

Implemented ROS Function 1:
Package pickup service
- uses `rospy`
- provides `/warehouse/package/pickup`
- service type: `std_srvs/Trigger`
- marks package as `CARRYING`
- publishes `PackageStatusEvent` JSON to `/warehouse/package/status`

Implemented ROS Function 2:
Package dropoff service
- uses `rospy`
- provides `/warehouse/package/dropoff`
- service type: `std_srvs/Trigger`
- marks package as `DELIVERED`
- publishes `PackageStatusEvent` JSON to `/warehouse/package/status`

Additional contribution:
- Optional reset service at `/warehouse/package/reset`
- CLI commands for package sampling, package event generation, package validation, demo flow, and ROS service command hints
- pytest coverage for package models, package handler service logic, node helper parsing, and CLI behavior

## Member 6: Robot Status + Diagnostics

Implemented ROS Function 1:
StatusPublisherNode
- uses `rospy`
- subscribes to task, navigation, safety, battery, and package topics
- aggregates robot state
- publishes `RobotStatusSnapshot` JSON to `/warehouse/robot/status`

Implemented ROS Function 2:
DiagnosticLoggerNode
- uses `rospy`
- subscribes to `/warehouse/robot/status`
- creates diagnostic events
- publishes `DiagnosticEvent` JSON to `/warehouse/robot/diagnostics`

Additional contribution:
- CLI commands for robot status samples, diagnostic samples, status demo, diagnostics demo, validation, and ROS monitoring commands
- pytest coverage for status models, aggregation logic, publisher helpers, diagnostic helpers, and CLI behavior
- improves the demo by giving a single operator-facing health stream plus a separate diagnostics stream for individual evaluation

## Member 7: Advanced CLI + Operations

Implemented ROS Function / Contribution 1:
Advanced Click CLI task and robot operation commands
- create task JSON
- navigation demo
- safety demo
- battery demo
- package demo
- robot status demo
- scenario generation

Implemented ROS Function / Contribution 2:
CLI simulation/control/rosbag/demo helpers
- overview command
- demo-plan command
- ros-commands command
- bag command group
- validate command group
- member-summary command

Additional contribution:
- Click is a mandatory assignment requirement and this layer satisfies that requirement in a visible way
- the operations commands make the project easier to demonstrate, verify, and evaluate during the 25-minute presentation and demo video

## Member 8: Testing + ROS Bag + Launch Validation

Implemented ROS/Project Function 1:
Pytest scenario validation
- validates happy path
- validates emergency stop
- validates low battery behavior
- validates package delivery
- validates robot status and diagnostics

Implemented ROS/Project Function 2:
ROS bag recording and launch validation
- validates launch file structure
- provides rosbag recording scripts
- provides replay and check scripts
- documents the final demo bag process

Additional contribution:
- final validation tests for project structure and ROS 1 compatibility
- supports the mandatory pytest and bag-recording assignment requirements
