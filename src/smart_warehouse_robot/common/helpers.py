"""Pure helper functions that are easy to test without ROS."""

from __future__ import annotations

import math
from typing import Iterable
from uuid import uuid4


def create_task_id(prefix: str = "TASK") -> str:
    """Create a readable unique task identifier."""
    safe_prefix = prefix.strip().upper() or "TASK"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_goal_id(prefix: str = "GOAL") -> str:
    """Create a readable unique navigation goal identifier."""
    safe_prefix = prefix.strip().upper() or "GOAL"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_reading_id(prefix: str = "OBS") -> str:
    """Create a readable unique obstacle reading identifier."""
    safe_prefix = prefix.strip().upper() or "OBS"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_emergency_command_id(prefix: str = "ESTOP") -> str:
    """Create a readable unique emergency-stop command identifier."""
    safe_prefix = prefix.strip().upper() or "ESTOP"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_battery_id(prefix: str = "BAT") -> str:
    """Create a readable unique battery identifier."""
    safe_prefix = prefix.strip().upper() or "BAT"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_charge_command_id(prefix: str = "CHARGE") -> str:
    """Create a readable unique charge command identifier."""
    safe_prefix = prefix.strip().upper() or "CHARGE"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_package_id(prefix: str = "PKG") -> str:
    """Create a readable unique package identifier."""
    safe_prefix = prefix.strip().upper() or "PKG"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_package_event_id(prefix: str = "PKG_EVT") -> str:
    """Create a readable unique package event identifier."""
    safe_prefix = prefix.strip().upper() or "PKG_EVT"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def create_diagnostic_id(prefix: str = "DIAG") -> str:
    """Create a readable unique diagnostic identifier."""
    safe_prefix = prefix.strip().upper() or "DIAG"
    return f"{safe_prefix}-{uuid4().hex[:8].upper()}"


def parse_task_type(value: str):
    """Normalize user input into a TaskType enum."""
    from smart_warehouse_robot.common.models import TaskType

    if isinstance(value, TaskType):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "pickup": TaskType.PICKUP,
        "dropoff": TaskType.DROPOFF,
        "move": TaskType.MOVE,
        "charge": TaskType.CHARGE,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_types = ", ".join(task_type.value for task_type in TaskType)
        raise ValueError(f"Invalid task type '{value}'. Expected one of: {valid_types}.") from exc


def parse_task_status(value: str):
    """Normalize user input into a TaskStatus enum."""
    from smart_warehouse_robot.common.models import TaskStatus

    if isinstance(value, TaskStatus):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "created": TaskStatus.CREATED,
        "queued": TaskStatus.QUEUED,
        "in_progress": TaskStatus.IN_PROGRESS,
        "completed": TaskStatus.COMPLETED,
        "cancelled": TaskStatus.CANCELLED,
        "failed": TaskStatus.FAILED,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_statuses = ", ".join(status.value for status in TaskStatus)
        raise ValueError(f"Invalid task status '{value}'. Expected one of: {valid_statuses}.") from exc


def parse_robot_mode(value: str):
    """Normalize user input into a RobotMode enum."""
    from smart_warehouse_robot.common.models import RobotMode

    if isinstance(value, RobotMode):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "idle": RobotMode.IDLE,
        "moving": RobotMode.MOVING,
        "loading": RobotMode.LOADING,
        "unloading": RobotMode.UNLOADING,
        "charging": RobotMode.CHARGING,
        "error": RobotMode.ERROR,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_modes = ", ".join(mode.value for mode in RobotMode)
        raise ValueError(f"Invalid robot mode '{value}'. Expected one of: {valid_modes}.") from exc


def parse_navigation_status(value: str):
    """Normalize user input into a NavigationStatus enum."""
    from smart_warehouse_robot.common.models import NavigationStatus

    if isinstance(value, NavigationStatus):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "idle": NavigationStatus.IDLE,
        "goal_received": NavigationStatus.GOAL_RECEIVED,
        "moving": NavigationStatus.MOVING,
        "arrived": NavigationStatus.ARRIVED,
        "blocked": NavigationStatus.BLOCKED,
        "cancelled": NavigationStatus.CANCELLED,
        "failed": NavigationStatus.FAILED,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_statuses = ", ".join(status.value for status in NavigationStatus)
        raise ValueError(f"Invalid navigation status '{value}'. Expected one of: {valid_statuses}.") from exc


