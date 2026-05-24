#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from smart_warehouse_robot.nodes.path_progress_monitor import main


if __name__ == "__main__":
    main()
