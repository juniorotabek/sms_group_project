"""ROS 1 node that animates the warehouse demo in RViz.

It listens to the existing task, navigation, and package topics, publishes a
moving TF for the robot base, and shows the package as an RViz marker that
moves from the source shelf to the destination shelf.
"""

from __future__ import annotations

import json
import math
from types import SimpleNamespace
from typing import Optional

from smart_warehouse_robot.common.constants import (
    DEFAULT_ROBOT_NAME,
    NAVIGATION_PROGRESS_TOPIC,
    PACKAGE_DROPOFF_SERVICE,
    PACKAGE_PICKUP_SERVICE,
    PACKAGE_RESET_SERVICE,
    PACKAGE_STATUS_TOPIC,
    PACKAGE_VISUALIZATION_TOPIC,
    TASK_STATUS_TOPIC,
    BATTERY_STATE_TOPIC,
    ROBOT_STATUS_TOPIC,
    WAREHOUSE_ZONE_COORDINATES,
)
from smart_warehouse_robot.common.helpers import clamp_progress, parse_package_state, parse_warehouse_zone
from smart_warehouse_robot.common.models import NavigationStatus, PackageInfo, PackageState, PackageStatusEvent, WarehouseZone

try:
    import rospy
    from std_msgs.msg import String
    from std_srvs.srv import Trigger
    from visualization_msgs.msg import Marker
    import tf
except ImportError:  # pragma: no cover - allows import in non-ROS environments
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data

    class Trigger:  # pragma: no cover
        pass

    class Marker:  # pragma: no cover
        CUBE = 1
        SPHERE = 2
        CYLINDER = 3
        ADD = 0
        DELETE = 2

        def __init__(self) -> None:
            self.header = SimpleNamespace(frame_id="", stamp=None)
            self.ns = ""
            self.id = 0
            self.type = self.CUBE
            self.action = self.ADD
            self.pose = SimpleNamespace(
                position=SimpleNamespace(x=0.0, y=0.0, z=0.0),
                orientation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
            )
            self.scale = SimpleNamespace(x=0.0, y=0.0, z=0.0)
            self.color = SimpleNamespace(r=0.0, g=0.0, b=0.0, a=0.0)
            self.lifetime = None

    class _TransformBroadcaster:  # pragma: no cover
        def sendTransform(self, *args, **kwargs) -> None:
            return None

    def _quaternion_from_euler(roll: float, pitch: float, yaw: float):  # pragma: no cover
        half_yaw = yaw * 0.5
        return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)

    tf = SimpleNamespace(TransformBroadcaster=_TransformBroadcaster, transformations=SimpleNamespace(quaternion_from_euler=_quaternion_from_euler))


def _zone_coordinates(zone: WarehouseZone | str) -> tuple[float, float]:
    parsed_zone = parse_warehouse_zone(zone)
    coordinates = WAREHOUSE_ZONE_COORDINATES[parsed_zone.value]
    return float(coordinates["x"]), float(coordinates["y"])


def _build_package_event_from_payload(payload: dict) -> PackageStatusEvent | None:
    package_state_value = payload.get("package_state")
    if package_state_value is None:
        return None

    package_id = payload.get("package_id")
    source_zone = payload.get("source_zone")
    destination_zone = payload.get("destination_zone")
    robot_name = payload.get("robot_name", DEFAULT_ROBOT_NAME)
    message = payload.get("message", "Package event.")

    if package_id is None or source_zone is None or destination_zone is None:
        return None

    return PackageStatusEvent(
        event_type=payload.get("event_type", "package_status"),
        package_id=package_id,
        package_state=package_state_value,
        robot_name=robot_name,
        message=message,
        task_id=payload.get("task_id"),
        source_zone=source_zone,
        destination_zone=destination_zone,
        timestamp=payload.get("timestamp"),
    )