def parse_obstacle_severity(value: str):
    """Normalize user input into an ObstacleSeverity enum."""
    from smart_warehouse_robot.common.models import ObstacleSeverity

    if isinstance(value, ObstacleSeverity):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "clear": ObstacleSeverity.CLEAR,
        "low": ObstacleSeverity.LOW,
        "medium": ObstacleSeverity.MEDIUM,
        "high": ObstacleSeverity.HIGH,
        "critical": ObstacleSeverity.CRITICAL,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in ObstacleSeverity)
        raise ValueError(f"Invalid obstacle severity '{value}'. Expected one of: {valid_values}.") from exc


def parse_safety_state(value: str):
    """Normalize user input into a SafetyState enum."""
    from smart_warehouse_robot.common.models import SafetyState

    if isinstance(value, SafetyState):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "safe": SafetyState.SAFE,
        "warning": SafetyState.WARNING,
        "stop_required": SafetyState.STOP_REQUIRED,
        "emergency_stopped": SafetyState.EMERGENCY_STOPPED,
        "recovering": SafetyState.RECOVERING,
        "fault": SafetyState.FAULT,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in SafetyState)
        raise ValueError(f"Invalid safety state '{value}'. Expected one of: {valid_values}.") from exc


def parse_battery_level(value: str):
    """Normalize user input into a BatteryLevel enum."""
    from smart_warehouse_robot.common.models import BatteryLevel

    if isinstance(value, BatteryLevel):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "full": BatteryLevel.FULL,
        "normal": BatteryLevel.NORMAL,
        "low": BatteryLevel.LOW,
        "critical": BatteryLevel.CRITICAL,
        "empty": BatteryLevel.EMPTY,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in BatteryLevel)
        raise ValueError(f"Invalid battery level '{value}'. Expected one of: {valid_values}.") from exc


def parse_charging_status(value: str):
    """Normalize user input into a ChargingStatus enum."""
    from smart_warehouse_robot.common.models import ChargingStatus

    if isinstance(value, ChargingStatus):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "not_charging": ChargingStatus.NOT_CHARGING,
        "returning_to_charge": ChargingStatus.RETURNING_TO_CHARGE,
        "charging": ChargingStatus.CHARGING,
        "charged": ChargingStatus.CHARGED,
        "charging_fault": ChargingStatus.CHARGING_FAULT,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in ChargingStatus)
        raise ValueError(f"Invalid charging status '{value}'. Expected one of: {valid_values}.") from exc


def parse_package_state(value: str):
    """Normalize user input into a PackageState enum."""
    from smart_warehouse_robot.common.models import PackageState

    if isinstance(value, PackageState):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "none": PackageState.NONE,
        "waiting_for_pickup": PackageState.WAITING_FOR_PICKUP,
        "carrying": PackageState.CARRYING,
        "delivered": PackageState.DELIVERED,
        "dropped": PackageState.DROPPED,
        "failed": PackageState.FAILED,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in PackageState)
        raise ValueError(f"Invalid package state '{value}'. Expected one of: {valid_values}.") from exc


def parse_package_action(value: str):
    """Normalize user input into a PackageAction enum."""
    from smart_warehouse_robot.common.models import PackageAction

    if isinstance(value, PackageAction):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "pickup": PackageAction.PICKUP,
        "dropoff": PackageAction.DROPOFF,
        "reset": PackageAction.RESET,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in PackageAction)
        raise ValueError(f"Invalid package action '{value}'. Expected one of: {valid_values}.") from exc


def parse_robot_health_level(value: str):
    """Normalize user input into a RobotHealthLevel enum."""
    from smart_warehouse_robot.common.models import RobotHealthLevel

    if isinstance(value, RobotHealthLevel):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "ok": RobotHealthLevel.OK,
        "warning": RobotHealthLevel.WARNING,
        "error": RobotHealthLevel.ERROR,
        "critical": RobotHealthLevel.CRITICAL,
        "unknown": RobotHealthLevel.UNKNOWN,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in RobotHealthLevel)
        raise ValueError(f"Invalid robot health level '{value}'. Expected one of: {valid_values}.") from exc


