import json

import pytest

from smart_warehouse_robot.common.models import TaskStatus, TaskType, WarehouseTask, WarehouseZone


def test_create_task_successfully():
    task = WarehouseTask(
        task_type="pickup",
        source_zone="receiving",
        destination_zone="storage_a",
        priority=3,
    )

    assert task.task_type == TaskType.PICKUP
    assert task.source_zone == WarehouseZone.RECEIVING
    assert task.destination_zone == WarehouseZone.STORAGE_A
    assert task.status == TaskStatus.CREATED
    assert task.task_id.startswith("TASK-")


def test_task_json_round_trip():
    task = WarehouseTask(
        task_type="move",
        source_zone="storage_a",
        destination_zone="packing",
        priority=2,
        notes="Move pallet to packing",
    )

    restored = WarehouseTask.from_json(task.to_json())

    assert restored.to_dict() == task.to_dict()


def test_invalid_task_type_raises_value_error():
    with pytest.raises(ValueError, match="Invalid task type"):
        WarehouseTask(
            task_type="teleport",
            source_zone="receiving",
            destination_zone="storage_a",
            priority=3,
        )


def test_priority_below_one_becomes_one():
    task = WarehouseTask(
        task_type="pickup",
        source_zone="receiving",
        destination_zone="storage_a",
        priority=-3,
    )
    assert task.priority == 1


def test_priority_above_five_becomes_five():
    task = WarehouseTask(
        task_type="pickup",
        source_zone="receiving",
        destination_zone="storage_a",
        priority=99,
    )
    assert task.priority == 5


def test_terminal_statuses_work():
    task = WarehouseTask(
        task_type="charge",
        source_zone="shipping",
        destination_zone="charging_station",
        priority=1,
        status="completed",
    )
    assert task.is_terminal() is True
    task.mark_cancelled()
    assert task.status == TaskStatus.CANCELLED
    assert task.is_terminal() is True


def test_from_json_rejects_invalid_payload():
    with pytest.raises(ValueError, match="Invalid task JSON"):
        WarehouseTask.from_json("not-json")
