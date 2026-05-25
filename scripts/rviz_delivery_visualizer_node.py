#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from smart_warehouse_robot.nodes.rviz_delivery_visualizer import main


if __name__ == "__main__":
    main()
