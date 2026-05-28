#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEMO_LOG="/tmp/smart_warehouse_demo.log"

cleanup() {
  if [[ -n "${DEMO_LAUNCH_PID:-}" ]] && kill -0 "$DEMO_LAUNCH_PID" >/dev/null 2>&1; then
    kill "$DEMO_LAUNCH_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

cd "$WORKSPACE_ROOT"
source devel/setup.bash

if ! pgrep -f rosmaster >/dev/null 2>&1; then
  roscore >/tmp/smart_warehouse_roscore.log 2>&1 &
  sleep 2
fi

roslaunch smart_warehouse_robot demo_with_rviz_delivery.launch >"$DEMO_LOG" 2>&1 &
DEMO_LAUNCH_PID=$!
wait "$DEMO_LAUNCH_PID"
