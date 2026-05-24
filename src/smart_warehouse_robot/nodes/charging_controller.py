"""ROS 1 node that publishes return-to-charge commands from battery state."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from smart_warehouse_robot.common.constants import (
    DEFAULT_CRITICAL_BATTERY_THRESHOLD,
    DEFAULT_LOW_BATTERY_THRESHOLD,
    NAVIGATION_GOAL_TOPIC,
    RETURN_TO_CHARGE_TOPIC,
    BATTERY_STATE_TOPIC,
)
from smart_warehouse_robot.common.helpers import (
    build_charge_command,
    build_charge_navigation_goal,
    format_battery_summary,
    format_charge_command_summary,
    should_emergency_stop_for_battery,
    should_return_to_charge,
)
from smart_warehouse_robot.common.models import BatteryState, ChargeCommand, ChargingStatus, NavigationGoal

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def safe_parse_battery_state(message_text: str) -> BatteryState:
    """Parse battery state JSON from a ROS message."""
    return BatteryState.from_json(message_text)


def charge_command_to_ros_message(command: ChargeCommand) -> String:
    """Convert a charge command into a ROS String message."""
    return String(data=command.to_json())


def charge_navigation_goal_to_ros_message(goal: NavigationGoal) -> String:
    """Convert a charge navigation goal into a ROS String message."""
    return String(data=goal.to_json())


def create_battery_alert_event(state: BatteryState, command: ChargeCommand | None) -> str:
    """Create a stable JSON alert event for logging or tests."""
    payload = {
        "event_type": "battery_alert",
        "robot_name": state.robot_name,
        "battery_id": state.battery_id,
        "percentage": state.percentage,
        "level": state.level.value,
        "charging_status": state.charging_status.value,
        "command_id": command.command_id if command is not None else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


class ChargingControllerNode:
    """Detect low battery and publish return-to-charge commands."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run ChargingControllerNode.")

        self.low_battery_threshold = float(rospy.get_param("~low_battery_threshold", DEFAULT_LOW_BATTERY_THRESHOLD))
        self.critical_battery_threshold = float(rospy.get_param("~critical_battery_threshold", DEFAULT_CRITICAL_BATTERY_THRESHOLD))
        self.publish_navigation_goal = bool(rospy.get_param("~publish_navigation_goal", True))
        self.command_active = False
        self.last_command_battery_id: str | None = None

        self.subscription = rospy.Subscriber(BATTERY_STATE_TOPIC, String, self.handle_battery_state, queue_size=10)
        self.command_publisher = rospy.Publisher(RETURN_TO_CHARGE_TOPIC, String, queue_size=10)
        self.goal_publisher = rospy.Publisher(NAVIGATION_GOAL_TOPIC, String, queue_size=10)
        rospy.loginfo("ChargingControllerNode started. Listening on %s", BATTERY_STATE_TOPIC)

    def handle_battery_state(self, msg: String) -> None:
        """Publish return-to-charge command and navigation goal when battery is low."""
        try:
            state = safe_parse_battery_state(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse battery state: %s", exc)
            return

        if state.charging_status in {ChargingStatus.CHARGING, ChargingStatus.CHARGED, ChargingStatus.RETURNING_TO_CHARGE}:
            self.command_active = False
            self.last_command_battery_id = None
            return

        if should_emergency_stop_for_battery(state.percentage, self.critical_battery_threshold):
            rospy.logwarn("Critical battery warning: %s", format_battery_summary(state))

        if not should_return_to_charge(state.percentage, self.low_battery_threshold):
            return

        if self.command_active and self.last_command_battery_id == state.battery_id:
            return

        command = build_charge_command(state)
        self.command_publisher.publish(charge_command_to_ros_message(command))
        rospy.logwarn("%s", format_charge_command_summary(command))

        if self.publish_navigation_goal:
            goal = build_charge_navigation_goal(command)
            self.goal_publisher.publish(charge_navigation_goal_to_ros_message(goal))
            rospy.loginfo("Published charge navigation goal %s", goal.goal_id)

        self.command_active = True
        self.last_command_battery_id = state.battery_id
        rospy.loginfo("%s", create_battery_alert_event(state, command))


def main() -> None:
    """Run the charging controller node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("charging_controller")
    ChargingControllerNode()
    rospy.spin()


if __name__ == "__main__":
    main()
