"""Pure robot status aggregation and diagnostic logging services."""

from __future__ import annotations

from smart_warehouse_robot.common.constants import DEFAULT_ROBOT_NAME
from smart_warehouse_robot.common.helpers import (
    build_diagnostic_event,
    determine_health_level,
    parse_warehouse_zone,
)
from smart_warehouse_robot.common.models import (
    DiagnosticEvent,
    DiagnosticSource,
    NavigationStatus,
    PackageState,
    RobotHealthLevel,
    RobotMode,
    RobotStatusSnapshot,
    WarehouseZone,
)


class RobotStatusAggregator:
    """Track the latest robot state from task, navigation, safety, battery, and package events."""

    def __init__(
        self,
        robot_name: str = DEFAULT_ROBOT_NAME,
        start_zone: WarehouseZone = WarehouseZone.RECEIVING,
    ) -> None:
        self.robot_name = robot_name
        self.mode = RobotMode.IDLE
        self.current_zone = start_zone
        self.battery_percentage: float | None = None
        self.active_task_id: str | None = None
        self.active_navigation_goal_id: str | None = None
        self.package_id: str | None = None
        self.carrying_package = False
        self.emergency_stop_active = False
        self.navigation_blocked = False
        self.package_failed = False
        self.last_event: str | None = None

    def update_from_task_status(self, event: dict) -> None:
        event_type = str(event.get("event_type", "")).strip().lower()
        task_payload = event.get("task") if isinstance(event.get("task"), dict) else event
        task_id = task_payload.get("task_id") or event.get("task_id")
        if task_id is not None:
            task_id = str(task_id).strip() or None

        status_value = str(task_payload.get("status", event.get("status", ""))).strip().lower()
        if event_type == "task_started" or status_value == "in_progress":
            self.active_task_id = task_id
            self.mode = RobotMode.MOVING
        elif event_type == "task_completed" or status_value == "completed":
            self.active_task_id = None
            self.mode = RobotMode.IDLE
        elif event_type == "task_cancelled" or status_value == "cancelled":
            self.active_task_id = None
            self.mode = RobotMode.IDLE
        elif event_type == "task_failed" or status_value == "failed":
            self.active_task_id = task_id
            self.mode = RobotMode.ERROR

        self.last_event = event_type or status_value or self.last_event

    def update_from_navigation_progress(self, event: dict) -> None:
        current_zone = event.get("current_zone")
        if current_zone is not None:
            self.current_zone = parse_warehouse_zone(current_zone)

        goal_id = event.get("goal_id")
        if goal_id is not None:
            cleaned_goal_id = str(goal_id).strip()
            self.active_navigation_goal_id = cleaned_goal_id or None

        status = str(event.get("status", "")).strip().lower()
        if status == NavigationStatus.BLOCKED.value:
            self.navigation_blocked = True
            self.mode = RobotMode.ERROR
        elif status == NavigationStatus.MOVING.value:
            self.navigation_blocked = False
            self.mode = RobotMode.MOVING
        elif status == NavigationStatus.ARRIVED.value:
            self.navigation_blocked = False
            self.active_navigation_goal_id = None
            self.mode = RobotMode.IDLE

        self.last_event = event.get("message") or status or self.last_event

    def update_from_emergency_stop(self, event: dict) -> None:
        self.emergency_stop_active = bool(event.get("active", False))
        if self.emergency_stop_active:
            self.mode = RobotMode.ERROR
        self.last_event = event.get("reason") or self.last_event

    def update_from_battery_state(self, event: dict) -> None:
        percentage = event.get("percentage")
        self.battery_percentage = float(percentage) if percentage is not None else self.battery_percentage
        self.last_event = f"battery={self.battery_percentage:.1f}%" if self.battery_percentage is not None else self.last_event

    def update_from_package_status(self, event: dict) -> None:
        package_id = event.get("package_id")
        if package_id is not None:
            cleaned_package_id = str(package_id).strip()
            self.package_id = cleaned_package_id or None

        package_state = str(event.get("package_state", "")).strip().lower()
        self.carrying_package = package_state == PackageState.CARRYING.value
        self.package_failed = package_state == PackageState.FAILED.value

        if self.carrying_package:
            self.mode = RobotMode.LOADING
        elif package_state == PackageState.DELIVERED.value:
            self.mode = RobotMode.UNLOADING
        elif package_state == PackageState.NONE.value:
            self.package_id = None

        self.last_event = event.get("message") or self.last_event

    def get_snapshot(self) -> RobotStatusSnapshot:
        health_level = determine_health_level(
            emergency_stop_active=self.emergency_stop_active,
            battery_percentage=self.battery_percentage,
            navigation_blocked=self.navigation_blocked,
            package_failed=self.package_failed,
        )
        return RobotStatusSnapshot(
            robot_name=self.robot_name,
            health_level=health_level,
            mode=self.mode,
            current_zone=self.current_zone,
            battery_percentage=self.battery_percentage,
            active_task_id=self.active_task_id,
            active_navigation_goal_id=self.active_navigation_goal_id,
            package_id=self.package_id,
            carrying_package=self.carrying_package,
            emergency_stop_active=self.emergency_stop_active,
            last_event=self.last_event,
        )

    def summary(self) -> dict:
        snapshot = self.get_snapshot()
        return {
            "robot_name": snapshot.robot_name,
            "health_level": snapshot.health_level.value,
            "current_zone": snapshot.current_zone.value,
            "battery_percentage": snapshot.battery_percentage,
            "active_task_id": snapshot.active_task_id,
            "active_navigation_goal_id": snapshot.active_navigation_goal_id,
            "carrying_package": snapshot.carrying_package,
            "emergency_stop_active": snapshot.emergency_stop_active,
        }


