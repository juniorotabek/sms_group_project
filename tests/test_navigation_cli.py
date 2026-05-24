import json

from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_create_nav_goal_works():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["create-nav-goal", "--source", "receiving", "--destination", "packing", "--priority", "3"],
    )

    assert result.exit_code == 0
    assert "Goal " in result.output
    assert '"destination_zone": "packing"' in result.output


def test_create_nav_goal_json_output_returns_valid_json():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "create-nav-goal",
            "--source",
            "receiving",
            "--destination",
            "packing",
            "--priority",
            "3",
            "--json-output",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["destination_zone"] == "packing"


def test_nav_demo_works():
    runner = CliRunner()
    result = runner.invoke(main, ["nav-demo"])

    assert result.exit_code == 0
    assert "Progress " in result.output
    assert "arrived" in result.output


def test_zone_distance_works():
    runner = CliRunner()
    result = runner.invoke(main, ["zone-distance", "--source", "receiving", "--destination", "shipping"])

    assert result.exit_code == 0
    assert "Distance from receiving to shipping:" in result.output


def test_validate_nav_goal_works_for_valid_json():
    runner = CliRunner()
    goal_json = (
        '{"goal_id":"GOAL-001","task_id":"TASK-001","source_zone":"receiving",'
        '"destination_zone":"shipping","priority":3,"status":"idle"}'
    )
    result = runner.invoke(main, ["validate-nav-goal", "--goal-json", goal_json])

    assert result.exit_code == 0
    assert "Valid navigation goal" in result.output


def test_validate_nav_goal_fails_cleanly_for_invalid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["validate-nav-goal", "--goal-json", "{bad json}"])

    assert result.exit_code != 0
    assert "Invalid navigation goal JSON" in result.output
