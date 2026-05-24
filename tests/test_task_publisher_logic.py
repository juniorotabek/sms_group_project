import json

from smart_warehouse_robot.nodes.task_publisher import create_sample_tasks, task_to_ros_message


def test_create_sample_tasks_returns_at_least_four_tasks():
    tasks = create_sample_tasks()

    assert len(tasks) >= 4


def test_each_sample_task_has_valid_source_and_destination():
    tasks = create_sample_tasks()

    for task in tasks:
        assert task.source_zone != task.destination_zone
        assert task.source_zone.value
        assert task.destination_zone.value


def test_task_to_ros_message_produces_json_string():
    task = create_sample_tasks()[0]
    message = task_to_ros_message(task)
    payload = json.loads(message.data)

    assert payload["task_id"] == task.task_id
    assert payload["task_type"] == task.task_type.value
