import json

from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_scenario_full_json_json_output_works():
    runner = CliRunner()
    result = runner.invoke(main, ["scenario", "full-json", "--json-output"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "task" in payload
    assert "navigation_goal" in payload
    assert "robot_status" in payload


def test_scenario_happy_path_works():
    runner = CliRunner()
    result = runner.invoke(main, ["scenario", "happy-path"])
    assert result.exit_code == 0
    assert "Task created." in result.output


def test_scenario_emergency_stop_works():
    runner = CliRunner()
    result = runner.invoke(main, ["scenario", "emergency-stop"])
    assert result.exit_code == 0
    assert "Emergency stop command published." in result.output


def test_scenario_low_battery_works():
    runner = CliRunner()
    result = runner.invoke(main, ["scenario", "low-battery"])
    assert result.exit_code == 0
    assert "Return-to-charge command is created." in result.output
