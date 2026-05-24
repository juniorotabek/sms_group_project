import json

import pytest

from smart_warehouse_robot.common.helpers import build_obstacle_reading
from smart_warehouse_robot.nodes.emergency_stop import (
    create_safety_summary_event,
    emergency_command_to_ros_message,
    safe_parse_obstacle_message,
)


def test_safe_parse_obstacle_message_parses_valid_json():
    reading = build_obstacle_reading("storage_a", 0.8, True)
    parsed = safe_parse_obstacle_message(reading.to_json())

    assert parsed.reading_id == reading.reading_id


def test_safe_parse_obstacle_message_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_obstacle_message("{not valid json}")


def test_emergency_command_to_ros_message_produces_json_string():
    reading = build_obstacle_reading("storage_a", 0.25, True)
    from smart_warehouse_robot.common.helpers import build_emergency_stop_command

    command = build_emergency_stop_command(reading)
    message = emergency_command_to_ros_message(command)
    payload = json.loads(message.data)

    assert payload["command_id"] == command.command_id
    assert payload["active"] == command.active


def test_create_safety_summary_event_returns_expected_keys():
    payload = json.loads(
        create_safety_summary_event(
            {
                "safety_state": "warning",
                "emergency_active": False,
                "latest_reading_id": "OBS-001",
                "latest_severity": "medium",
                "latest_zone": "storage_a",
            }
        )
    )

    assert payload["event_type"] == "safety_summary"
    assert payload["safety_state"] == "warning"
    assert "timestamp" in payload
