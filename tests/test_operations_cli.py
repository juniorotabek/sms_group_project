from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_overview_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["overview"])
    assert result.exit_code == 0
    assert "ROS 1 Noetic" in result.output
    assert "Member 7 Advanced CLI + Operations" in result.output


def test_demo_plan_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["demo-plan"])
    assert result.exit_code == 0
    assert "25-minute Demo Plan" in result.output
    assert "rosbag" in result.output.lower()
    assert "pytest" in result.output.lower()


def test_ros_commands_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["ros-commands"])
    assert result.exit_code == 0
    assert "roslaunch smart_warehouse_robot warehouse_demo.launch" in result.output
    assert "rosbag record" in result.output
    assert "ros2" not in result.output.lower()


def test_member_summary_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["member-summary"])
    assert result.exit_code == 0
    for member_label in ["Member 1", "Member 7", "Member 8"]:
        assert member_label in result.output


def test_launch_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["launch-command"])
    assert result.exit_code == 0
    assert "roscore" in result.output
    assert "roslaunch smart_warehouse_robot warehouse_demo.launch" in result.output