def parse_diagnostic_source(value: str):
    """Normalize user input into a DiagnosticSource enum."""
    from smart_warehouse_robot.common.models import DiagnosticSource

    if isinstance(value, DiagnosticSource):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "task": DiagnosticSource.TASK,
        "navigation": DiagnosticSource.NAVIGATION,
        "safety": DiagnosticSource.SAFETY,
        "battery": DiagnosticSource.BATTERY,
        "package": DiagnosticSource.PACKAGE,
        "status": DiagnosticSource.STATUS,
        "system": DiagnosticSource.SYSTEM,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_values = ", ".join(item.value for item in DiagnosticSource)
        raise ValueError(f"Invalid diagnostic source '{value}'. Expected one of: {valid_values}.") from exc


def parse_warehouse_zone(value: str):
    """Normalize user input into a WarehouseZone enum."""
    from smart_warehouse_robot.common.models import WarehouseZone

    if isinstance(value, WarehouseZone):
        return value

    normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "receiving": WarehouseZone.RECEIVING,
        "storage_a": WarehouseZone.STORAGE_A,
        "storage_b": WarehouseZone.STORAGE_B,
        "packing": WarehouseZone.PACKING,
        "shipping": WarehouseZone.SHIPPING,
        "charging_station": WarehouseZone.CHARGING_STATION,
        "parking_a": WarehouseZone.PARKING_A,
        "parking_b": WarehouseZone.PARKING_B,
        "parking_c": WarehouseZone.PARKING_C,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        valid_zones = ", ".join(zone.value for zone in WarehouseZone)
        raise ValueError(f"Invalid warehouse zone '{value}'. Expected one of: {valid_zones}.") from exc


def validate_zone(zone_name: str) -> bool:
    """Return True when the provided zone name matches a known warehouse zone."""
    try:
        parse_warehouse_zone(zone_name)
    except ValueError:
        return False
    return True


def clamp_priority(priority: int, minimum: int = 1, maximum: int = 5) -> int:
    """Keep priority values inside a beginner-friendly range."""
    return max(minimum, min(maximum, int(priority)))


def clamp_progress(progress: float) -> float:
    """Keep progress between 0 and 100 percent."""
    return max(0.0, min(100.0, float(progress)))


def clamp_percentage(percentage: float) -> float:
    """Keep percentages between 0 and 100."""
    return max(0.0, min(100.0, float(percentage)))


def classify_obstacle_severity(distance_meters: float, detected: bool):
    """Classify obstacle severity from distance and detection state."""
    from smart_warehouse_robot.common.models import ObstacleSeverity

    distance = max(0.0, float(distance_meters))
    if not detected:
        return ObstacleSeverity.CLEAR
    if distance <= 0.4:
        return ObstacleSeverity.CRITICAL
    if distance <= 1.0:
        return ObstacleSeverity.HIGH
    if distance <= 2.0:
        return ObstacleSeverity.MEDIUM
    if distance <= 4.0:
        return ObstacleSeverity.LOW
    return ObstacleSeverity.CLEAR


def classify_battery_level(percentage: float):
    """Classify battery level from percentage."""
    from smart_warehouse_robot.common.models import BatteryLevel

    value = clamp_percentage(percentage)
    if value >= 80.0:
        return BatteryLevel.FULL
    if value >= 30.0:
        return BatteryLevel.NORMAL
    if value >= 15.0:
        return BatteryLevel.LOW
    if value > 0.0:
        return BatteryLevel.CRITICAL
    return BatteryLevel.EMPTY


def build_task_json(task_type, source, destination, priority, notes=None) -> str:
    """Create a WarehouseTask and return stable JSON."""
    from smart_warehouse_robot.common.models import WarehouseTask

    task = WarehouseTask(
        task_type=task_type,
        source_zone=source,
        destination_zone=destination,
        priority=priority,
        notes=notes,
    )
    return task.to_json()


