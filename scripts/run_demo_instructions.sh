#!/usr/bin/env bash
set -e

echo "Smart Warehouse Robot Demo Instructions"
echo
echo "Terminal 1:"
echo "roscore"
echo
echo "Terminal 2:"
echo "cd ~/catkin_ws"
echo "source devel/setup.bash"
echo "roslaunch smart_warehouse_robot warehouse_demo.launch"
echo
echo "Terminal 3:"
echo "rostopic list"
echo "rostopic echo /warehouse/robot/status"
echo "rostopic echo /warehouse/robot/diagnostics"
echo
echo "Terminal 4:"
echo "rosservice call /warehouse/package/pickup"
echo "rosservice call /warehouse/package/dropoff"
echo
echo "Terminal 5:"
echo "bash scripts/record_demo_bag.sh"
