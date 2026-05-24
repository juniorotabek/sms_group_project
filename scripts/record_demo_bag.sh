#!/usr/bin/env bash
set -e

echo "Preparing to record the final demo bag."

if ! command -v rosbag >/dev/null 2>&1; then
  echo "Error: rosbag is not available in PATH. Source your ROS 1 Noetic environment first."
  exit 1
fi

mkdir -p bags

echo "Recording bags/final_demo.bag with all main project topics."
rosbag record -O bags/final_demo.bag \
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
