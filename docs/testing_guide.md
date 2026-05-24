# Testing Guide

## Purpose of Pytest in This Project
Pytest is used to validate the pure Python logic behind the Smart Warehouse Mobility Robot project without requiring a running ROS master for default test execution. This keeps most validation fast, repeatable, and suitable for development on non-ROS machines.

## Run All Tests
```bash
pytest
```

## Run Scenario Tests
```bash
pytest tests/test_full_happy_path_scenario.py
pytest tests/test_full_emergency_stop_scenario.py
pytest tests/test_full_low_battery_scenario.py
```

## Run Validation Tests
```bash
pytest tests/test_launch_file_validation.py
pytest tests/test_ros1_compatibility.py
pytest tests/test_project_structure_validation.py
```

## Important Notes
- Default pytest tests do not require `roscore`.
- ROS runtime behavior should still be tested manually on Ubuntu 20.04 with ROS 1 Noetic.
- Use `roslaunch smart_warehouse_robot warehouse_demo.launch` for the manual demo check.

## Manual Runtime Checklist
- package builds with `catkin_make`
- launch file starts
- topics appear with `rostopic list`
- services respond with `rosservice call`
- rosbag records the final demo topics
- pytest passes
