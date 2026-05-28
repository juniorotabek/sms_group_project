"""ROS 1 node that manages incoming tasks and queue status updates."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from smart_warehouse_robot.common.constants import (
    DEFAULT_ROBOT_NAME,
    PACKAGE_STATUS_TOPIC,
    TASK_NEW_TOPIC,
    TASK_STATUS_TOPIC,
)
from smart_warehouse_robot.common.models import PackageState, PackageStatusEvent, TaskStatus, WarehouseTask
from smart_warehouse_robot.services.task_queue import TaskQueue

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def create_status_event(event_type: str, task: WarehouseTask, queue_summary: dict) -> str:
    """Create a stable JSON status event payload."""
    payload = {
        "event_type": event_type,
        "task_id": task.task_id,
        "task_type": task.task_type.value,
        "source_zone": task.source_zone.value,
        "destination_zone": task.destination_zone.value,
        "priority": task.priority,
        "status": task.status.value,
        "assigned_robot": task.assigned_robot,
        "task": task.to_dict(),
        "queue_summary": queue_summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def safe_parse_task_message(message_text: str) -> WarehouseTask:
    """Parse task JSON from a ROS message and raise ValueError on invalid input."""
    return WarehouseTask.from_json(message_text)


class TaskQueueManagerNode:
    """Manage a simple in-memory task queue from incoming ROS topic messages."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run TaskQueueManagerNode.")

        self.robot_name = str(rospy.get_param("~robot_name", DEFAULT_ROBOT_NAME))
        self.auto_process_tasks = bool(rospy.get_param("~auto_process_tasks", True))

        self.queue = TaskQueue()
        self.current_task_id: str | None = None

        self.subscription = rospy.Subscriber(TASK_NEW_TOPIC, String, self.handle_new_task, queue_size=10)
        self.package_subscription = rospy.Subscriber(PACKAGE_STATUS_TOPIC, String, self.handle_package_status, queue_size=10)
        self.status_publisher = rospy.Publisher(TASK_STATUS_TOPIC, String, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(3.0), self.process_queue)
        rospy.loginfo(
            "TaskQueueManagerNode started. Listening on %s and %s, publishing to %s",
            TASK_NEW_TOPIC,
            PACKAGE_STATUS_TOPIC,
            TASK_STATUS_TOPIC,
        )

    def publish_status_payload(self, payload: str) -> None:
        """Publish a JSON status payload to the task status topic."""
        self.status_publisher.publish(String(data=payload))

    def publish_task_event(self, event_type: str, task: WarehouseTask) -> None:
        """Publish a task-related event along with the current queue summary."""
        self.publish_status_payload(create_status_event(event_type, task, self.queue.summary()))

    def publish_invalid_task_event(self, raw_message: str, error_message: str) -> None:
        """Publish a failure event for malformed incoming task messages."""
        payload = {
            "event_type": "task_failed",
            "task_id": None,
            "status": TaskStatus.FAILED.value,
            "assigned_robot": None,
            "queue_summary": self.queue.summary(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error_message,
            "raw_message": raw_message,
        }
        self.publish_status_payload(json.dumps(payload, indent=2, sort_keys=True))

    def handle_new_task(self, msg: String) -> None:
        """Receive, validate, queue, and acknowledge new tasks."""
        try:
            task = safe_parse_task_message(msg.data)
            queued_task = self.queue.add_task(task)
            rospy.loginfo("Queued task %s", queued_task.task_id)
            self.publish_task_event("task_queued", queued_task)
            self.publish_queue_summary()
        except ValueError as exc:
            rospy.logerr("Failed to parse incoming task message: %s", exc)
            self.publish_invalid_task_event(msg.data, str(exc))

    def publish_queue_summary(self) -> None:
        """Publish queue summary even when no task changed state."""
        payload = {
            "event_type": "queue_summary",
            "task_id": self.current_task_id,
            "status": None,
            "assigned_robot": self.robot_name if self.current_task_id else None,
            "queue_summary": self.queue.summary(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.publish_status_payload(json.dumps(payload, indent=2, sort_keys=True))

    def complete_current_task(self, reason: str) -> None:
        """Complete the active task, publish events, and reset active tracking."""
        if self.current_task_id is None:
            return

        current_task = self.queue.get_task(self.current_task_id)
        if current_task is None or current_task.status != TaskStatus.IN_PROGRESS:
            return

        completed_task = self.queue.complete_task(current_task.task_id)
        rospy.loginfo("Completed task %s (%s)", completed_task.task_id, reason)
        self.publish_task_event("task_completed", completed_task)
        self.current_task_id = None
        self.publish_queue_summary()

    def handle_package_status(self, msg: String) -> None:
        """Complete the active task only after the package is actually delivered."""
        if self.current_task_id is None:
            return

        try:
            package_event = PackageStatusEvent.from_json(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse package status in task manager: %s", exc)
            return

        if package_event.package_state != PackageState.DELIVERED:
            return

        if package_event.task_id != self.current_task_id:
            return

        self.complete_current_task("package_delivered")

    def process_queue(self, _event=None) -> None:
        """Simulate starting tasks; completion is driven by package delivery events."""
        if not self.auto_process_tasks:
            return

        current_task = self.queue.get_task(self.current_task_id) if self.current_task_id else None
        if current_task is not None and current_task.status == TaskStatus.IN_PROGRESS:
            return

        next_task = self.queue.start_next_task(self.robot_name)
        if next_task is not None:
            self.current_task_id = next_task.task_id
            rospy.loginfo("Started task %s on robot %s", next_task.task_id, self.robot_name)
            self.publish_task_event("task_started", next_task)
            self.publish_queue_summary()


def main() -> None:
    """Run the task queue manager node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("task_queue_manager")
    TaskQueueManagerNode()
    rospy.spin()


if __name__ == "__main__":
    main()
