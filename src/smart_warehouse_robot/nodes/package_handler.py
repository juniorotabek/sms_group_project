"""ROS 1 node that exposes package pickup/dropoff services and status events."""

from __future__ import annotations

import json

from smart_warehouse_robot.common.constants import (
    DEFAULT_ROBOT_NAME,
    NAVIGATION_PROGRESS_TOPIC,
    PACKAGE_DROPOFF_SERVICE,
    PACKAGE_PICKUP_SERVICE,
    PACKAGE_RESET_SERVICE,
    PACKAGE_STATUS_TOPIC,
    TASK_STATUS_TOPIC,
)
from smart_warehouse_robot.common.helpers import (
    build_package_info,
    format_package_event_summary,
    format_package_summary,
    parse_warehouse_zone,
)
from smart_warehouse_robot.common.models import NavigationStatus, PackageInfo, PackageState, PackageStatusEvent
from smart_warehouse_robot.services.package_handler import PackageHandler

try:
    import rospy
    from std_msgs.msg import String
    from std_srvs.srv import Trigger, TriggerResponse
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data

    class TriggerResponse:  # pragma: no cover
        def __init__(self, success: bool = False, message: str = "") -> None:
            self.success = success
            self.message = message

    class Trigger:  # pragma: no cover
        pass


def package_event_to_ros_message(event: PackageStatusEvent) -> String:
    """Convert a package status event into a ROS String message."""
    return String(data=event.to_json())


def safe_parse_task_status_for_package(message_text: str) -> dict:
    """Parse task status JSON for package preparation."""
    try:
        payload = json.loads(message_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid task status JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid task status JSON: expected a JSON object.")
    return payload


def safe_parse_navigation_progress_for_package(message_text: str) -> dict:
    """Parse navigation progress JSON for pickup/dropoff readiness checks."""
    try:
        payload = json.loads(message_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid navigation progress JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid navigation progress JSON: expected a JSON object.")
    return payload


def create_package_from_task_event(event_json: str) -> PackageInfo | None:
    """Create package info from a task_started event when zones are available."""
    payload = safe_parse_task_status_for_package(event_json)
    if payload.get("event_type") != "task_started":
        return None

    task_payload = payload.get("task") if isinstance(payload.get("task"), dict) else payload
    if "source_zone" not in task_payload or "destination_zone" not in task_payload:
        return None

    return build_package_info(
        package_id=None,
        source_zone=task_payload["source_zone"],
        destination_zone=task_payload["destination_zone"],
        task_id=task_payload.get("task_id"),
        notes=task_payload.get("notes"),
    )


class PackageHandlerNode:
    """Provide package pickup/dropoff services and publish package status events."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run PackageHandlerNode.")

        robot_name = str(rospy.get_param("~robot_name", DEFAULT_ROBOT_NAME))
        self.default_source_zone = parse_warehouse_zone(rospy.get_param("~default_source_zone", "storage_a"))
        self.default_destination_zone = parse_warehouse_zone(rospy.get_param("~default_destination_zone", "shipping"))
        self.auto_create_package_on_pickup = bool(rospy.get_param("~auto_create_package_on_pickup", True))

        self.handler = PackageHandler(robot_name=robot_name)
        self.publisher = rospy.Publisher(PACKAGE_STATUS_TOPIC, String, queue_size=10)
        self.task_subscription = rospy.Subscriber(TASK_STATUS_TOPIC, String, self.handle_task_status, queue_size=10)
        self.navigation_subscription = rospy.Subscriber(
            NAVIGATION_PROGRESS_TOPIC, String, self.handle_navigation_progress, queue_size=10
        )
        self.pickup_service = rospy.Service(PACKAGE_PICKUP_SERVICE, Trigger, self.handle_pickup)
        self.dropoff_service = rospy.Service(PACKAGE_DROPOFF_SERVICE, Trigger, self.handle_dropoff)
        self.reset_service = rospy.Service(PACKAGE_RESET_SERVICE, Trigger, self.handle_reset)
        rospy.loginfo("PackageHandlerNode started. Publishing package status to %s", PACKAGE_STATUS_TOPIC)

    def publish_event(self, event: PackageStatusEvent) -> None:
        """Publish a package status event."""
        self.publisher.publish(package_event_to_ros_message(event))
        rospy.loginfo("%s", format_package_event_summary(event))

    def handle_pickup(self, _request) -> TriggerResponse:
        """Handle package pickup service calls."""
        try:
            if self.handler.get_current_package() is None and self.auto_create_package_on_pickup:
                self.handler.create_package(
                    source_zone=self.default_source_zone,
                    destination_zone=self.default_destination_zone,
                )
            event = self.handler.pickup()
            self.publish_event(event)
            return TriggerResponse(success=True, message=format_package_event_summary(event))
        except ValueError as exc:
            rospy.logwarn("Package pickup failed: %s", exc)
            return TriggerResponse(success=False, message=str(exc))

    def handle_dropoff(self, _request) -> TriggerResponse:
        """Handle package dropoff service calls."""
        try:
            event = self.handler.dropoff()
            self.publish_event(event)
            return TriggerResponse(success=True, message=format_package_event_summary(event))
        except ValueError as exc:
            rospy.logwarn("Package dropoff failed: %s", exc)
            return TriggerResponse(success=False, message=str(exc))

    def handle_reset(self, _request) -> TriggerResponse:
        """Handle package reset service calls."""
        event = self.handler.reset()
        self.publish_event(event)
        return TriggerResponse(success=True, message=format_package_event_summary(event))

    def handle_task_status(self, msg: String) -> None:
        """Prepare a package when a task starts with source/destination zones."""
        try:
            package_info = create_package_from_task_event(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse task status for package handling: %s", exc)
            return

        if package_info is None:
            return

        self.handler.create_package(
            source_zone=package_info.source_zone,
            destination_zone=package_info.destination_zone,
            task_id=package_info.task_id,
            notes=package_info.notes,
        )
        rospy.loginfo("Prepared package for task: %s", format_package_summary(self.handler.get_current_package()))

    def handle_navigation_progress(self, msg: String) -> None:
        """Log readiness when the robot arrives at pickup or dropoff zones."""
        try:
            payload = safe_parse_navigation_progress_for_package(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse navigation progress for package handling: %s", exc)
            return

        current_package = self.handler.get_current_package()
        if current_package is None:
            return

        if payload.get("status") != NavigationStatus.ARRIVED.value:
            return

        current_zone = payload.get("current_zone")
        if current_zone is None:
            return

        if current_package.state == PackageState.WAITING_FOR_PICKUP and current_zone == current_package.source_zone.value:
            rospy.loginfo("Package pickup is ready at %s", current_zone)
        elif current_package.state == PackageState.CARRYING and current_zone == current_package.destination_zone.value:
            rospy.loginfo("Package dropoff is ready at %s", current_zone)


def main() -> None:
    """Run the package handler node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("package_handler")
    PackageHandlerNode()
    rospy.spin()


if __name__ == "__main__":
    main()
