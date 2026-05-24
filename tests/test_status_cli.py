import json

from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_robot_status_sample_works():
    runner = CliRunner()
    result = runner.invoke(main, ["robot-status-sample", "--battery-percentage", "80", "--zone", "receiving"])
    assert result.exit_code == 0
    assert "RobotStatus warehouse_bot_01" in result.output


def test_robot_status_sample_json_output_returns_valid_json():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["robot-status-sample", "--battery-percentage", "80", "--zone", "receiving", "--json-output"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["health_level"] == "ok"


def test_diagnostic_sample_works():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["diagnostic-sample", "--source", "battery", "--level", "warning", "--message", "Battery below threshold"],
    )
    assert result.exit_code == 0
    assert "Diagnostic " in result.output


def test_diagnostic_sample_json_output_returns_valid_json():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "diagnostic-sample",
            "--source",
            "battery",
            "--level",
            "warning",
            "--message",
            "Battery below threshold",
            "--json-output",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["source"] == "battery"


def test_status_demo_works():
    runner = CliRunner()
    result = runner.invoke(main, ["status-demo"])
    assert result.exit_code == 0
    assert "RobotStatus warehouse_bot_01" in result.output


def test_diagnostics_demo_works():
    runner = CliRunner()
    result = runner.invoke(main, ["diagnostics-demo"])
    assert result.exit_code == 0
    assert "Diagnostic " in result.output


def test_validate_status_works_for_valid_json():
    runner = CliRunner()
    status_json = (
        '{"robot_name":"warehouse_bot_01","health_level":"ok","mode":"idle",'
        '"current_zone":"receiving","battery_percentage":80}'
    )
    result = runner.invoke(main, ["validate-status", "--status-json", status_json])
    assert result.exit_code == 0
    assert "Valid robot status" in result.output


def test_validate_status_fails_cleanly_for_invalid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["validate-status", "--status-json", "{bad json}"])
    assert result.exit_code != 0
    assert "Invalid robot status JSON" in result.output


def test_validate_diagnostic_works_for_valid_json():
    runner = CliRunner()
    diagnostic_json = (
        '{"diagnostic_id":"DIAG-001","source":"battery","health_level":"warning",'
        '"message":"Battery below threshold"}'
    )
    result = runner.invoke(main, ["validate-diagnostic", "--diagnostic-json", diagnostic_json])
    assert result.exit_code == 0
    assert "Valid diagnostic event" in result.output


def test_validate_diagnostic_fails_cleanly_for_invalid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["validate-diagnostic", "--diagnostic-json", "{bad json}"])
    assert result.exit_code != 0
    assert "Invalid diagnostic JSON" in result.output


def test_status_ros_commands_works():
    runner = CliRunner()
    result = runner.invoke(main, ["status-ros-commands"])
    assert result.exit_code == 0
    assert "/warehouse/robot/diagnostics" in result.output
