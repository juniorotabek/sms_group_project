from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_validate_all_samples_works():
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "all-samples"])
    assert result.exit_code == 0
    assert "Validated" in result.output


def test_validate_project_structure_works():
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "project-structure"])
    assert result.exit_code == 0
    assert "All required project files are present." in result.output


def test_validate_no_ros2_works():
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "no-ros2"])
    assert result.exit_code == 0
    assert "No forbidden ROS 2 terms found" in result.output
