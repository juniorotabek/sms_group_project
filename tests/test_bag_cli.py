from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_bag_record_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["bag", "record-command"])
    assert result.exit_code == 0
    assert "rosbag record" in result.output
    assert "/warehouse/tasks/new" in result.output


def test_bag_replay_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["bag", "replay-command"])
    assert result.exit_code == 0
    assert "rosbag play bags/final_demo.bag" in result.output


def test_bag_info_command_works():
    runner = CliRunner()
    result = runner.invoke(main, ["bag", "info-command"])
    assert result.exit_code == 0
    assert "rosbag info bags/final_demo.bag" in result.output
