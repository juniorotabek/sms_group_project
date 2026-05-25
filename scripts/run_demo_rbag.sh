#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEMO_LOG="/tmp/smart_warehouse_demo.log"
BAG_DIR="$WORKSPACE_ROOT/bags"
BAG_FILE="$BAG_DIR/demo_$(date +%Y%m%d_%H%M%S).bag"

cleanup() {
  if [[ -n "${DEMO_LAUNCH_PID:-}" ]] && kill -0 "$DEMO_LAUNCH_PID" >/dev/null 2>&1; then
    kill "$DEMO_LAUNCH_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

cd "$WORKSPACE_ROOT"
source devel/setup.bash

if ! command -v rosbag >/dev/null 2>&1; then
  echo "Error: rosbag is not available in PATH. Install rosbag or source the ROS environment first."
  exit 1
fi

mkdir -p "$BAG_DIR"

if ! pgrep -f rosmaster >/dev/null 2>&1; then
  roscore >/tmp/smart_warehouse_roscore.log 2>&1 &
  sleep 2
fi

roslaunch smart_warehouse_robot warehouse_demo.launch >"$DEMO_LOG" 2>&1 &
DEMO_LAUNCH_PID=$!
sleep 5

echo "Recording bag to $BAG_FILE"
rosbag record -O "$BAG_FILE" /warehouse/#
