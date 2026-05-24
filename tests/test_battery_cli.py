import json

from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_battery_sample_works():
    runner = CliRunner()
    result = runner.invoke(main, ["battery-sample", "--percentage", "20", "--zone", "storage_a"])
    assert result.exit_code == 0
    assert "Battery " in result.output


def test_battery_sample_json_output_returns_valid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["battery-sample", "--percentage", "20", "--zone", "storage_a", "--json-output"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["level"] == "low"


def test_charge_command_sample_works():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["charge-command-sample", "--percentage", "20", "--zone", "storage_a", "--reason", "Low battery"],
    )
    assert result.exit_code == 0
    assert "ChargeCommand " in result.output


def test_battery_demo_works():
    runner = CliRunner()
    result = runner.invoke(main, ["battery-demo"])
    assert result.exit_code == 0
    assert "ChargeCommand " in result.output


def test_classify_battery_works():
    runner = CliRunner()
    result = runner.invoke(main, ["classify-battery", "--percentage", "20"])
    assert result.exit_code == 0
    assert "Battery level: low" in result.output


def test_validate_battery_works_for_valid_json():
    runner = CliRunner()
    battery_json = (
        '{"battery_id":"BAT-001","robot_name":"warehouse_bot_01","percentage":20,'
        '"level":"low","charging_status":"not_charging","current_zone":"storage_a"}'
    )
    result = runner.invoke(main, ["validate-battery", "--battery-json", battery_json])
    assert result.exit_code == 0
    assert "Valid battery state" in result.output


def test_validate_battery_fails_cleanly_for_invalid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["validate-battery", "--battery-json", "{bad json}"])
    assert result.exit_code != 0
    assert "Invalid battery JSON" in result.output
