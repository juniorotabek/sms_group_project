#!/usr/bin/env bash
set -e

echo "Preparing to inspect the final demo bag."

if ! command -v rosbag >/dev/null 2>&1; then
  echo "Error: rosbag is not available in PATH. Source your ROS 1 Noetic environment first."
  exit 1
fi

if [ ! -f bags/final_demo.bag ]; then
  echo "Error: bags/final_demo.bag does not exist."
  exit 1
fi

echo "Showing rosbag info for bags/final_demo.bag."
rosbag info bags/final_demo.bag
