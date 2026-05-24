"""ROS 1 node that simulates and publishes battery state."""

from __future__ import annotations

import json

from smart_warehouse_robot.common.constants import (
    BATTERY_STATE_TOPIC,
    CHARGING_STATION_ZONE,
    DEFAULT_BATTERY_CHARGE_PERCENT,
    DEFAULT_BATTERY_DRAIN_PERCENT,
    DEFAULT_BATTERY_PUBLISH_INTERVAL_SECONDS,
    DEFAULT_ROBOT_NAME,
    NAVIGATION_PROGRESS_TOPIC,
)
from smart_warehouse_robot.common.helpers import format_battery_summary, parse_warehouse_zone
from smart_warehouse_robot.common.models import BatteryState, ChargingStatus, NavigationStatus
from smart_warehouse_robot.services.battery import BatterySimulator

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def battery_state_to_ros_message(state: BatteryState) -> String:
    """Convert a battery state into a ROS String message."""
    return String(data=state.to_json())


def safe_parse_navigation_progress_for_battery(message_text: str) -> dict:
    """Parse navigation progress JSON and return a dict for battery updates."""
    try:
        payload = json.loads(message_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid navigation progress JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid navigation progress JSON: expected a JSON object.")
    return payload


class BatteryPublisherNode:
    """Simulate battery drain/charge and publish battery state."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run BatteryPublisherNode.")

        robot_name = str(rospy.get_param("~robot_name", DEFAULT_ROBOT_NAME))
        publish_interval_seconds = float(rospy.get_param("~publish_interval_seconds", DEFAULT_BATTERY_PUBLISH_INTERVAL_SECONDS))
        start_percentage = float(rospy.get_param("~start_percentage", 100.0))
        battery_drain_percent = float(rospy.get_param("~battery_drain_percent", DEFAULT_BATTERY_DRAIN_PERCENT))
        battery_charge_percent = float(rospy.get_param("~battery_charge_percent", DEFAULT_BATTERY_CHARGE_PERCENT))
        start_zone = parse_warehouse_zone(rospy.get_param("~start_zone", "receiving"))

        self.simulator = BatterySimulator(
            robot_name=robot_name,
            start_percentage=start_percentage,
            start_zone=start_zone,
            drain_percent=battery_drain_percent,
            charge_percent=battery_charge_percent,
        )
        self.publisher = rospy.Publisher(BATTERY_STATE_TOPIC, String, queue_size=10)
        self.subscription = rospy.Subscriber(NAVIGATION_PROGRESS_TOPIC, String, self.handle_navigation_progress, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(publish_interval_seconds), self.publish_battery_state)
        rospy.loginfo("BatteryPublisherNode started. Publishing to %s", BATTERY_STATE_TOPIC)

    def handle_navigation_progress(self, msg: String) -> None:
        """Update battery simulator zone and charging state from navigation progress."""
        try:
            payload = safe_parse_navigation_progress_for_battery(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse navigation progress for battery: %s", exc)
            return

        current_zone = payload.get("current_zone")
        if current_zone is not None:
            try:
                self.simulator.set_current_zone(parse_warehouse_zone(current_zone))
            except ValueError as exc:
                rospy.logerr("Failed to parse current_zone for battery update: %s", exc)
                return

        if payload.get("current_zone") == CHARGING_STATION_ZONE and payload.get("status") == NavigationStatus.ARRIVED.value:
            self.simulator.start_charging()

    def publish_battery_state(self, _event=None) -> None:
        """Advance the battery simulation and publish the current state."""
        state = self.simulator.get_state()
        if state.charging_status == ChargingStatus.CHARGING:
            state = self.simulator.charge()
            state = self.simulator.stop_charging_if_full()
        elif state.charging_status == ChargingStatus.CHARGED:
            state = self.simulator.get_state()
        else:
            state = self.simulator.drain()

        self.publisher.publish(battery_state_to_ros_message(state))
        rospy.loginfo("%s", format_battery_summary(state))


def main() -> None:
    """Run the battery publisher node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("battery_publisher")
    BatteryPublisherNode()
    rospy.spin()


if __name__ == "__main__":
    main()
