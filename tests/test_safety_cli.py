import json

from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_obstacle_sample_works():
    runner = CliRunner()
    result = runner.invoke(main, ["obstacle-sample", "--zone", "storage_a", "--distance", "0.8", "--detected"])

    assert result.exit_code == 0
    assert "Obstacle " in result.output


def test_obstacle_sample_json_output_returns_valid_json():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["obstacle-sample", "--zone", "storage_a", "--distance", "0.8", "--detected", "--json-output"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["severity"] == "high"


def test_emergency_stop_sample_works():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["emergency-stop-sample", "--zone", "storage_a", "--distance", "0.25", "--reason", "Critical obstacle detected"],
    )

    assert result.exit_code == 0
    assert "EmergencyStop " in result.output


def test_safety_demo_works():
    runner = CliRunner()
    result = runner.invoke(main, ["safety-demo"])

    assert result.exit_code == 0
    assert "Safety state:" in result.output or "EMERGENCY:" in result.output


def test_classify_obstacle_works():
    runner = CliRunner()
    result = runner.invoke(main, ["classify-obstacle", "--distance", "0.8", "--detected"])

    assert result.exit_code == 0
    assert "Severity: high" in result.output


def test_validate_obstacle_works_for_valid_json():
    runner = CliRunner()
    obstacle_json = (
        '{"reading_id":"OBS-001","zone":"storage_a","distance_meters":0.8,'
        '"severity":"high","obstacle_detected":true,"description":"Box detected"}'
    )
    result = runner.invoke(main, ["validate-obstacle", "--obstacle-json", obstacle_json])

    assert result.exit_code == 0
    assert "Valid obstacle reading" in result.output


def test_validate_obstacle_fails_cleanly_for_invalid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["validate-obstacle", "--obstacle-json", "{bad json}"])

    assert result.exit_code != 0
    assert "Invalid obstacle JSON" in result.output
