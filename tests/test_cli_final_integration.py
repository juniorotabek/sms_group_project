from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_cli_final_integration_commands_exit_zero() -> None:
    runner = CliRunner()
    commands = [
        ["overview"],
        ["demo-plan"],
        ["ros-commands"],
        ["member-summary"],
        ["scenario", "happy-path"],
        ["scenario", "emergency-stop"],
        ["scenario", "low-battery"],
        ["validate", "all-samples"],
        ["validate", "project-structure"],
        ["bag", "record-command"],
        ["bag", "replay-command"],
        ["launch-command"],
    ]
    for command in commands:
        result = runner.invoke(main, command)
        assert result.exit_code == 0, f"Command failed: {' '.join(command)}\n{result.output}"
        assert "ros2" not in result.output.lower(), f"Unexpected ROS 2 text in command: {' '.join(command)}"


def test_ros_commands_and_bag_output_are_correct() -> None:
    runner = CliRunner()
    ros_commands = runner.invoke(main, ["ros-commands"])
    bag_record = runner.invoke(main, ["bag", "record-command"])
    member_summary = runner.invoke(main, ["member-summary"])

    assert ros_commands.exit_code == 0
    assert "roslaunch" in ros_commands.output
    assert "rosbag record" in bag_record.output
    for member_label in [f"Member {index}" for index in range(1, 9)]:
        assert member_label in member_summary.output