def build_navigation_goal_from_task_json(task_json: str):
    """Build a navigation goal from a warehouse task JSON payload."""
    from smart_warehouse_robot.common.models import NavigationGoal, WarehouseTask

    task = WarehouseTask.from_json(task_json)
    return NavigationGoal(
        task_id=task.task_id,
        source_zone=task.source_zone,
        destination_zone=task.destination_zone,
        priority=task.priority,
    )


def build_obstacle_reading(zone, distance_meters, detected, description=None):
    """Create an obstacle reading from simple CLI or node inputs."""
    from smart_warehouse_robot.common.models import ObstacleReading

    severity = classify_obstacle_severity(distance_meters, detected)
    return ObstacleReading(
        zone=zone,
        distance_meters=distance_meters,
        severity=severity,
        obstacle_detected=detected,
        description=description,
    )


def should_trigger_emergency_stop(reading) -> bool:
    """Return True when the reading requires an emergency stop."""
    from smart_warehouse_robot.common.models import ObstacleSeverity

    return reading.severity in {ObstacleSeverity.HIGH, ObstacleSeverity.CRITICAL}


def build_emergency_stop_command(reading, reason=None):
    """Create an emergency stop command from an obstacle reading."""
    from smart_warehouse_robot.common.models import EmergencyStopCommand, SafetyState

    command_reason = reason or f"Obstacle severity {reading.severity.value} detected in {reading.zone.value}"
    return EmergencyStopCommand(
        active=should_trigger_emergency_stop(reading),
        reason=command_reason,
        safety_state=SafetyState.EMERGENCY_STOPPED if should_trigger_emergency_stop(reading) else SafetyState.WARNING,
        source_reading_id=reading.reading_id,
        zone=reading.zone,
    )


def should_return_to_charge(percentage: float, low_threshold: float = 25.0) -> bool:
    """Return True when battery is at or below the low threshold."""
    return clamp_percentage(percentage) <= float(low_threshold)


def should_emergency_stop_for_battery(percentage: float, critical_threshold: float = 10.0) -> bool:
    """Return True when battery is at or below the critical threshold."""
    return clamp_percentage(percentage) <= float(critical_threshold)


def build_battery_state(robot_name, percentage, current_zone, charging_status="not_charging"):
    """Create a battery state from simple inputs."""
    from smart_warehouse_robot.common.models import BatteryState

    return BatteryState(
        robot_name=robot_name,
        percentage=percentage,
        charging_status=charging_status,
        current_zone=current_zone,
    )


def build_charge_command(battery_state, reason=None):
    """Create a return-to-charge command from a battery state."""
    from smart_warehouse_robot.common.constants import CHARGING_STATION_ZONE
    from smart_warehouse_robot.common.models import ChargeCommand, ChargingStatus

    command_reason = reason or f"Low battery detected at {battery_state.percentage:.1f}%"
    return ChargeCommand(
        robot_name=battery_state.robot_name,
        active=True,
        reason=command_reason,
        target_zone=CHARGING_STATION_ZONE,
        battery_percentage=battery_state.percentage,
        charging_status=ChargingStatus.RETURNING_TO_CHARGE,
        source_battery_id=battery_state.battery_id,
        current_zone=battery_state.current_zone,
    )


def build_charge_navigation_goal(command):
    """Create a high-priority navigation goal toward the charging station."""
    from smart_warehouse_robot.common.constants import CHARGING_STATION_ZONE
    from smart_warehouse_robot.common.models import NavigationGoal, WarehouseZone

    source_zone = getattr(command, "current_zone", None) or WarehouseZone.RECEIVING
    return NavigationGoal(
        goal_id=create_goal_id(),
        task_id=command.command_id,
        source_zone=source_zone,
        destination_zone=CHARGING_STATION_ZONE,
        priority=5,
    )


def build_package_info(package_id, source_zone, destination_zone, task_id=None, notes=None):
    """Create package information for pickup/dropoff simulation."""
    from smart_warehouse_robot.common.models import PackageInfo, PackageState

    package = PackageInfo(
        package_id=package_id or create_package_id(),
        source_zone=source_zone,
        destination_zone=destination_zone,
        state=PackageState.NONE,
        task_id=task_id,
        notes=notes,
    )
    package.mark_waiting()
    return package


