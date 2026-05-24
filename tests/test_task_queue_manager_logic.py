import json

import pytest

from smart_warehouse_robot.common.models import WarehouseTask
from smart_warehouse_robot.nodes.task_queue_manager import create_status_event, safe_parse_task_message


def test_safe_parse_task_message_parses_valid_json():
    task = WarehouseTask(
        task_type="pickup",
        source_zone="receiving",
        destination_zone="storage_a",
        priority=3,
    )

    parsed = safe_parse_task_message(task.to_json())

    assert parsed.task_id == task.task_id


def test_safe_parse_task_message_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_task_message("{not valid json}")


def test_create_status_event_returns_expected_keys():
    task = WarehouseTask(
        task_type="pickup",
        source_zone="receiving",
        destination_zone="storage_a",
        priority=3,
    )
    payload = json.loads(create_status_event("task_queued", task, {"total_tasks": 1}))

    assert payload["event_type"] == "task_queued"
    assert payload["task_id"] == task.task_id
    assert payload["status"] == task.status.value
    assert payload["queue_summary"] == {"total_tasks": 1}
    assert "timestamp" in payload
