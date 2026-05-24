"""ROS 1 node that converts task status events into navigation goals."""

from __future__ import annotations

import json

from smart_warehouse_robot.common.constants import NAVIGATION_GOAL_TOPIC, TASK_STATUS_TOPIC
from smart_warehouse_robot.common.helpers import format_navigation_goal_summary
from smart_warehouse_robot.common.models import NavigationGoal

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def extract_task_payload_from_status_event(event_json: str) -> dict | None:
    """Return a task payload from either nested or flattened event JSON."""
    try:
        payload = json.loads(event_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid task status event JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid task status event JSON: expected a JSON object.")
    if payload.get("event_type") != "task_started":
        return None
    if isinstance(payload.get("task"), dict):
        return payload["task"]
    required_keys = {"task_id", "source_zone", "destination_zone", "priority"}
    if required_keys.issubset(payload):
        return {
            "task_id": payload["task_id"],
            "source_zone": payload["source_zone"],
            "destination_zone": payload["destination_zone"],
            "priority": payload["priority"],
            "status": payload.get("status", "in_progress"),
        }
    raise ValueError("Task status event is missing task fields required for navigation.")


def navigation_goal_from_status_event(event_json: str) -> NavigationGoal | None:
    """Convert a task-started event into a NavigationGoal."""
    task_payload = extract_task_payload_from_status_event(event_json)
    if task_payload is None:
        return None
    return NavigationGoal(
        task_id=task_payload.get("task_id"),
        source_zone=task_payload["source_zone"],
        destination_zone=task_payload["destination_zone"],
        priority=task_payload["priority"],
    )


def goal_to_ros_message(goal: NavigationGoal) -> String:
    """Convert a navigation goal into a ROS String message."""
    return String(data=goal.to_json())


class WaypointGoalPublisherNode:
    """Listen for task-started events and publish navigation goals."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run WaypointGoalPublisherNode.")

        self.subscription = rospy.Subscriber(TASK_STATUS_TOPIC, String, self.handle_task_status, queue_size=10)
        self.goal_publisher = rospy.Publisher(NAVIGATION_GOAL_TOPIC, String, queue_size=10)
        rospy.loginfo(
            "WaypointGoalPublisherNode started. Listening on %s and publishing to %s",
            TASK_STATUS_TOPIC,
            NAVIGATION_GOAL_TOPIC,
        )

    def handle_task_status(self, msg: String) -> None:
        """Publish a navigation goal when a task enters the started state."""
        try:
            goal = navigation_goal_from_status_event(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to build navigation goal from task event: %s", exc)
            return
        if goal is None:
            return
        self.goal_publisher.publish(goal_to_ros_message(goal))
        rospy.loginfo("Published navigation goal: %s", format_navigation_goal_summary(goal))


def main() -> None:
    """Run the waypoint goal publisher node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("waypoint_goal_publisher")
    WaypointGoalPublisherNode()
    rospy.spin()


if __name__ == "__main__":
    main()