def build_package_status_event(event_type: str, package_info, robot_name: str, message: str):
    """Create a package status event for the package status topic."""
    from smart_warehouse_robot.common.models import PackageState, PackageStatusEvent

    return PackageStatusEvent(
        event_type=event_type,
        package_id=package_info.package_id if package_info is not None else None,
        package_state=package_info.state if package_info is not None else PackageState.NONE,
        robot_name=robot_name,
        message=message,
        task_id=package_info.task_id if package_info is not None else None,
        source_zone=package_info.source_zone if package_info is not None else None,
        destination_zone=package_info.destination_zone if package_info is not None else None,
    )


def determine_health_level(
    emergency_stop_active: bool = False,
    battery_percentage: float | None = None,
    navigation_blocked: bool = False,
    package_failed: bool = False,
):
    """Determine a combined health level from major robot state flags."""
    from smart_warehouse_robot.common.models import RobotHealthLevel

    if emergency_stop_active:
        return RobotHealthLevel.CRITICAL

    if battery_percentage is not None:
        battery_value = clamp_percentage(battery_percentage)
        if battery_value <= 10.0:
            return RobotHealthLevel.CRITICAL
        if battery_value <= 25.0:
            return RobotHealthLevel.WARNING

    if package_failed:
        return RobotHealthLevel.ERROR

    if navigation_blocked:
        return RobotHealthLevel.WARNING

    return RobotHealthLevel.OK


def build_robot_status_snapshot(
    robot_name: str,
    current_zone,
    mode,
    battery_percentage: float | None = None,
    active_task_id: str | None = None,
    active_navigation_goal_id: str | None = None,
    package_id: str | None = None,
    carrying_package: bool = False,
    emergency_stop_active: bool = False,
    last_event: str | None = None,
):
    """Create a robot status snapshot from simple inputs."""
    from smart_warehouse_robot.common.models import RobotStatusSnapshot

    health_level = determine_health_level(
        emergency_stop_active=emergency_stop_active,
        battery_percentage=battery_percentage,
    )
    return RobotStatusSnapshot(
        robot_name=robot_name,
        health_level=health_level,
        mode=mode,
        current_zone=current_zone,
        battery_percentage=battery_percentage,
        active_task_id=active_task_id,
        active_navigation_goal_id=active_navigation_goal_id,
        package_id=package_id,
        carrying_package=carrying_package,
        emergency_stop_active=emergency_stop_active,
        last_event=last_event,
    )


def build_diagnostic_event(
    source,
    health_level,
    message: str,
    related_id: str | None = None,
    robot_name: str | None = None,
    topic: str | None = None,
):
    """Create a diagnostic event from simple CLI or service inputs."""
    from smart_warehouse_robot.common.models import DiagnosticEvent

    return DiagnosticEvent(
        source=source,
        health_level=health_level,
        message=message,
        related_id=related_id,
        robot_name=robot_name,
        topic=topic,
    )


def format_task_summary(task) -> str:
    """Build a human-readable summary from a task-like object."""
    assigned = task.assigned_robot or "unassigned"
    notes = f", notes={task.notes}" if task.notes else ""
    return (
        f"Task {task.task_id}: {task.task_type.value} "
        f"from {task.source_zone.value} to {task.destination_zone.value} "
        f"(priority={task.priority}, status={task.status.value}, robot={assigned}{notes})"
    )


def format_navigation_goal_summary(goal) -> str:
    """Build a readable summary for a navigation goal."""
    task_ref = goal.task_id or "no-task"
    return (
        f"Goal {goal.goal_id}: task={task_ref} "
        f"from {goal.source_zone.value} to {goal.destination_zone.value} "
        f"(priority={goal.priority}, status={goal.status.value})"
    )


def format_navigation_progress_summary(progress) -> str:
    """Build a readable summary for a navigation progress update."""
    task_ref = progress.task_id or "no-task"
    return (
        f"Progress {progress.goal_id}: task={task_ref} "
        f"{progress.current_zone.value} -> {progress.destination_zone.value} "
        f"({progress.progress_percent:.1f}%, status={progress.status.value}, message={progress.message})"
    )


