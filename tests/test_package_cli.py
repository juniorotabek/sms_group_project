import json

from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_package_sample_works():
    runner = CliRunner()
    result = runner.invoke(main, ["package-sample", "--source", "storage_a", "--destination", "shipping"])
    assert result.exit_code == 0
    assert "Package " in result.output


def test_package_sample_json_output_returns_valid_json():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["package-sample", "--source", "storage_a", "--destination", "shipping", "--json-output"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["state"] == "waiting_for_pickup"


def test_package_demo_works():
    runner = CliRunner()
    result = runner.invoke(main, ["package-demo"])
    assert result.exit_code == 0
    assert "PackageEvent " in result.output


def test_package_status_event_works():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["package-status-event", "--event-type", "package_ready", "--source", "storage_a", "--destination", "shipping", "--message", "ready"],
    )
    assert result.exit_code == 0
    assert "PackageEvent " in result.output


def test_validate_package_works_for_valid_json():
    runner = CliRunner()
    package_json = '{"package_id":"PKG-001","source_zone":"storage_a","destination_zone":"shipping","state":"waiting_for_pickup"}'
    result = runner.invoke(main, ["validate-package", "--package-json", package_json])
    assert result.exit_code == 0
    assert "Valid package" in result.output


def test_validate_package_fails_cleanly_for_invalid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["validate-package", "--package-json", "{bad json}"])
    assert result.exit_code != 0
    assert "Invalid package JSON" in result.output


def test_package_ros_commands_works():
    runner = CliRunner()
    result = runner.invoke(main, ["package-ros-commands"])
    assert result.exit_code == 0
    assert "rosservice call /warehouse/package/pickup" in result.output
