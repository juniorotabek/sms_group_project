"""JSON assertion helpers for final test validation."""

from __future__ import annotations

import json


def assert_json_round_trip(model_obj, model_class) -> None:
    restored = model_class.from_json(model_obj.to_json())
    assert restored.to_dict() == model_obj.to_dict()


def assert_required_keys(data: dict, keys: list[str]) -> None:
    missing = [key for key in keys if key not in data]
    assert not missing, f"Missing required keys: {missing}"


def assert_valid_json_text(text: str) -> dict:
    payload = json.loads(text)
    assert isinstance(payload, dict), "Expected JSON object payload."
    return payload


def assert_topic_payload_shape(payload: dict, expected_type: str) -> None:
    expected_keys = {
        "task": ["task_id", "task_type", "source_zone", "destination_zone", "priority", "status"],
        "navigation_goal": ["goal_id", "source_zone", "destination_zone", "priority", "status"],
        "navigation_progress": ["goal_id", "current_zone", "destination_zone", "progress_percent", "status", "message"],
        "obstacle": ["reading_id", "zone", "distance_meters", "severity", "obstacle_detected"],
        "emergency_stop": ["command_id", "active", "reason", "safety_state"],
        "battery": ["battery_id", "robot_name", "percentage", "level", "charging_status", "current_zone"],
        "charge_command": ["command_id", "robot_name", "active", "target_zone", "battery_percentage", "charging_status"],
        "package": ["package_id", "source_zone", "destination_zone", "state"],
        "package_event": ["event_id", "event_type", "package_state", "robot_name", "message"],
        "robot_status": ["robot_name", "health_level", "mode", "current_zone"],
        "diagnostic": ["diagnostic_id", "source", "health_level", "message"],
    }
    assert expected_type in expected_keys, f"Unknown expected payload type: {expected_type}"
    assert_required_keys(payload, expected_keys[expected_type])
