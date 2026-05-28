"""ROS 1 node that publishes warehouse task JSON messages."""

from __future__ import annotations

from itertools import cycle

from smart_warehouse_robot.common.constants import DEFAULT_TASK_PUBLISH_INTERVAL_SECONDS, TASK_NEW_TOPIC
from smart_warehouse_robot.common.helpers import format_task_summary
from smart_warehouse_robot.common.models import TaskType, WarehouseTask, WarehouseZone

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover - allows import during non-ROS tests
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def create_sample_tasks(profile: str = "mixed") -> list[WarehouseTask]:
    """Create rotating sample tasks for demo publishing.

    Supported profiles:
    - mixed: general warehouse flow with varied task types.
    - delivery_loop: repeated pickup/dropoff style routes for continuous delivery animation.
    - parking_demo: single pickup location (receiving) with rotating parking spots (parking_a, parking_b, parking_c).
    """
    normalized = str(profile).strip().lower()
    if normalized == "parking_demo":
        # Single pickup from RECEIVING, cycle through 3 parking spots for dropoff
        return [
            WarehouseTask(TaskType.PICKUP, WarehouseZone.RECEIVING, WarehouseZone.PARKING_A, 3),
            WarehouseTask(TaskType.DROPOFF, WarehouseZone.RECEIVING, WarehouseZone.PARKING_B, 4),
            WarehouseTask(TaskType.PICKUP, WarehouseZone.RECEIVING, WarehouseZone.PARKING_C, 3),
            WarehouseTask(TaskType.DROPOFF, WarehouseZone.RECEIVING, WarehouseZone.PARKING_A, 4),
        ]
    if normalized == "delivery_loop":
        return [
            WarehouseTask(TaskType.PICKUP, WarehouseZone.RECEIVING, WarehouseZone.STORAGE_A, 3),
            WarehouseTask(TaskType.DROPOFF, WarehouseZone.STORAGE_A, WarehouseZone.SHIPPING, 4),
            WarehouseTask(TaskType.PICKUP, WarehouseZone.PACKING, WarehouseZone.STORAGE_B, 3),
            WarehouseTask(TaskType.DROPOFF, WarehouseZone.STORAGE_B, WarehouseZone.SHIPPING, 4),
        ]

    return [
        WarehouseTask(TaskType.PICKUP, WarehouseZone.RECEIVING, WarehouseZone.STORAGE_A, 3),
        WarehouseTask(TaskType.MOVE, WarehouseZone.STORAGE_A, WarehouseZone.PACKING, 2),
        WarehouseTask(TaskType.DROPOFF, WarehouseZone.PACKING, WarehouseZone.SHIPPING, 4),
        WarehouseTask(TaskType.CHARGE, WarehouseZone.SHIPPING, WarehouseZone.CHARGING_STATION, 1),
    ]


def task_to_ros_message(task: WarehouseTask) -> String:
    """Convert a task model into a ROS String message."""
    return String(data=task.to_json())


class TaskPublisherNode:
    """Publish warehouse tasks on a timer using ROS 1 publishers."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run TaskPublisherNode.")

        self.publish_interval_seconds = float(rospy.get_param("~publish_interval_seconds", DEFAULT_TASK_PUBLISH_INTERVAL_SECONDS))
        self.auto_publish_sample_tasks = bool(rospy.get_param("~auto_publish_sample_tasks", True))
        self.sample_profile = str(rospy.get_param("~sample_profile", "mixed"))
        self.publisher = rospy.Publisher(TASK_NEW_TOPIC, String, queue_size=10)
        self._sample_task_iterator = cycle(create_sample_tasks(self.sample_profile))
        self.timer = None

        if self.auto_publish_sample_tasks:
            self.timer = rospy.Timer(rospy.Duration(self.publish_interval_seconds), self.publish_sample_task)
            rospy.loginfo(
                "TaskPublisherNode started with auto sample publishing every %.1fs on %s (profile=%s)",
                self.publish_interval_seconds,
                TASK_NEW_TOPIC,
                self.sample_profile,
            )
        else:
            rospy.loginfo("TaskPublisherNode started with auto sample publishing disabled. Topic: %s", TASK_NEW_TOPIC)

    def publish_sample_task(self, _event=None) -> None:
        """Publish the next rotating sample task."""
        task = next(self._sample_task_iterator)
        self.publisher.publish(task_to_ros_message(task))
        rospy.loginfo("Published task: %s", format_task_summary(task))


def main() -> None:
    """Run the task publisher node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("task_publisher")
    TaskPublisherNode()
    rospy.spin()


if __name__ == "__main__":
    main()