class DiagnosticLogger:
    """Keep a bounded in-memory list of diagnostic events."""

    def __init__(self, robot_name: str = DEFAULT_ROBOT_NAME, max_events: int = 100) -> None:
        self.robot_name = robot_name
        self.max_events = max(1, int(max_events))
        self.events: list[DiagnosticEvent] = []

    def add_event(self, event: DiagnosticEvent) -> DiagnosticEvent:
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]
        return event

    def event_from_snapshot(self, snapshot: RobotStatusSnapshot) -> DiagnosticEvent:
        message = (
            f"Robot status is healthy in {snapshot.current_zone.value}."
            if snapshot.is_healthy()
            else f"Robot health is {snapshot.health_level.value}: {snapshot.last_event or 'status requires attention'}"
        )
        return build_diagnostic_event(
            source=DiagnosticSource.STATUS,
            health_level=snapshot.health_level,
            message=message,
            related_id=snapshot.active_task_id or snapshot.active_navigation_goal_id or snapshot.package_id,
            robot_name=snapshot.robot_name,
            topic="/warehouse/robot/status",
        )

    def list_events(
        self,
        source: DiagnosticSource | None = None,
        min_level: RobotHealthLevel | None = None,
    ) -> list[DiagnosticEvent]:
        filtered = list(self.events)
        if source is not None:
            filtered = [event for event in filtered if event.source == source]
        if min_level is not None:
            order = {
                RobotHealthLevel.UNKNOWN: 0,
                RobotHealthLevel.OK: 1,
                RobotHealthLevel.WARNING: 2,
                RobotHealthLevel.ERROR: 3,
                RobotHealthLevel.CRITICAL: 4,
            }
            filtered = [
                event for event in filtered if order[event.health_level] >= order[min_level]
            ]
        return filtered

    def latest_event(self) -> DiagnosticEvent | None:
        return self.events[-1] if self.events else None

    def summary(self) -> dict:
        latest = self.latest_event()
        return {
            "robot_name": self.robot_name,
            "total_events": len(self.events),
            "latest_level": latest.health_level.value if latest is not None else None,
            "latest_message": latest.message if latest is not None else None,
        }
