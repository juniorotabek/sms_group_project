import json

import pytest

from smart_warehouse_robot.common.helpers import build_battery_state
from smart_warehouse_robot.nodes.battery_publisher import battery_state_to_ros_message, safe_parse_navigation_progress_for_battery


def test_battery_state_to_ros_message_produces_json_string():
    state = build_battery_state("warehouse_bot_01", 50, "storage_a")
    message = battery_state_to_ros_message(state)
    payload = json.loads(message.data)
    assert payload["battery_id"] == state.battery_id
    assert payload["percentage"] == state.percentage


def test_safe_parse_navigation_progress_for_battery_parses_valid_json():
    payload = safe_parse_navigation_progress_for_battery(
        '{"goal_id":"GOAL-001","current_zone":"charging_station","destination_zone":"charging_station","progress_percent":100,"status":"arrived","message":"done"}'
    )
    assert payload["current_zone"] == "charging_station"


def test_safe_parse_navigation_progress_for_battery_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_navigation_progress_for_battery("{bad json}")
