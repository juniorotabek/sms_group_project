#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export GAZEBO_MODEL_PATH="$PACKAGE_ROOT/models${GAZEBO_MODEL_PATH:+:$GAZEBO_MODEL_PATH}"

exec gazebo --verbose "$PACKAGE_ROOT/worlds/warehouse_sim.world"