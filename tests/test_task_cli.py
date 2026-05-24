import json

from click.testing import CliRunner

from smart_warehouse_robot.cli import main


def test_create_task_works():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["create-task", "--type", "pickup", "--source", "receiving", "--destination", "storage_a", "--priority", "3"],
    )

    assert result.exit_code == 0
    assert "Task " in result.output
    assert '"task_type": "pickup"' in result.output


def test_create_task_json_output_returns_valid_json():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "create-task",
            "--type",
            "pickup",
            "--source",
            "receiving",
            "--destination",
            "storage_a",
            "--priority",
            "3",
            "--json-output",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["task_type"] == "pickup"


def test_sample_tasks_works():
    runner = CliRunner()
    result = runner.invoke(main, ["sample-tasks"])

    assert result.exit_code == 0
    assert "pickup" in result.output
    assert "dropoff" in result.output


def test_queue_demo_works():
    runner = CliRunner()
    result = runner.invoke(main, ["queue-demo"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total_tasks"] == 3


def test_validate_task_works_for_valid_json():
    runner = CliRunner()
    task_json = (
        '{"task_id":"TASK-001","task_type":"pickup","source_zone":"receiving",'
        '"destination_zone":"storage_a","priority":3,"status":"created"}'
    )
    result = runner.invoke(main, ["validate-task", "--task-json", task_json])

    assert result.exit_code == 0
    assert "Valid task" in result.output


def test_validate_task_fails_cleanly_for_invalid_json():
    runner = CliRunner()
    result = runner.invoke(main, ["validate-task", "--task-json", "{bad json}"])

    assert result.exit_code != 0
    assert "Invalid task JSON" in result.output
