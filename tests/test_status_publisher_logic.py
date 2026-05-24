import json

import pytest

from smart_warehouse_robot.common.helpers import build_robot_status_snapshot
from smart_warehouse_robot.nodes.status_publisher import robot_status_to_ros_message, safe_parse_json_event


def test_robot_status_to_ros_message_produces_json_string():
    snapshot = build_robot_status_snapshot(
        robot_name="warehouse_bot_01",
        current_zone="receiving",
        mode="idle",
        battery_percentage=80,
    )
    message = robot_status_to_ros_message(snapshot)
    payload = json.loads(message.data)
    assert payload["robot_name"] == "warehouse_bot_01"


def test_safe_parse_json_event_parses_valid_json():
    payload = safe_parse_json_event('{"status":"moving"}', "navigation")
    assert payload["status"] == "moving"


def test_safe_parse_json_event_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_json_event("{bad json}", "battery")
