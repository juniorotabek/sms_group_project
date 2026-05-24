import json

import pytest

from smart_warehouse_robot.common.helpers import build_diagnostic_event, build_robot_status_snapshot
from smart_warehouse_robot.nodes.diagnostic_logger import (
    create_diagnostic_summary_event,
    diagnostic_event_to_ros_message,
    safe_parse_robot_status,
)


def test_safe_parse_robot_status_parses_valid_json():
    snapshot = build_robot_status_snapshot(
        robot_name="warehouse_bot_01",
        current_zone="receiving",
        mode="idle",
        battery_percentage=80,
    )
    restored = safe_parse_robot_status(snapshot.to_json())
    assert restored.robot_name == "warehouse_bot_01"


def test_safe_parse_robot_status_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_robot_status("{bad json}")


def test_diagnostic_event_to_ros_message_produces_json_string():
    event = build_diagnostic_event(
        source="battery",
        health_level="warning",
        message="Battery below threshold",
    )
    message = diagnostic_event_to_ros_message(event)
    payload = json.loads(message.data)
    assert payload["message"] == "Battery below threshold"


def test_create_diagnostic_summary_event_returns_expected_keys():
    summary_json = create_diagnostic_summary_event(
        {
            "robot_name": "warehouse_bot_01",
            "total_events": 2,
            "latest_level": "warning",
            "latest_message": "Battery below threshold",
        }
    )
    payload = json.loads(summary_json)
    assert payload["total_events"] == 2
    assert payload["latest_level"] == "warning"
