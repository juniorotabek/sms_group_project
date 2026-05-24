# ROS Bag Recording Guide

## Manual Record Command
```bash
mkdir -p bags
rosbag record -O bags/final_demo.bag /warehouse/tasks/new /warehouse/tasks/status /warehouse/navigation/goal /warehouse/navigation/progress /warehouse/safety/obstacle /warehouse/safety/emergency_stop /warehouse/battery/state /warehouse/battery/return_to_charge /warehouse/package/status /warehouse/robot/status /warehouse/robot/diagnostics
```

## Script Record Command
```bash
bash scripts/record_demo_bag.sh
```

## CLI Bag Helpers
The CLI can print the same bag commands for the demo team:

```bash
rosrun smart_warehouse_robot smart_warehouse_cli.py bag record-command
rosrun smart_warehouse_robot smart_warehouse_cli.py bag replay-command
rosrun smart_warehouse_robot smart_warehouse_cli.py bag info-command
```

## Suggested Demo Workflow
1. Start `roscore`.
2. Launch the full demo with `roslaunch smart_warehouse_robot warehouse_demo.launch`.
3. In another terminal, start `rosbag record`.
4. Show package services during the demo:
   `rosservice call /warehouse/package/pickup`
   `rosservice call /warehouse/package/dropoff`
   `rostopic echo /warehouse/package/status`
5. Let task, navigation, safety, battery, and package events run for the demo.
6. Stop recording with `Ctrl+C`.

## Check the Bag
```bash
rosbag info bags/final_demo.bag
```

Or:
```bash
bash scripts/check_demo_bag.sh
```

## Replay the Bag
```bash
rosbag play bags/final_demo.bag
```

Or:
```bash
bash scripts/replay_demo_bag.sh
```

## Topics Covered
- `/warehouse/tasks/new`
- `/warehouse/tasks/status`
- `/warehouse/navigation/goal`
- `/warehouse/navigation/progress`
- `/warehouse/safety/obstacle`
- `/warehouse/safety/emergency_stop`
- `/warehouse/battery/state`
- `/warehouse/battery/return_to_charge`
- `/warehouse/package/status`
- `/warehouse/robot/status`
- `/warehouse/robot/diagnostics`

## Service Demonstration Note
ROS services are not recorded in the same way as topic streams. For the demo video, show these commands alongside the bagged topic output:

```bash
rosservice call /warehouse/package/pickup
rosservice call /warehouse/package/dropoff
rostopic echo /warehouse/package/status
```

## Final Notes
- The final demo bag should be created on an Ubuntu 20.04 machine with ROS 1 Noetic while the application is running.
- Bag files can be large.
- If GitHub rejects large files, submit the bag separately through E-class if your instructor allows it.
