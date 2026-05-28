#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

cd "$WORKSPACE_ROOT"
source devel/setup.bash

if ! pgrep -f rosmaster >/dev/null 2>&1; then
  roscore >/tmp/smart_warehouse_roscore.log 2>&1 &
  sleep 2
fi

roslaunch smart_warehouse_robot warehouse_demo.launch