class RVizDeliveryVisualizerNode:
    """Visualize the warehouse demo with a moving robot and package marker."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run RVizDeliveryVisualizerNode.")

        self.robot_name = str(rospy.get_param("~robot_name", DEFAULT_ROBOT_NAME))
        self.map_frame = str(rospy.get_param("~map_frame", "map"))
        self.base_frame = str(rospy.get_param("~base_frame", "base_link"))
        self.robot_height = float(rospy.get_param("~robot_height", 0.15))
        self.package_height = float(rospy.get_param("~package_height", 0.75))
        self.package_size = float(rospy.get_param("~package_size", 0.25))
        self.animation_rate_hz = float(rospy.get_param("~animation_rate_hz", 20.0))
        self.robot_speed_mps = float(rospy.get_param("~robot_speed_mps", 1.2))
        self.hud_offset_x = float(rospy.get_param("~hud_offset_x", 2.0))
        self.hud_offset_y = float(rospy.get_param("~hud_offset_y", 1.4))
        self.hud_offset_z = float(rospy.get_param("~hud_offset_z", -0.2))

        self.tf_broadcaster = tf.TransformBroadcaster()
        self.package_marker_publisher = rospy.Publisher(PACKAGE_VISUALIZATION_TOPIC, Marker, queue_size=10)
        self.hud_marker_publisher = rospy.Publisher("/warehouse/hud_text", Marker, queue_size=1)
        self.battery_subscriber = rospy.Subscriber(BATTERY_STATE_TOPIC, String, self.handle_battery_state, queue_size=5)
        self.robot_status_subscriber = rospy.Subscriber(ROBOT_STATUS_TOPIC, String, self.handle_robot_status, queue_size=5)
        self.camera_follower_publisher = rospy.Publisher("/warehouse/camera_follower", Marker, queue_size=10)
        self.task_subscriber = rospy.Subscriber(TASK_STATUS_TOPIC, String, self.handle_task_status, queue_size=10)
        self.progress_subscriber = rospy.Subscriber(
            NAVIGATION_PROGRESS_TOPIC, String, self.handle_navigation_progress, queue_size=10
        )
        self.package_subscriber = rospy.Subscriber(PACKAGE_STATUS_TOPIC, String, self.handle_package_status, queue_size=10)

        self.pickup_service = rospy.ServiceProxy(PACKAGE_PICKUP_SERVICE, Trigger)
        self.dropoff_service = rospy.ServiceProxy(PACKAGE_DROPOFF_SERVICE, Trigger)
        self.reset_service = rospy.ServiceProxy(PACKAGE_RESET_SERVICE, Trigger)

        self.active_task: dict | None = None
        self.active_task_id: str | None = None
        self.source_zone: WarehouseZone | None = None
        self.destination_zone: WarehouseZone | None = None
        self.current_package: PackageInfo | None = None
        self.current_package_state = PackageState.NONE
        self.robot_position = (0.0, 0.0, self.robot_height)
        self.robot_yaw = 0.0
        self.pickup_triggered = False
        self.dropoff_triggered = False
        self.package_marker_id = 1
        self.pickup_marker_id = 2
        self.dropoff_marker_id = 3
        self.route_phase = "idle"
        self.leg_progress_ratio = 0.0
        self.pickup_position_xy = (0.0, 0.0)
        self.dropoff_position_xy = (0.0, 0.0)
        self.leg_start_xy = (0.0, 0.0)
        self.leg_end_xy = (0.0, 0.0)
        self.has_started = False  # Track if robot has ever moved; prevents spawn-from-nowhere
        self.robot_depot_xy = (-3.0, 0.0)  # Robot starts at depot (offscreen), distinct from pickup
        self.latest_battery_percent: float | None = None
        self.latest_robot_status: dict | None = None
        self.latest_progress_percent: float = 0.0

        self.animation_timer = rospy.Timer(rospy.Duration(1.0 / max(self.animation_rate_hz, 1.0)), self.handle_animation_tick)

        rospy.loginfo("RVizDeliveryVisualizerNode started. Publishing to %s", PACKAGE_VISUALIZATION_TOPIC)

    def handle_task_status(self, msg: String) -> None:
        """Track the active task and reset the pickup/dropoff flow."""
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            rospy.logerr("Failed to parse task status for visualization: %s", exc.msg)
            return
        if not isinstance(payload, dict):
            rospy.logerr("Failed to parse task status for visualization: expected a JSON object.")
            return

        if payload.get("event_type") != "task_started":
            if payload.get("event_type") == "task_completed" and payload.get("task_id") == self.active_task_id:
                self.active_task = None
                self.active_task_id = None
                self.source_zone = None
                self.destination_zone = None
                self.pickup_triggered = False
                self.dropoff_triggered = False
            return

        task_payload = payload.get("task") if isinstance(payload.get("task"), dict) else payload
        try:
            self.active_task_id = str(task_payload["task_id"])
            self.source_zone = parse_warehouse_zone(task_payload["source_zone"])
            self.destination_zone = parse_warehouse_zone(task_payload["destination_zone"])
        except (KeyError, ValueError) as exc:
            rospy.logerr("Task status event is missing required data for RViz visualization: %s", exc)
            return

        self.active_task = task_payload
        self.current_package = PackageInfo(
            package_id=str(task_payload.get("task_id") or "PKG-DEMO"),
            source_zone=self.source_zone,
            destination_zone=self.destination_zone,
            state=PackageState.WAITING_FOR_PICKUP,
            task_id=task_payload.get("task_id"),
            notes=f"Visual package for task {task_payload.get('task_id')}",
        )
        self.current_package_state = PackageState.WAITING_FOR_PICKUP
        self.pickup_triggered = False
        self.dropoff_triggered = False
        self.pickup_position_xy = _zone_coordinates(self.source_zone)
        self.dropoff_position_xy = _zone_coordinates(self.destination_zone)
        
        # If this is the first task, start from depot; otherwise continue from current position
        if not self.has_started:
            self.robot_position = (self.robot_depot_xy[0], self.robot_depot_xy[1], self.robot_height)
            self.has_started = True
        
        self.leg_start_xy = (self.robot_position[0], self.robot_position[1])
        self.leg_end_xy = self.pickup_position_xy
        self.leg_progress_ratio = 0.0
        self.route_phase = "to_pickup"
        self.robot_yaw = math.atan2(
            self.leg_end_xy[1] - self.leg_start_xy[1],
            self.leg_end_xy[0] - self.leg_start_xy[0],
        )
        self.publish_robot_transform()
        self.publish_location_markers()
        self.publish_package_marker()
        rospy.loginfo(
            "Visualizing task %s from %s to %s",
            self.active_task_id,
            self.source_zone.value,
            self.destination_zone.value,
        )

    def handle_navigation_progress(self, msg: String) -> None:
        """Track progress updates for observability while animation runs locally."""
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            rospy.logerr("Failed to parse navigation progress for visualization: %s", exc.msg)
            return
        if not isinstance(payload, dict):
            rospy.logerr("Failed to parse navigation progress for visualization: expected a JSON object.")
            return

        if self.source_zone is None or self.destination_zone is None:
            return

        self.latest_progress_percent = float(clamp_progress(payload.get("progress_percent", 0.0)))

        self.publish_package_marker()
        self.publish_hud_marker()

    def handle_animation_tick(self, event) -> None:
        """Advance robot pose smoothly toward target progress and keep RViz visuals refreshed."""
        if self.source_zone is None or self.destination_zone is None:
            # Keep TF alive from startup so map->base_link->wheels always resolves in RViz.
            self.publish_robot_transform()
            self.publish_location_markers()
            self.publish_package_marker()
            self.publish_camera_follower_marker()
            return

        start_x, start_y = self.leg_start_xy
        end_x, end_y = self.leg_end_xy
        leg_distance = math.hypot(end_x - start_x, end_y - start_y)
        dt = max((event.current_real - event.last_real).to_sec(), 0.0) if event.last_real else 0.0

        if leg_distance > 1e-6:
            max_ratio_step = (self.robot_speed_mps * dt) / leg_distance
            self.leg_progress_ratio = min(1.0, self.leg_progress_ratio + max_ratio_step)
        else:
            self.leg_progress_ratio = 1.0

        x_position = start_x + (end_x - start_x) * self.leg_progress_ratio
        y_position = start_y + (end_y - start_y) * self.leg_progress_ratio
        self.robot_position = (x_position, y_position, self.robot_height)
        self.robot_yaw = math.atan2(end_y - start_y, end_x - start_x) if leg_distance > 1e-6 else self.robot_yaw

        if self.leg_progress_ratio >= 0.999:
            self.handle_leg_arrival()

        self.publish_robot_transform()
        self.publish_location_markers()
        self.publish_package_marker()
        self.publish_hud_marker()

    def handle_battery_state(self, msg: String) -> None:
        """Parse battery JSON state and remember percentage for HUD."""
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        try:
            self.latest_battery_percent = float(payload.get("percentage", payload.get("level", 0.0)))
        except Exception:
            self.latest_battery_percent = None
        self.publish_hud_marker()

    def handle_robot_status(self, msg: String) -> None:
        """Store latest robot status for HUD display."""
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        self.latest_robot_status = payload
        self.publish_hud_marker()

    def publish_hud_marker(self) -> None:
        """Publish a text marker that summarizes key telemetry for easy viewing in RViz.

        The marker is published in the `camera_target` frame so it stays visible in the camera-centered view.
        """
        try:
            marker = Marker()
            marker.header.stamp = rospy.Time.now()
            marker.header.frame_id = "camera_target"
            marker.ns = "hud"
            marker.id = 99
            marker.type = Marker.TEXT_VIEW_FACING
            marker.action = Marker.ADD
            marker.pose.position.x = self.hud_offset_x
            marker.pose.position.y = self.hud_offset_y
            marker.pose.position.z = self.hud_offset_z
            marker.pose.orientation.w = 1.0
            marker.scale.z = 0.35
            marker.color.r = 1.0
            marker.color.g = 1.0
            marker.color.b = 1.0
            marker.color.a = 1.0

            lines = []
            if self.latest_battery_percent is not None:
                lines.append(f"Battery: {self.latest_battery_percent:.0f}%")
            else:
                lines.append("Battery: N/A")

            task_desc = "idle"
            if self.active_task is not None:
                try:
                    src = self.active_task.get("source_zone") or self.active_task.get("source")
                    dst = self.active_task.get("destination_zone") or self.active_task.get("destination")
                    task_desc = f"Task: {self.active_task.get('task_type','task')} {src}->{dst}"
                except Exception:
                    task_desc = "Task: active"
            lines.append(task_desc)

            lines.append(f"Progress: {int(self.latest_progress_percent)}%")

            if self.current_package is not None:
                pkg_state = getattr(self.current_package, 'state', None)
                if pkg_state is not None and getattr(pkg_state, 'value', None) is not None:
                    lines.append(f"Package: {pkg_state.value}")
                else:
                    lines.append("Package: N/A")

            marker.text = "\n".join(lines)
            self.hud_marker_publisher.publish(marker)
        except Exception:
            return
        self.publish_camera_follower_marker()

    def handle_leg_arrival(self) -> None:
        """Handle reaching pickup/dropoff points and chain the next leg."""
        if self.route_phase == "to_pickup":
            if not self.pickup_triggered:
                self.call_pickup_service()
            self.pickup_triggered = True
            self.route_phase = "to_dropoff"
            self.leg_start_xy = self.pickup_position_xy
            self.leg_end_xy = self.dropoff_position_xy
            self.leg_progress_ratio = 0.0
            return

        if self.route_phase == "to_dropoff":
            if not self.dropoff_triggered and self.current_package_state in (PackageState.CARRYING, PackageState.WAITING_FOR_PICKUP):
                self.call_dropoff_service()
            self.dropoff_triggered = True
            self.route_phase = "idle"
            self.leg_start_xy = self.dropoff_position_xy
            self.leg_end_xy = self.dropoff_position_xy
            self.leg_progress_ratio = 1.0

    def handle_package_status(self, msg: String) -> None:
        """Update the rendered package state from package handler events."""
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            rospy.logerr("Failed to parse package status for visualization: %s", exc.msg)
            return
        if not isinstance(payload, dict):
            rospy.logerr("Failed to parse package status for visualization: expected a JSON object.")
            return

        event = _build_package_event_from_payload(payload)
        if event is None:
            return

        self.current_package_state = event.package_state
        self.current_package = PackageInfo(
            package_id=event.package_id or "",
            source_zone=event.source_zone or self.source_zone or WarehouseZone.RECEIVING,
            destination_zone=event.destination_zone or self.destination_zone or WarehouseZone.SHIPPING,
            state=event.package_state,
            carried_by=event.robot_name if event.package_state == PackageState.CARRYING else None,
            task_id=event.task_id,
            notes=event.message,
            timestamp=event.timestamp,
        )

        if self.current_package_state == PackageState.CARRYING:
            self.pickup_triggered = True
            self.route_phase = "to_dropoff"
            self.leg_start_xy = (self.robot_position[0], self.robot_position[1])
            self.leg_end_xy = self.dropoff_position_xy
            self.leg_progress_ratio = 0.0
        elif self.current_package_state == PackageState.DELIVERED:
            self.dropoff_triggered = True
            self.route_phase = "idle"
            self.leg_start_xy = self.dropoff_position_xy
            self.leg_end_xy = self.dropoff_position_xy
            self.leg_progress_ratio = 1.0

        self.publish_package_marker()

    def call_pickup_service(self) -> None:
        """Ask the existing package handler to perform pickup."""
        try:
            response = self.pickup_service()
            if getattr(response, "success", False):
                self.pickup_triggered = True
                rospy.loginfo("Triggered package pickup for task %s", self.active_task_id)
            else:
                rospy.logwarn("Package pickup service returned failure: %s", getattr(response, "message", ""))
        except Exception as exc:  # pragma: no cover - ROS service availability/runtime issues
            rospy.logwarn("Package pickup service call failed: %s", exc)

    def call_dropoff_service(self) -> None:
        """Ask the existing package handler to perform dropoff."""
        try:
            response = self.dropoff_service()
            if getattr(response, "success", False):
                self.dropoff_triggered = True
                rospy.loginfo("Triggered package dropoff for task %s", self.active_task_id)
            else:
                rospy.logwarn("Package dropoff service returned failure: %s", getattr(response, "message", ""))
        except Exception as exc:  # pragma: no cover - ROS service availability/runtime issues
            rospy.logwarn("Package dropoff service call failed: %s", exc)

    def publish_robot_transform(self) -> None:
        """Publish the robot's pose as a dynamic TF from map -> base_link."""
        x_position, y_position, z_position = self.robot_position
        quaternion = tf.transformations.quaternion_from_euler(0.0, 0.0, self.robot_yaw)
        self.tf_broadcaster.sendTransform(
            (x_position, y_position, z_position),
            quaternion,
            rospy.Time.now(),
            self.base_frame,
            self.map_frame,
        )
        
        # Publish camera_target frame for RViz camera following
        camera_offset_x = -2.5
        camera_offset_z = 3.5
        camera_x = x_position + camera_offset_x * math.cos(self.robot_yaw)
        camera_y = y_position + camera_offset_x * math.sin(self.robot_yaw)
        camera_quaternion = tf.transformations.quaternion_from_euler(0.0, 0.0, 0.0)
        self.tf_broadcaster.sendTransform(
            (camera_x, camera_y, z_position + camera_offset_z),
            camera_quaternion,
            rospy.Time.now(),
            "camera_target",
            self.map_frame,
        )

    def publish_package_marker(self) -> None:
        """Publish a package marker that follows the package state."""
        marker = Marker()
        marker.header.stamp = rospy.Time.now()
        marker.ns = "warehouse_package"
        marker.id = self.package_marker_id
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.scale.x = self.package_size
        marker.scale.y = self.package_size
        marker.scale.z = self.package_size

        if self.current_package is None:
            marker.action = Marker.DELETE
            marker.header.frame_id = self.map_frame
            self.package_marker_publisher.publish(marker)
            return

        if self.current_package_state == PackageState.CARRYING:
            marker.header.frame_id = self.base_frame
            marker.pose.position.x = 0.12
            marker.pose.position.y = 0.0
            marker.pose.position.z = self.package_height
            marker.pose.orientation.w = 1.0
            marker.color.r = 0.20
            marker.color.g = 0.70
            marker.color.b = 1.00
            marker.color.a = 1.0
        else:
            marker.header.frame_id = self.map_frame
            if self.current_package_state == PackageState.DELIVERED and self.destination_zone is not None:
                marker_x, marker_y = _zone_coordinates(self.destination_zone)
                marker.color.r = 0.20
                marker.color.g = 0.85
                marker.color.b = 0.20
            else:
                marker_x, marker_y = _zone_coordinates(self.current_package.source_zone)
                marker.color.r = 0.95
                marker.color.g = 0.65
                marker.color.b = 0.10
            marker.pose.position.x = marker_x
            marker.pose.position.y = marker_y
            marker.pose.position.z = self.package_height
            marker.pose.orientation.w = 1.0
            marker.color.a = 1.0

        self.package_marker_publisher.publish(marker)

    def publish_location_markers(self) -> None:
        """Publish distinct pickup and dropoff location markers."""
        pickup_marker = Marker()
        pickup_marker.header.stamp = rospy.Time.now()
        pickup_marker.ns = "warehouse_locations"
        pickup_marker.id = self.pickup_marker_id
        pickup_marker.type = Marker.CYLINDER
        pickup_marker.scale.x = 0.45
        pickup_marker.scale.y = 0.45
        pickup_marker.scale.z = 0.03
        pickup_marker.pose.orientation.w = 1.0
        pickup_marker.color.r = 0.95
        pickup_marker.color.g = 0.55
        pickup_marker.color.b = 0.10
        pickup_marker.color.a = 0.95

        dropoff_marker = Marker()
        dropoff_marker.header.stamp = rospy.Time.now()
        dropoff_marker.ns = "warehouse_locations"
        dropoff_marker.id = self.dropoff_marker_id
        dropoff_marker.type = Marker.SPHERE
        dropoff_marker.scale.x = 0.35
        dropoff_marker.scale.y = 0.35
        dropoff_marker.scale.z = 0.35
        dropoff_marker.pose.orientation.w = 1.0
        dropoff_marker.color.r = 0.10
        dropoff_marker.color.g = 0.90
        dropoff_marker.color.b = 0.30
        dropoff_marker.color.a = 0.95

        if self.source_zone is None or self.destination_zone is None:
            pickup_marker.action = Marker.DELETE
            dropoff_marker.action = Marker.DELETE
            pickup_marker.header.frame_id = self.map_frame
            dropoff_marker.header.frame_id = self.map_frame
            self.package_marker_publisher.publish(pickup_marker)
            self.package_marker_publisher.publish(dropoff_marker)
            return

        pickup_x, pickup_y = _zone_coordinates(self.source_zone)
        dropoff_x, dropoff_y = _zone_coordinates(self.destination_zone)

        pickup_marker.action = Marker.ADD
        pickup_marker.header.frame_id = self.map_frame
        pickup_marker.pose.position.x = pickup_x
        pickup_marker.pose.position.y = pickup_y
        pickup_marker.pose.position.z = 0.015

        dropoff_marker.action = Marker.ADD
        dropoff_marker.header.frame_id = self.map_frame
        dropoff_marker.pose.position.x = dropoff_x
        dropoff_marker.pose.position.y = dropoff_y
        dropoff_marker.pose.position.z = 0.18

        self.package_marker_publisher.publish(pickup_marker)
        self.package_marker_publisher.publish(dropoff_marker)

    def publish_camera_follower_marker(self) -> None:
        """Publish a marker at robot position for camera following (RViz can track this)."""
        marker = Marker()
        marker.header.stamp = rospy.Time.now()
        marker.header.frame_id = self.map_frame
        marker.ns = "camera_follower"
        marker.id = 1
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x, marker.pose.position.y, _ = self.robot_position
        marker.pose.position.z = self.robot_height + 1.5  # Slightly above robot for better view
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.05
        marker.scale.y = 0.05
        marker.scale.z = 0.05
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 0.3  # Invisible, but RViz can track it
        marker.lifetime = rospy.Duration(0.5)
        self.camera_follower_publisher.publish(marker)


def main() -> None:
    """Run the RViz delivery visualizer node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("rviz_delivery_visualizer")
    RVizDeliveryVisualizerNode()
    rospy.spin()


if __name__ == "__main__":
    main()
