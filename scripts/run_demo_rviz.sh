#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEMO_LOG="/tmp/smart_warehouse_demo.log"
RVIZ_CONFIG="$WORKSPACE_ROOT/src/smart_warehouse_robot/rviz/robot_camera_follow.rviz"

cleanup() {
  if [[ -n "${DEMO_LAUNCH_PID:-}" ]] && kill -0 "$DEMO_LAUNCH_PID" >/dev/null 2>&1; then
    kill "$DEMO_LAUNCH_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

cd "$WORKSPACE_ROOT"
source devel/setup.bash

if ! command -v rviz >/dev/null 2>&1; then
  echo "Error: rviz is not available in PATH. Install rviz or source the ROS environment first."
  exit 1
fi

if [[ ! -f "$RVIZ_CONFIG" ]]; then
  echo "Error: RViz config not found at $RVIZ_CONFIG"
  exit 1
fi

if ! pgrep -f rosmaster >/dev/null 2>&1; then
  roscore >/tmp/smart_warehouse_roscore.log 2>&1 &
  sleep 2
fi

roslaunch smart_warehouse_robot warehouse_demo.launch >"$DEMO_LOG" 2>&1 &
DEMO_LAUNCH_PID=$!
sleep 5

rviz -d "$RVIZ_CONFIG"
