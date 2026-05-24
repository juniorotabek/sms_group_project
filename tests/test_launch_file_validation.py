from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
LAUNCH_FILE = ROOT / "launch" / "warehouse_demo.launch"


def test_launch_file_structure_is_valid() -> None:
    assert LAUNCH_FILE.exists(), "launch/warehouse_demo.launch is missing."
    tree = ET.parse(LAUNCH_FILE)
    root = tree.getroot()
    assert root.tag == "launch", "Launch file root tag must be <launch>."

    nodes = root.findall("node")
    node_map = {node.attrib.get("type"): node for node in nodes}
    required_nodes = [
        "task_publisher_node.py",
        "task_queue_manager_node.py",
        "waypoint_goal_publisher_node.py",
        "path_progress_monitor_node.py",
        "obstacle_detector_node.py",
        "emergency_stop_node.py",
        "battery_publisher_node.py",
        "charging_controller_node.py",
        "package_handler_node.py",
        "status_publisher_node.py",
        "diagnostic_logger_node.py",
    ]
    missing = [node_name for node_name in required_nodes if node_name not in node_map]
    assert not missing, f"Missing required launch nodes: {missing}"

    for node_name in required_nodes:
        assert node_map[node_name].attrib.get("pkg") == "smart_warehouse_robot", (
            f"Node {node_name} must use pkg='smart_warehouse_robot'."
        )

    def param_names(node_type: str) -> set[str]:
        return {param.attrib.get("name") for param in node_map[node_type].findall("param")}

    assert "robot_name" in param_names("task_queue_manager_node.py")
    assert "publish_interval_seconds" in param_names("task_publisher_node.py")
    assert "low_battery_threshold" in param_names("charging_controller_node.py")
    assert "default_source_zone" in param_names("package_handler_node.py")
    assert "default_destination_zone" in param_names("package_handler_node.py")
    assert "robot_name" in param_names("status_publisher_node.py")
    assert "publish_interval_seconds" in param_names("status_publisher_node.py")
