"""In-memory queue logic for warehouse task management."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from smart_warehouse_robot.common.helpers import sort_tasks_by_priority
from smart_warehouse_robot.common.models import TaskStatus, WarehouseTask


class TaskQueue:
    """Simple in-memory task queue used by the queue manager node and CLI."""

    def __init__(self) -> None:
        self._tasks: dict[str, WarehouseTask] = {}

    def add_task(self, task: WarehouseTask) -> WarehouseTask:
        """Store a task and mark it queued for later processing."""
        task.mark_queued()
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[WarehouseTask]:
        """Return a task by id if it exists."""
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> list[WarehouseTask]:
        """List all tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [task for task in tasks if task.status == status]
        return sort_tasks_by_priority(tasks)

    def get_next_task(self) -> Optional[WarehouseTask]:
        """Return the highest-priority queued task."""
        queued_tasks = self.list_tasks(TaskStatus.QUEUED)
        return queued_tasks[0] if queued_tasks else None

    def start_next_task(self, robot_name: str) -> Optional[WarehouseTask]:
        """Start the next queued task and assign it to a robot."""
        task = self.get_next_task()
        if task is None:
            return None
        if task.is_terminal():
            return None

        task.assigned_robot = robot_name
        task.mark_in_progress()
        return task

    def update_status(self, task_id: str, status: TaskStatus) -> WarehouseTask:
        """Update a task status or raise when the task is unknown."""
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Unknown task_id: {task_id}")
        task.status = status
        return task

    def complete_task(self, task_id: str) -> WarehouseTask:
        """Mark an existing task as completed."""
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Unknown task_id: {task_id}")
        task.mark_completed()
        return task

    def cancel_task(self, task_id: str) -> WarehouseTask:
        """Mark an existing task as cancelled."""
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Unknown task_id: {task_id}")
        task.mark_cancelled()
        return task

    def summary(self) -> dict:
        """Return overall queue counts for CLI output and status events."""
        counts = Counter(task.status.value for task in self._tasks.values())
        return {
            "total_tasks": len(self._tasks),
            "queued_tasks": counts.get(TaskStatus.QUEUED.value, 0),
            "in_progress_tasks": counts.get(TaskStatus.IN_PROGRESS.value, 0),
            "completed_tasks": counts.get(TaskStatus.COMPLETED.value, 0),
            "cancelled_tasks": counts.get(TaskStatus.CANCELLED.value, 0),
            "failed_tasks": counts.get(TaskStatus.FAILED.value, 0),
            "counts_by_status": dict(sorted(counts.items())),
        }
