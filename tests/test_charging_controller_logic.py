import json

import pytest

from smart_warehouse_robot.common.helpers import build_battery_state, build_charge_command, build_charge_navigation_goal
from smart_warehouse_robot.nodes.charging_controller import (
    charge_command_to_ros_message,
    charge_navigation_goal_to_ros_message,
    create_battery_alert_event,
    safe_parse_battery_state,
)


def test_safe_parse_battery_state_parses_valid_json():
    state = build_battery_state("warehouse_bot_01", 20, "storage_a")
    parsed = safe_parse_battery_state(state.to_json())
    assert parsed.battery_id == state.battery_id


def test_safe_parse_battery_state_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_battery_state("{bad json}")


def test_charge_command_to_ros_message_produces_json_string():
    state = build_battery_state("warehouse_bot_01", 20, "storage_a")
    command = build_charge_command(state)
    message = charge_command_to_ros_message(command)
    payload = json.loads(message.data)
    assert payload["command_id"] == command.command_id


def test_charge_navigation_goal_to_ros_message_produces_json_string():
    state = build_battery_state("warehouse_bot_01", 20, "storage_a")
    command = build_charge_command(state)
    goal = build_charge_navigation_goal(command)
    message = charge_navigation_goal_to_ros_message(goal)
    payload = json.loads(message.data)
    assert payload["goal_id"] == goal.goal_id


def test_create_battery_alert_event_returns_json_with_expected_keys():
    state = build_battery_state("warehouse_bot_01", 20, "storage_a")
    command = build_charge_command(state)
    payload = json.loads(create_battery_alert_event(state, command))
    assert payload["event_type"] == "battery_alert"
    assert payload["battery_id"] == state.battery_id
    assert "timestamp" in payload
