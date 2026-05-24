"""ROS 1 node that turns obstacle readings into emergency-stop commands."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from smart_warehouse_robot.common.constants import EMERGENCY_STOP_TOPIC, OBSTACLE_TOPIC
from smart_warehouse_robot.common.helpers import format_emergency_stop_summary, format_obstacle_summary
from smart_warehouse_robot.common.models import EmergencyStopCommand, ObstacleReading, SafetyState
from smart_warehouse_robot.services.safety import SafetyMonitor

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def safe_parse_obstacle_message(message_text: str) -> ObstacleReading:
    """Parse obstacle JSON from a ROS message."""
    return ObstacleReading.from_json(message_text)


def emergency_command_to_ros_message(command: EmergencyStopCommand) -> String:
    """Convert an emergency-stop command into a ROS String message."""
    return String(data=command.to_json())


def create_safety_summary_event(summary: dict) -> str:
    """Create a stable JSON summary event for logging or publication."""
    payload = {
        "event_type": "safety_summary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **summary,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


class EmergencyStopNode:
    """Subscribe to obstacle readings and publish emergency-stop commands when required."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run EmergencyStopNode.")

        self.monitor = SafetyMonitor()
        self.subscription = rospy.Subscriber(OBSTACLE_TOPIC, String, self.handle_obstacle_reading, queue_size=10)
        self.publisher = rospy.Publisher(EMERGENCY_STOP_TOPIC, String, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(5.0), self.log_safety_summary)
        rospy.loginfo(
            "EmergencyStopNode started. Listening on %s and publishing to %s",
            OBSTACLE_TOPIC,
            EMERGENCY_STOP_TOPIC,
        )

    def handle_obstacle_reading(self, msg: String) -> None:
        """Process incoming obstacle readings and publish emergency commands when needed."""
        try:
            reading = safe_parse_obstacle_message(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse obstacle reading: %s", exc)
            return
        rospy.loginfo("%s", format_obstacle_summary(reading))
        command = self.monitor.process_reading(reading)
        if command is None:
            if self.monitor.get_safety_state() == SafetyState.WARNING:
                rospy.logwarn("Safety warning: %s", format_obstacle_summary(reading))
            return
        self.publisher.publish(emergency_command_to_ros_message(command))
        rospy.logwarn("%s", format_emergency_stop_summary(command))

    def log_safety_summary(self, _event=None) -> None:
        """Log the current safety summary periodically."""
        rospy.loginfo("%s", create_safety_summary_event(self.monitor.summary()))


def main() -> None:
    """Run the emergency stop node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("emergency_stop")
    EmergencyStopNode()
    rospy.spin()


if __name__ == "__main__":
    main()
