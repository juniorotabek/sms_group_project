import json

import pytest

from smart_warehouse_robot.nodes.package_handler import (
    create_package_from_task_event,
    package_event_to_ros_message,
    safe_parse_navigation_progress_for_package,
    safe_parse_task_status_for_package,
)
from smart_warehouse_robot.common.helpers import build_package_status_event


def test_package_event_to_ros_message_produces_json_string():
    event = build_package_status_event("package_reset", None, "warehouse_bot_01", "reset")
    message = package_event_to_ros_message(event)
    payload = json.loads(message.data)
    assert payload["event_id"] == event.event_id


def test_safe_parse_task_status_for_package_parses_valid_json():
    payload = safe_parse_task_status_for_package('{"event_type":"task_started","task_id":"TASK-001"}')
    assert payload["task_id"] == "TASK-001"


def test_safe_parse_task_status_for_package_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_task_status_for_package("{bad json}")


def test_safe_parse_navigation_progress_for_package_parses_valid_json():
    payload = safe_parse_navigation_progress_for_package('{"current_zone":"shipping","status":"arrived"}')
    assert payload["current_zone"] == "shipping"


def test_create_package_from_task_event_returns_package_info_for_task_started_event():
    package_info = create_package_from_task_event(
        '{"event_type":"task_started","task":{"task_id":"TASK-001","source_zone":"storage_a","destination_zone":"shipping"}}'
    )
    assert package_info is not None
    assert package_info.task_id == "TASK-001"


def test_create_package_from_task_event_returns_none_for_irrelevant_event():
    package_info = create_package_from_task_event('{"event_type":"task_completed"}')
    assert package_info is None
