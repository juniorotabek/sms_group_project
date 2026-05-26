from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
GAZEBO_LAUNCH_FILE = ROOT / "launch" / "gazebo_warehouse.launch"
URDF_FILE = ROOT / "urdf" / "warehouse_robot.urdf"
WORLD_FILE = ROOT / "worlds" / "warehouse_sim.world"


def test_gazebo_assets_exist() -> None:
    assert GAZEBO_LAUNCH_FILE.exists(), "launch/gazebo_warehouse.launch is missing."
    assert URDF_FILE.exists(), "urdf/warehouse_robot.urdf is missing."
    assert WORLD_FILE.exists(), "worlds/warehouse_sim.world is missing."


def test_robot_model_contains_visual_features() -> None:
    tree = ET.parse(URDF_FILE)
    root = tree.getroot()
    link_names = {link.attrib.get("name") for link in root.findall("link")}
    assert "status_light_link" in link_names, "Robot model should include a visible status light."
    assert "cargo_box_link" in link_names, "Robot model should include a cargo box visual."


def test_robot_model_contains_motion_plugin() -> None:
    tree = ET.parse(URDF_FILE)
    root = tree.getroot()
    plugins = root.findall("plugin")
    assert any(plugin.attrib.get("filename") == "libRandomVelocityPlugin.so" for plugin in plugins), (
        "Robot model should include the built-in random velocity motion plugin."
    )


def test_gazebo_launch_file_structure_is_valid() -> None:
    tree = ET.parse(GAZEBO_LAUNCH_FILE)
    root = tree.getroot()
    assert root.tag == "launch", "Gazebo launch file root tag must be <launch>."

    nodes = root.findall("node")
    assert len(nodes) == 1, "Gazebo launch should expose one visualization node."

    node = nodes[0]
    assert node.attrib.get("pkg") == "smart_warehouse_robot", "Visualization must run from this package."
    assert node.attrib.get("type") == "run_gazebo_visualization.sh", (
        "Visualization launch must call the standalone Gazebo runner."
    )

    envs = root.findall("env")
    assert any(env.attrib.get("name") == "GAZEBO_MODEL_PATH" for env in envs), (
        "Gazebo launch must set GAZEBO_MODEL_PATH for the local model folder."
    )