def format_obstacle_summary(reading) -> str:
    """Build a readable summary for an obstacle reading."""
    return (
        f"Obstacle {reading.reading_id}: zone={reading.zone.value}, distance={reading.distance_meters:.2f}m, "
        f"severity={reading.severity.value}, detected={reading.obstacle_detected}, description={reading.description}"
    )


def format_emergency_stop_summary(command) -> str:
    """Build a readable summary for an emergency stop command."""
    zone = command.zone.value if command.zone is not None else "unknown"
    return (
        f"EmergencyStop {command.command_id}: active={command.active}, state={command.safety_state.value}, "
        f"zone={zone}, reason={command.reason}"
    )


def format_battery_summary(state) -> str:
    """Build a readable summary for a battery state."""
    return (
        f"Battery {state.battery_id}: robot={state.robot_name}, percentage={state.percentage:.1f}%, "
        f"level={state.level.value}, charging_status={state.charging_status.value}, zone={state.current_zone.value}"
    )


def format_charge_command_summary(command) -> str:
    """Build a readable summary for a charge command."""
    return (
        f"ChargeCommand {command.command_id}: robot={command.robot_name}, active={command.active}, "
        f"target_zone={command.target_zone.value}, battery={command.battery_percentage:.1f}%, "
        f"status={command.charging_status.value}, reason={command.reason}"
    )


def format_package_summary(package_info) -> str:
    """Build a readable summary for a package."""
    carried_by = package_info.carried_by or "none"
    return (
        f"Package {package_info.package_id}: {package_info.source_zone.value} -> "
        f"{package_info.destination_zone.value}, state={package_info.state.value}, carried_by={carried_by}"
    )


def format_package_event_summary(event) -> str:
    """Build a readable summary for a package status event."""
    return (
        f"PackageEvent {event.event_id}: type={event.event_type}, package_id={event.package_id}, "
        f"state={event.package_state.value}, robot={event.robot_name}, message={event.message}"
    )


def format_robot_status_summary(snapshot) -> str:
    """Build a readable summary for a robot status snapshot."""
    return (
        f"RobotStatus {snapshot.robot_name}: health={snapshot.health_level.value}, "
        f"mode={snapshot.mode.value}, zone={snapshot.current_zone.value}, "
        f"battery={snapshot.battery_percentage if snapshot.battery_percentage is not None else 'unknown'}, "
        f"task={snapshot.active_task_id or 'none'}, goal={snapshot.active_navigation_goal_id or 'none'}, "
        f"package={snapshot.package_id or 'none'}, carrying={snapshot.carrying_package}, "
        f"estop={snapshot.emergency_stop_active}"
    )


def format_diagnostic_event_summary(event) -> str:
    """Build a readable summary for a diagnostic event."""
    return (
        f"Diagnostic {event.diagnostic_id}: source={event.source.value}, "
        f"level={event.health_level.value}, related_id={event.related_id or 'none'}, "
        f"message={event.message}"
    )


def sort_tasks_by_priority(tasks: list) -> list:
    """Sort tasks by priority descending, then by created time, then task id."""
    return sorted(
        tasks,
        key=lambda task: (-task.priority, task.created_at or "", task.task_id),
    )


def iter_status_counts(tasks: Iterable) -> dict[str, int]:
    """Build a simple count map keyed by task status value."""
    counts: dict[str, int] = {}
    for task in tasks:
        counts[task.status.value] = counts.get(task.status.value, 0) + 1
    return counts


def get_waypoint_for_zone(zone):
    """Return the waypoint coordinates for a warehouse zone."""
    from smart_warehouse_robot.common.constants import WAREHOUSE_ZONE_COORDINATES
    from smart_warehouse_robot.common.models import Waypoint

    parsed_zone = parse_warehouse_zone(zone)
    coordinates = WAREHOUSE_ZONE_COORDINATES[parsed_zone.value]
    return Waypoint(zone=parsed_zone, x=coordinates["x"], y=coordinates["y"])


def calculate_distance(source, destination) -> float:
    """Calculate Euclidean distance between two warehouse waypoints."""
    return math.hypot(destination.x - source.x, destination.y - source.y)
