"""ROS 1 node that aggregates robot state and publishes status snapshots."""

from __future__ import annotations

import json

from smart_warehouse_robot.common.constants import (
    BATTERY_STATE_TOPIC,
    DEFAULT_ROBOT_NAME,
    DEFAULT_STATUS_PUBLISH_INTERVAL_SECONDS,
    EMERGENCY_STOP_TOPIC,
    NAVIGATION_PROGRESS_TOPIC,
    PACKAGE_STATUS_TOPIC,
    ROBOT_STATUS_TOPIC,
    TASK_STATUS_TOPIC,
)
from smart_warehouse_robot.common.helpers import format_robot_status_summary, parse_warehouse_zone
from smart_warehouse_robot.common.models import RobotStatusSnapshot, WarehouseZone
from smart_warehouse_robot.services.status import RobotStatusAggregator

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def robot_status_to_ros_message(snapshot: RobotStatusSnapshot) -> String:
    """Convert a status snapshot into a ROS String message."""
    return String(data=snapshot.to_json())


def safe_parse_json_event(message_text: str, source_name: str = "unknown") -> dict:
    """Parse a JSON event and raise a helpful error on invalid input."""
    try:
        payload = json.loads(message_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid {source_name} JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid {source_name} JSON: expected a JSON object.")
    return payload


class StatusPublisherNode:
    """Aggregate robot state from topic events and publish status snapshots."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run StatusPublisherNode.")

        self.robot_name = str(rospy.get_param("~robot_name", DEFAULT_ROBOT_NAME))
        self.publish_interval_seconds = float(
            rospy.get_param("~publish_interval_seconds", DEFAULT_STATUS_PUBLISH_INTERVAL_SECONDS)
        )
        self.start_zone = parse_warehouse_zone(rospy.get_param("~start_zone", WarehouseZone.RECEIVING.value))
        self.aggregator = RobotStatusAggregator(robot_name=self.robot_name, start_zone=self.start_zone)

        self.publisher = rospy.Publisher(ROBOT_STATUS_TOPIC, String, queue_size=10)
        self.task_subscriber = rospy.Subscriber(TASK_STATUS_TOPIC, String, self.handle_task_status, queue_size=10)
        self.navigation_subscriber = rospy.Subscriber(
            NAVIGATION_PROGRESS_TOPIC, String, self.handle_navigation_progress, queue_size=10
        )
        self.estop_subscriber = rospy.Subscriber(
            EMERGENCY_STOP_TOPIC, String, self.handle_emergency_stop, queue_size=10
        )
        self.battery_subscriber = rospy.Subscriber(
            BATTERY_STATE_TOPIC, String, self.handle_battery_state, queue_size=10
        )
        self.package_subscriber = rospy.Subscriber(
            PACKAGE_STATUS_TOPIC, String, self.handle_package_status, queue_size=10
        )
        self.timer = rospy.Timer(rospy.Duration(self.publish_interval_seconds), self.publish_status)
        rospy.loginfo("StatusPublisherNode started. Publishing robot status to %s", ROBOT_STATUS_TOPIC)

    def handle_task_status(self, msg: String) -> None:
        try:
            payload = safe_parse_json_event(msg.data, "task status")
            self.aggregator.update_from_task_status(payload)
        except ValueError as exc:
            rospy.logerr("Failed to parse task status for robot status: %s", exc)

    def handle_navigation_progress(self, msg: String) -> None:
        try:
            payload = safe_parse_json_event(msg.data, "navigation progress")
            self.aggregator.update_from_navigation_progress(payload)
        except ValueError as exc:
            rospy.logerr("Failed to parse navigation progress for robot status: %s", exc)

    def handle_emergency_stop(self, msg: String) -> None:
        try:
            payload = safe_parse_json_event(msg.data, "emergency stop")
            self.aggregator.update_from_emergency_stop(payload)
        except ValueError as exc:
            rospy.logerr("Failed to parse emergency stop for robot status: %s", exc)

    def handle_battery_state(self, msg: String) -> None:
        try:
            payload = safe_parse_json_event(msg.data, "battery state")
            self.aggregator.update_from_battery_state(payload)
        except ValueError as exc:
            rospy.logerr("Failed to parse battery state for robot status: %s", exc)

    def handle_package_status(self, msg: String) -> None:
        try:
            payload = safe_parse_json_event(msg.data, "package status")
            self.aggregator.update_from_package_status(payload)
        except ValueError as exc:
            rospy.logerr("Failed to parse package status for robot status: %s", exc)

    def publish_status(self, _event=None) -> None:
        snapshot = self.aggregator.get_snapshot()
        self.publisher.publish(robot_status_to_ros_message(snapshot))
        rospy.loginfo("%s", format_robot_status_summary(snapshot))


def main() -> None:
    """Run the robot status publisher node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("status_publisher")
    StatusPublisherNode()
    rospy.spin()


if __name__ == "__main__":
    main()
