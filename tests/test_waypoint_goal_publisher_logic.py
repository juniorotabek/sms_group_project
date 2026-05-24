import json

import pytest

from smart_warehouse_robot.nodes.waypoint_goal_publisher import (
    extract_task_payload_from_status_event,
    goal_to_ros_message,
    navigation_goal_from_status_event,
)


def test_task_started_event_creates_navigation_goal():
    event_json = json.dumps(
        {
            "event_type": "task_started",
            "task_id": "TASK-001",
            "source_zone": "receiving",
            "destination_zone": "packing",
            "priority": 3,
        }
    )

    goal = navigation_goal_from_status_event(event_json)

    assert goal is not None
    assert goal.task_id == "TASK-001"


def test_non_task_started_event_returns_none():
    event_json = json.dumps({"event_type": "task_queued"})

    assert navigation_goal_from_status_event(event_json) is None


def test_supports_nested_task_event_format():
    event_json = json.dumps(
        {
            "event_type": "task_started",
            "task": {
                "task_id": "TASK-001",
                "source_zone": "receiving",
                "destination_zone": "shipping",
                "priority": 4,
            },
        }
    )

    payload = extract_task_payload_from_status_event(event_json)

    assert payload["task_id"] == "TASK-001"
    assert payload["destination_zone"] == "shipping"


def test_supports_flattened_event_format():
    event_json = json.dumps(
        {
            "event_type": "task_started",
            "task_id": "TASK-002",
            "source_zone": "storage_a",
            "destination_zone": "packing",
            "priority": 2,
        }
    )

    payload = extract_task_payload_from_status_event(event_json)

    assert payload["task_id"] == "TASK-002"


def test_invalid_json_raises_value_error():
    with pytest.raises(ValueError, match="Invalid task status event JSON"):
        extract_task_payload_from_status_event("{bad json}")


def test_goal_to_ros_message_produces_json_string():
    event_json = json.dumps(
        {
            "event_type": "task_started",
            "task_id": "TASK-003",
            "source_zone": "receiving",
            "destination_zone": "packing",
            "priority": 2,
        }
    )

    goal = navigation_goal_from_status_event(event_json)
    message = goal_to_ros_message(goal)
    payload = json.loads(message.data)

    assert payload["task_id"] == "TASK-003"
    assert payload["destination_zone"] == "packing"
