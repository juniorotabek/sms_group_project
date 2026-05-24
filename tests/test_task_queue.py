import pytest

from smart_warehouse_robot.common.models import TaskStatus, WarehouseTask
from smart_warehouse_robot.services.task_queue import TaskQueue


def make_task(priority: int, task_id: str) -> WarehouseTask:
    return WarehouseTask(
        task_id=task_id,
        task_type="pickup",
        source_zone="receiving",
        destination_zone="storage_a",
        priority=priority,
    )


def test_add_task_makes_it_queued():
    queue = TaskQueue()
    task = queue.add_task(make_task(3, "TASK-001"))

    assert task.status == TaskStatus.QUEUED


def test_get_task_by_id():
    queue = TaskQueue()
    task = queue.add_task(make_task(3, "TASK-001"))

    assert queue.get_task(task.task_id) is task


def test_list_queued_tasks():
    queue = TaskQueue()
    queue.add_task(make_task(2, "TASK-001"))
    queue.add_task(make_task(4, "TASK-002"))

    queued_tasks = queue.list_tasks(TaskStatus.QUEUED)
    assert len(queued_tasks) == 2
    assert all(task.status == TaskStatus.QUEUED for task in queued_tasks)


def test_priority_sorting_works():
    queue = TaskQueue()
    queue.add_task(make_task(1, "TASK-001"))
    queue.add_task(make_task(5, "TASK-002"))

    assert queue.get_next_task().task_id == "TASK-002"


def test_start_next_task_assigns_robot_and_marks_in_progress():
    queue = TaskQueue()
    queue.add_task(make_task(5, "TASK-001"))

    started = queue.start_next_task("warehouse_bot_01")

    assert started is not None
    assert started.assigned_robot == "warehouse_bot_01"
    assert started.status == TaskStatus.IN_PROGRESS


def test_complete_task_marks_completed():
    queue = TaskQueue()
    task = queue.add_task(make_task(5, "TASK-001"))

    queue.complete_task(task.task_id)

    assert task.status == TaskStatus.COMPLETED


def test_cancel_task_marks_cancelled():
    queue = TaskQueue()
    task = queue.add_task(make_task(5, "TASK-001"))

    queue.cancel_task(task.task_id)

    assert task.status == TaskStatus.CANCELLED


def test_unknown_task_id_raises_value_error():
    queue = TaskQueue()

    with pytest.raises(ValueError, match="Unknown task_id"):
        queue.complete_task("TASK-404")
