from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_structure_contains_required_files() -> None:
    required_paths = [
        "CMakeLists.txt",
        "package.xml",
        "setup.py",
        "README.md",
        ".gitignore",
        "launch/warehouse_demo.launch",
        "scripts/smart_warehouse_cli.py",
        "scripts/task_publisher_node.py",
        "scripts/task_queue_manager_node.py",
        "scripts/waypoint_goal_publisher_node.py",
        "scripts/path_progress_monitor_node.py",
        "scripts/obstacle_detector_node.py",
        "scripts/emergency_stop_node.py",
        "scripts/battery_publisher_node.py",
        "scripts/charging_controller_node.py",
        "scripts/package_handler_node.py",
        "scripts/status_publisher_node.py",
        "scripts/diagnostic_logger_node.py",
        "src/smart_warehouse_robot/common/models.py",
        "src/smart_warehouse_robot/common/helpers.py",
        "src/smart_warehouse_robot/common/constants.py",
        "docs/architecture_overview.md",
        "docs/member_functionality_plan.md",
        "docs/rosbag_recording_guide.md",
        "docs/testing_guide.md",
        "bags/.gitkeep",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    assert not missing, f"Missing required project files: {missing}"


def test_no_ros_build_output_folders_are_committed() -> None:
    forbidden_dirs = ["build", "devel", "install", "log"]
    existing = [directory for directory in forbidden_dirs if (ROOT / directory).exists()]
    assert not existing, f"Committed build output folders should not exist: {existing}"
