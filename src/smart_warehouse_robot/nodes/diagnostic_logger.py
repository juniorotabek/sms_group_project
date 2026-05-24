"""ROS 1 node that creates diagnostic events from robot status snapshots."""

from __future__ import annotations

import json

from smart_warehouse_robot.common.constants import (
    DEFAULT_DIAGNOSTIC_LOG_INTERVAL_SECONDS,
    DEFAULT_ROBOT_NAME,
    DIAGNOSTICS_TOPIC,
    ROBOT_STATUS_TOPIC,
)
from smart_warehouse_robot.common.helpers import format_diagnostic_event_summary
from smart_warehouse_robot.common.models import DiagnosticEvent, RobotStatusSnapshot
from smart_warehouse_robot.services.status import DiagnosticLogger

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def safe_parse_robot_status(message_text: str) -> RobotStatusSnapshot:
    """Parse a robot status JSON payload into a RobotStatusSnapshot."""
    return RobotStatusSnapshot.from_json(message_text)


def diagnostic_event_to_ros_message(event: DiagnosticEvent) -> String:
    """Convert a diagnostic event into a ROS String message."""
    return String(data=event.to_json())


def create_diagnostic_summary_event(summary: dict) -> str:
    """Serialize a lightweight diagnostic summary event for logging or tests."""
    payload = {
        "robot_name": summary.get("robot_name"),
        "total_events": summary.get("total_events"),
        "latest_level": summary.get("latest_level"),
        "latest_message": summary.get("latest_message"),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


class DiagnosticLoggerNode:
    """Convert status snapshots into diagnostic events and publish warnings or worse."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run DiagnosticLoggerNode.")

        self.robot_name = str(rospy.get_param("~robot_name", DEFAULT_ROBOT_NAME))
        self.log_interval_seconds = float(
            rospy.get_param("~log_interval_seconds", DEFAULT_DIAGNOSTIC_LOG_INTERVAL_SECONDS)
        )
        self.max_events = int(rospy.get_param("~max_events", 100))
        self.logger = DiagnosticLogger(robot_name=self.robot_name, max_events=self.max_events)

        self.publisher = rospy.Publisher(DIAGNOSTICS_TOPIC, String, queue_size=10)
        self.status_subscriber = rospy.Subscriber(
            ROBOT_STATUS_TOPIC, String, self.handle_robot_status, queue_size=10
        )
        self.timer = rospy.Timer(rospy.Duration(self.log_interval_seconds), self.publish_summary)
        rospy.loginfo("DiagnosticLoggerNode started. Publishing diagnostics to %s", DIAGNOSTICS_TOPIC)

    def handle_robot_status(self, msg: String) -> None:
        try:
            snapshot = safe_parse_robot_status(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse robot status for diagnostics: %s", exc)
            return

        event = self.logger.add_event(self.logger.event_from_snapshot(snapshot))
        if snapshot.has_warning_or_worse():
            self.publisher.publish(diagnostic_event_to_ros_message(event))
            rospy.logwarn("%s", format_diagnostic_event_summary(event))
        else:
            rospy.loginfo("%s", format_diagnostic_event_summary(event))

    def publish_summary(self, _event=None) -> None:
        summary = self.logger.summary()
        latest = self.logger.latest_event()
        if latest is not None and latest.health_level.value in {"warning", "error", "critical"}:
            self.publisher.publish(diagnostic_event_to_ros_message(latest))
        rospy.loginfo("Diagnostic summary: %s", create_diagnostic_summary_event(summary))


def main() -> None:
    """Run the diagnostic logger node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("diagnostic_logger")
    DiagnosticLoggerNode()
    rospy.spin()


if __name__ == "__main__":
    main()
