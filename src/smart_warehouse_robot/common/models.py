"""Shared data models for warehouse tasks and robot state."""

from __future__ import annotations

import json
from dataclasses import dataclass as _dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# Compatibility shim: allow @dataclass(slots=True) on Python <3.10
def dataclass(*args, **kwargs):
    if 'slots' in kwargs:
        try:
            return _dataclass(*args, **kwargs)
        except TypeError:
            kwargs = dict(kwargs)
            kwargs.pop('slots', None)
            return _dataclass(*args, **kwargs)
    return _dataclass(*args, **kwargs)


class WarehouseZone(str, Enum):
    RECEIVING = "receiving"
    STORAGE_A = "storage_a"
    STORAGE_B = "storage_b"
    PACKING = "packing"
    SHIPPING = "shipping"
    CHARGING_STATION = "charging_station"
    PARKING_A = "parking_a"
    PARKING_B = "parking_b"
    PARKING_C = "parking_c"


class TaskType(str, Enum):
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    MOVE = "move"
    CHARGE = "charge"


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RobotMode(str, Enum):
    IDLE = "idle"
    MOVING = "moving"
    LOADING = "loading"
    UNLOADING = "unloading"
    CHARGING = "charging"
    ERROR = "error"


class NavigationStatus(str, Enum):
    IDLE = "idle"
    GOAL_RECEIVED = "goal_received"
    MOVING = "moving"
    ARRIVED = "arrived"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ObstacleSeverity(str, Enum):
    CLEAR = "clear"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyState(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    STOP_REQUIRED = "stop_required"
    EMERGENCY_STOPPED = "emergency_stopped"
    RECOVERING = "recovering"
    FAULT = "fault"


class BatteryLevel(str, Enum):
    FULL = "full"
    NORMAL = "normal"
    LOW = "low"
    CRITICAL = "critical"
    EMPTY = "empty"


class ChargingStatus(str, Enum):
    NOT_CHARGING = "not_charging"
    RETURNING_TO_CHARGE = "returning_to_charge"
    CHARGING = "charging"
    CHARGED = "charged"
    CHARGING_FAULT = "charging_fault"


class PackageState(str, Enum):
    NONE = "none"
    WAITING_FOR_PICKUP = "waiting_for_pickup"
    CARRYING = "carrying"
    DELIVERED = "delivered"
    DROPPED = "dropped"
    FAILED = "failed"


class PackageAction(str, Enum):
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    RESET = "reset"


class RobotHealthLevel(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DiagnosticSource(str, Enum):
    TASK = "task"
    NAVIGATION = "navigation"
    SAFETY = "safety"
    BATTERY = "battery"
    PACKAGE = "package"
    STATUS = "status"
    SYSTEM = "system"


@dataclass(slots=True)
class WarehouseTask:
    """Data model for warehouse work items shared across CLI and ROS nodes."""

    task_type: TaskType | str
    source_zone: WarehouseZone | str
    destination_zone: WarehouseZone | str
    priority: int
    status: TaskStatus | str = TaskStatus.CREATED
    task_id: str = field(default_factory=lambda: _default_task_id())
    assigned_robot: Optional[str] = None
    created_at: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import (
            clamp_priority,
            parse_task_status,
            parse_task_type,
            parse_warehouse_zone,
        )

        self.task_type = parse_task_type(self.task_type)
        self.source_zone = parse_warehouse_zone(self.source_zone)
        self.destination_zone = parse_warehouse_zone(self.destination_zone)
        self.status = parse_task_status(self.status)
        self.priority = clamp_priority(self.priority)
        self.task_id = str(self.task_id).strip()
        if not self.task_id:
            raise ValueError("task_id must be a non-empty string.")

        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

        self.ensure_distinct_zones()

    def ensure_distinct_zones(self) -> None:
        """Avoid meaningless tasks where source and destination are identical."""
        if self.source_zone == self.destination_zone:
            raise ValueError("Source and destination zones must be different.")

    def is_high_priority(self) -> bool:
        """Return True when the task should be treated as urgent."""
        return self.priority >= 4

    def is_terminal(self) -> bool:
        """Return True for statuses that should not return to active processing."""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
        }

    def mark_queued(self) -> "WarehouseTask":
        self.status = TaskStatus.QUEUED
        return self

    def mark_in_progress(self) -> "WarehouseTask":
        self.status = TaskStatus.IN_PROGRESS
        return self

    def mark_completed(self) -> "WarehouseTask":
        self.status = TaskStatus.COMPLETED
        return self

    def mark_cancelled(self) -> "WarehouseTask":
        self.status = TaskStatus.CANCELLED
        return self

    def to_dict(self) -> dict:
        """Return a JSON-serializable task dictionary with stable keys."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "source_zone": self.source_zone.value,
            "destination_zone": self.destination_zone.value,
            "priority": self.priority,
            "status": self.status.value,
            "assigned_robot": self.assigned_robot,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    def to_json(self) -> str:
        """Serialize the task with stable ordering and readable indentation."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "WarehouseTask":
        """Build a task from a dictionary and raise clear validation errors."""
        try:
            return cls(
                task_id=data.get("task_id") or _default_task_id(),
                task_type=data["task_type"],
                source_zone=data["source_zone"],
                destination_zone=data["destination_zone"],
                priority=data["priority"],
                status=data.get("status", TaskStatus.CREATED.value),
                assigned_robot=data.get("assigned_robot"),
                created_at=data.get("created_at"),
                notes=data.get("notes"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required task field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid task data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "WarehouseTask":
        """Build a task from JSON and raise helpful validation errors."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid task JSON: {exc.msg}") from exc

        if not isinstance(data, dict):
            raise ValueError("Invalid task JSON: expected a JSON object.")

        return cls.from_dict(data)


def _default_task_id() -> str:
    from smart_warehouse_robot.common.helpers import create_task_id

    return create_task_id()


@dataclass(slots=True)
class Waypoint:
    """Simple warehouse waypoint derived from a named zone."""

    zone: WarehouseZone | str
    x: float
    y: float

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import parse_warehouse_zone

        self.zone = parse_warehouse_zone(self.zone)
        self.x = float(self.x)
        self.y = float(self.y)

    def to_dict(self) -> dict:
        return {
            "zone": self.zone.value,
            "x": self.x,
            "y": self.y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Waypoint":
        try:
            return cls(
                zone=data["zone"],
                x=data["x"],
                y=data["y"],
            )
        except KeyError as exc:
            raise ValueError(f"Missing required waypoint field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid waypoint data: {exc}") from exc


@dataclass(slots=True)
class NavigationGoal:
    """Navigation goal produced from a task start event."""

    source_zone: WarehouseZone | str
    destination_zone: WarehouseZone | str
    priority: int
    status: NavigationStatus | str = NavigationStatus.IDLE
    goal_id: str = field(default_factory=lambda: _default_goal_id())
    task_id: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import (
            clamp_priority,
            parse_navigation_status,
            parse_warehouse_zone,
        )

        self.goal_id = str(self.goal_id).strip()
        if not self.goal_id:
            raise ValueError("goal_id must be a non-empty string.")

        self.task_id = str(self.task_id).strip() if self.task_id is not None else None
        self.source_zone = parse_warehouse_zone(self.source_zone)
        self.destination_zone = parse_warehouse_zone(self.destination_zone)
        self.priority = clamp_priority(self.priority)
        self.status = parse_navigation_status(self.status)

        if self.source_zone == self.destination_zone:
            raise ValueError("Navigation goal source and destination must be different.")

    def mark_received(self) -> "NavigationGoal":
        self.status = NavigationStatus.GOAL_RECEIVED
        return self

    def mark_moving(self) -> "NavigationGoal":
        self.status = NavigationStatus.MOVING
        return self

    def mark_arrived(self) -> "NavigationGoal":
        self.status = NavigationStatus.ARRIVED
        return self

    def mark_blocked(self) -> "NavigationGoal":
        self.status = NavigationStatus.BLOCKED
        return self

    def mark_cancelled(self) -> "NavigationGoal":
        self.status = NavigationStatus.CANCELLED
        return self

    def is_terminal(self) -> bool:
        return self.status in {
            NavigationStatus.ARRIVED,
            NavigationStatus.CANCELLED,
            NavigationStatus.FAILED,
        }

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "source_zone": self.source_zone.value,
            "destination_zone": self.destination_zone.value,
            "priority": self.priority,
            "status": self.status.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "NavigationGoal":
        try:
            return cls(
                goal_id=data.get("goal_id") or _default_goal_id(),
                task_id=data.get("task_id"),
                source_zone=data["source_zone"],
                destination_zone=data["destination_zone"],
                priority=data["priority"],
                status=data.get("status", NavigationStatus.IDLE.value),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required navigation goal field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid navigation goal data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "NavigationGoal":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid navigation goal JSON: {exc.msg}") from exc

        if not isinstance(data, dict):
            raise ValueError("Invalid navigation goal JSON: expected a JSON object.")

        return cls.from_dict(data)


@dataclass(slots=True)
class NavigationProgress:
    """Progress event emitted while the robot moves toward a destination zone."""

    goal_id: str
    task_id: Optional[str]
    current_zone: WarehouseZone | str
    destination_zone: WarehouseZone | str
    progress_percent: float
    status: NavigationStatus | str
    message: str

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import clamp_progress, parse_navigation_status, parse_warehouse_zone

        self.goal_id = str(self.goal_id).strip()
        if not self.goal_id:
            raise ValueError("goal_id must be a non-empty string.")

        self.task_id = str(self.task_id).strip() if self.task_id is not None else None
        self.current_zone = parse_warehouse_zone(self.current_zone)
        self.destination_zone = parse_warehouse_zone(self.destination_zone)
        self.progress_percent = clamp_progress(self.progress_percent)
        self.status = parse_navigation_status(self.status)
        self.message = str(self.message)

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "current_zone": self.current_zone.value,
            "destination_zone": self.destination_zone.value,
            "progress_percent": self.progress_percent,
            "status": self.status.value,
            "message": self.message,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "NavigationProgress":
        try:
            return cls(
                goal_id=data["goal_id"],
                task_id=data.get("task_id"),
                current_zone=data["current_zone"],
                destination_zone=data["destination_zone"],
                progress_percent=data["progress_percent"],
                status=data["status"],
                message=data["message"],
            )
        except KeyError as exc:
            raise ValueError(f"Missing required navigation progress field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid navigation progress data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "NavigationProgress":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid navigation progress JSON: {exc.msg}") from exc

        if not isinstance(data, dict):
            raise ValueError("Invalid navigation progress JSON: expected a JSON object.")

        return cls.from_dict(data)


def _default_goal_id() -> str:
    from smart_warehouse_robot.common.helpers import create_goal_id

    return create_goal_id()


@dataclass(slots=True)
class ObstacleReading:
    """Obstacle reading used for safety simulation."""

    zone: WarehouseZone | str
    distance_meters: float
    severity: ObstacleSeverity | str
    obstacle_detected: bool
    reading_id: str = field(default_factory=lambda: _default_reading_id())
    description: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import parse_obstacle_severity, parse_warehouse_zone

        self.reading_id = str(self.reading_id).strip()
        if not self.reading_id:
            raise ValueError("reading_id must be a non-empty string.")

        self.zone = parse_warehouse_zone(self.zone)
        self.distance_meters = max(0.0, float(self.distance_meters))
        self.severity = parse_obstacle_severity(self.severity)
        self.obstacle_detected = self.severity != ObstacleSeverity.CLEAR
        self.description = str(self.description) if self.description is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "reading_id": self.reading_id,
            "zone": self.zone.value,
            "distance_meters": self.distance_meters,
            "severity": self.severity.value,
            "obstacle_detected": self.obstacle_detected,
            "description": self.description,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "ObstacleReading":
        try:
            return cls(
                reading_id=data.get("reading_id") or _default_reading_id(),
                zone=data["zone"],
                distance_meters=data["distance_meters"],
                severity=data["severity"],
                obstacle_detected=data.get("obstacle_detected", False),
                description=data.get("description"),
                timestamp=data.get("timestamp"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required obstacle reading field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid obstacle reading data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "ObstacleReading":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid obstacle reading JSON: {exc.msg}") from exc

        if not isinstance(data, dict):
            raise ValueError("Invalid obstacle reading JSON: expected a JSON object.")

        return cls.from_dict(data)

    def is_dangerous(self) -> bool:
        return self.severity in {ObstacleSeverity.HIGH, ObstacleSeverity.CRITICAL}


@dataclass(slots=True)
class EmergencyStopCommand:
    """Emergency stop command emitted by the safety monitor."""

    active: bool
    reason: str
    safety_state: SafetyState | str
    command_id: str = field(default_factory=lambda: _default_emergency_command_id())
    source_reading_id: Optional[str] = None
    zone: Optional[WarehouseZone | str] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import parse_safety_state, parse_warehouse_zone

        self.command_id = str(self.command_id).strip()
        if not self.command_id:
            raise ValueError("command_id must be a non-empty string.")

        self.active = bool(self.active)
        self.reason = str(self.reason)
        self.safety_state = parse_safety_state(self.safety_state)
        self.source_reading_id = str(self.source_reading_id).strip() if self.source_reading_id is not None else None
        self.zone = parse_warehouse_zone(self.zone) if self.zone is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "active": self.active,
            "reason": self.reason,
            "safety_state": self.safety_state.value,
            "source_reading_id": self.source_reading_id,
            "zone": self.zone.value if self.zone is not None else None,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "EmergencyStopCommand":
        try:
            return cls(
                command_id=data.get("command_id") or _default_emergency_command_id(),
                active=data["active"],
                reason=data["reason"],
                safety_state=data["safety_state"],
                source_reading_id=data.get("source_reading_id"),
                zone=data.get("zone"),
                timestamp=data.get("timestamp"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required emergency stop field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid emergency stop data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "EmergencyStopCommand":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid emergency stop JSON: {exc.msg}") from exc

        if not isinstance(data, dict):
            raise ValueError("Invalid emergency stop JSON: expected a JSON object.")

        return cls.from_dict(data)

    def activate(self) -> "EmergencyStopCommand":
        self.active = True
        if self.safety_state not in {SafetyState.EMERGENCY_STOPPED, SafetyState.STOP_REQUIRED}:
            self.safety_state = SafetyState.EMERGENCY_STOPPED
        return self

    def clear(self) -> "EmergencyStopCommand":
        self.active = False
        self.safety_state = SafetyState.SAFE
        return self

    def is_active(self) -> bool:
        return self.active


def _default_reading_id() -> str:
    from smart_warehouse_robot.common.helpers import create_reading_id

    return create_reading_id()


def _default_emergency_command_id() -> str:
    from smart_warehouse_robot.common.helpers import create_emergency_command_id

    return create_emergency_command_id()


@dataclass(slots=True)
class BatteryState:
    """Battery state used for simulation and charge control."""

    robot_name: str
    percentage: float
    charging_status: ChargingStatus | str
    current_zone: WarehouseZone | str
    battery_id: str = field(default_factory=lambda: _default_battery_id())
    level: BatteryLevel | str | None = None
    voltage: Optional[float] = None
    temperature_celsius: Optional[float] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import clamp_percentage, classify_battery_level, parse_battery_level, parse_charging_status, parse_warehouse_zone

        self.battery_id = str(self.battery_id).strip()
        if not self.battery_id:
            raise ValueError("battery_id must be a non-empty string.")

        self.robot_name = str(self.robot_name).strip()
        if not self.robot_name:
            raise ValueError("robot_name must be a non-empty string.")

        self.percentage = clamp_percentage(self.percentage)
        self.current_zone = parse_warehouse_zone(self.current_zone)
        self.charging_status = parse_charging_status(self.charging_status)
        self.level = classify_battery_level(self.percentage) if self.level is None else parse_battery_level(self.level)
        self.voltage = float(self.voltage) if self.voltage is not None else None
        self.temperature_celsius = float(self.temperature_celsius) if self.temperature_celsius is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "battery_id": self.battery_id,
            "robot_name": self.robot_name,
            "percentage": self.percentage,
            "level": self.level.value,
            "charging_status": self.charging_status.value,
            "current_zone": self.current_zone.value,
            "voltage": self.voltage,
            "temperature_celsius": self.temperature_celsius,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "BatteryState":
        try:
            return cls(
                battery_id=data.get("battery_id") or _default_battery_id(),
                robot_name=data["robot_name"],
                percentage=data["percentage"],
                level=data.get("level"),
                charging_status=data["charging_status"],
                current_zone=data["current_zone"],
                voltage=data.get("voltage"),
                temperature_celsius=data.get("temperature_celsius"),
                timestamp=data.get("timestamp"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required battery state field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid battery state data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "BatteryState":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid battery state JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid battery state JSON: expected a JSON object.")
        return cls.from_dict(data)

    def is_low(self) -> bool:
        return self.level in {BatteryLevel.LOW, BatteryLevel.CRITICAL, BatteryLevel.EMPTY}

    def is_critical(self) -> bool:
        return self.level in {BatteryLevel.CRITICAL, BatteryLevel.EMPTY}

    def is_empty(self) -> bool:
        return self.level == BatteryLevel.EMPTY

    def is_charging(self) -> bool:
        return self.charging_status == ChargingStatus.CHARGING


@dataclass(slots=True)
class ChargeCommand:
    """Command instructing the robot to return to the charging station."""

    robot_name: str
    active: bool
    reason: str
    target_zone: WarehouseZone | str
    battery_percentage: float
    charging_status: ChargingStatus | str
    command_id: str = field(default_factory=lambda: _default_charge_command_id())
    source_battery_id: Optional[str] = None
    timestamp: Optional[str] = None
    current_zone: Optional[WarehouseZone | str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import clamp_percentage, parse_charging_status, parse_warehouse_zone

        self.command_id = str(self.command_id).strip()
        if not self.command_id:
            raise ValueError("command_id must be a non-empty string.")

        self.robot_name = str(self.robot_name).strip()
        if not self.robot_name:
            raise ValueError("robot_name must be a non-empty string.")

        self.active = bool(self.active)
        self.reason = str(self.reason)
        self.target_zone = parse_warehouse_zone(self.target_zone)
        self.battery_percentage = clamp_percentage(self.battery_percentage)
        self.charging_status = parse_charging_status(self.charging_status)
        self.source_battery_id = str(self.source_battery_id).strip() if self.source_battery_id is not None else None
        self.current_zone = parse_warehouse_zone(self.current_zone) if self.current_zone is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "robot_name": self.robot_name,
            "active": self.active,
            "reason": self.reason,
            "target_zone": self.target_zone.value,
            "battery_percentage": self.battery_percentage,
            "charging_status": self.charging_status.value,
            "source_battery_id": self.source_battery_id,
            "timestamp": self.timestamp,
            "current_zone": self.current_zone.value if self.current_zone is not None else None,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "ChargeCommand":
        try:
            return cls(
                command_id=data.get("command_id") or _default_charge_command_id(),
                robot_name=data["robot_name"],
                active=data["active"],
                reason=data["reason"],
                target_zone=data["target_zone"],
                battery_percentage=data["battery_percentage"],
                charging_status=data["charging_status"],
                source_battery_id=data.get("source_battery_id"),
                timestamp=data.get("timestamp"),
                current_zone=data.get("current_zone"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required charge command field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid charge command data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "ChargeCommand":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid charge command JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid charge command JSON: expected a JSON object.")
        return cls.from_dict(data)

    def activate(self) -> "ChargeCommand":
        self.active = True
        if self.charging_status != ChargingStatus.RETURNING_TO_CHARGE:
            self.charging_status = ChargingStatus.RETURNING_TO_CHARGE
        return self

    def clear(self) -> "ChargeCommand":
        self.active = False
        if self.charging_status == ChargingStatus.RETURNING_TO_CHARGE:
            self.charging_status = ChargingStatus.NOT_CHARGING
        return self

    def is_active(self) -> bool:
        return self.active


def _default_battery_id() -> str:
    from smart_warehouse_robot.common.helpers import create_battery_id

    return create_battery_id()


def _default_charge_command_id() -> str:
    from smart_warehouse_robot.common.helpers import create_charge_command_id

    return create_charge_command_id()


@dataclass(slots=True)
class PackageInfo:
    """Package data tracked by the package handler."""

    package_id: str
    source_zone: WarehouseZone | str
    destination_zone: WarehouseZone | str
    state: PackageState | str
    carried_by: Optional[str] = None
    task_id: Optional[str] = None
    notes: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import parse_package_state, parse_warehouse_zone

        self.package_id = str(self.package_id).strip()
        if not self.package_id:
            raise ValueError("package_id must be a non-empty string.")
        self.source_zone = parse_warehouse_zone(self.source_zone)
        self.destination_zone = parse_warehouse_zone(self.destination_zone)
        self.state = parse_package_state(self.state)
        self.carried_by = str(self.carried_by).strip() if self.carried_by is not None else None
        self.task_id = str(self.task_id).strip() if self.task_id is not None else None
        self.notes = str(self.notes) if self.notes is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "source_zone": self.source_zone.value,
            "destination_zone": self.destination_zone.value,
            "state": self.state.value,
            "carried_by": self.carried_by,
            "task_id": self.task_id,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "PackageInfo":
        try:
            return cls(
                package_id=data["package_id"],
                source_zone=data["source_zone"],
                destination_zone=data["destination_zone"],
                state=data["state"],
                carried_by=data.get("carried_by"),
                task_id=data.get("task_id"),
                notes=data.get("notes"),
                timestamp=data.get("timestamp"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required package field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid package data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "PackageInfo":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid package JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid package JSON: expected a JSON object.")
        return cls.from_dict(data)

    def mark_waiting(self) -> "PackageInfo":
        self.state = PackageState.WAITING_FOR_PICKUP
        return self

    def mark_carrying(self, robot_name: str) -> "PackageInfo":
        self.state = PackageState.CARRYING
        self.carried_by = robot_name
        return self

    def mark_delivered(self) -> "PackageInfo":
        self.state = PackageState.DELIVERED
        return self

    def mark_dropped(self) -> "PackageInfo":
        self.state = PackageState.DROPPED
        return self

    def mark_failed(self) -> "PackageInfo":
        self.state = PackageState.FAILED
        return self

    def is_terminal(self) -> bool:
        return self.state in {PackageState.DELIVERED, PackageState.DROPPED, PackageState.FAILED}


@dataclass(slots=True)
class PackageStatusEvent:
    """Status event published by the package handler node."""

    event_type: str
    package_state: PackageState | str
    robot_name: str
    message: str
    event_id: str = field(default_factory=lambda: _default_package_event_id())
    package_id: Optional[str] = None
    task_id: Optional[str] = None
    source_zone: Optional[WarehouseZone | str] = None
    destination_zone: Optional[WarehouseZone | str] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import parse_package_state, parse_warehouse_zone

        self.event_id = str(self.event_id).strip()
        if not self.event_id:
            raise ValueError("event_id must be a non-empty string.")
        self.event_type = str(self.event_type).strip()
        self.package_state = parse_package_state(self.package_state)
        self.robot_name = str(self.robot_name).strip()
        self.message = str(self.message)
        self.package_id = str(self.package_id).strip() if self.package_id is not None else None
        self.task_id = str(self.task_id).strip() if self.task_id is not None else None
        self.source_zone = parse_warehouse_zone(self.source_zone) if self.source_zone is not None else None
        self.destination_zone = parse_warehouse_zone(self.destination_zone) if self.destination_zone is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "package_id": self.package_id,
            "package_state": self.package_state.value,
            "robot_name": self.robot_name,
            "message": self.message,
            "task_id": self.task_id,
            "source_zone": self.source_zone.value if self.source_zone is not None else None,
            "destination_zone": self.destination_zone.value if self.destination_zone is not None else None,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "PackageStatusEvent":
        try:
            return cls(
                event_id=data.get("event_id") or _default_package_event_id(),
                event_type=data["event_type"],
                package_id=data.get("package_id"),
                package_state=data["package_state"],
                robot_name=data["robot_name"],
                message=data["message"],
                task_id=data.get("task_id"),
                source_zone=data.get("source_zone"),
                destination_zone=data.get("destination_zone"),
                timestamp=data.get("timestamp"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required package event field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid package event data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "PackageStatusEvent":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid package event JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid package event JSON: expected a JSON object.")
        return cls.from_dict(data)


def _default_package_event_id() -> str:
    from smart_warehouse_robot.common.helpers import create_package_event_id

    return create_package_event_id()


@dataclass(slots=True)
class RobotStatusSnapshot:
    """Combined robot snapshot used by the status and diagnostics pipeline."""

    robot_name: str
    health_level: RobotHealthLevel | str
    mode: RobotMode | str
    current_zone: WarehouseZone | str
    battery_percentage: Optional[float] = None
    active_task_id: Optional[str] = None
    active_navigation_goal_id: Optional[str] = None
    package_id: Optional[str] = None
    carrying_package: bool = False
    emergency_stop_active: bool = False
    last_event: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import (
            clamp_percentage,
            parse_robot_health_level,
            parse_robot_mode,
            parse_warehouse_zone,
        )

        self.robot_name = str(self.robot_name).strip()
        if not self.robot_name:
            raise ValueError("robot_name must be a non-empty string.")
        self.health_level = parse_robot_health_level(self.health_level)
        self.mode = parse_robot_mode(self.mode)
        self.current_zone = parse_warehouse_zone(self.current_zone)
        self.battery_percentage = (
            clamp_percentage(self.battery_percentage)
            if self.battery_percentage is not None
            else None
        )
        self.active_task_id = str(self.active_task_id).strip() if self.active_task_id is not None else None
        self.active_navigation_goal_id = (
            str(self.active_navigation_goal_id).strip()
            if self.active_navigation_goal_id is not None
            else None
        )
        self.package_id = str(self.package_id).strip() if self.package_id is not None else None
        self.carrying_package = bool(self.carrying_package)
        self.emergency_stop_active = bool(self.emergency_stop_active)
        self.last_event = str(self.last_event) if self.last_event is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "robot_name": self.robot_name,
            "health_level": self.health_level.value,
            "mode": self.mode.value,
            "current_zone": self.current_zone.value,
            "battery_percentage": self.battery_percentage,
            "active_task_id": self.active_task_id,
            "active_navigation_goal_id": self.active_navigation_goal_id,
            "package_id": self.package_id,
            "carrying_package": self.carrying_package,
            "emergency_stop_active": self.emergency_stop_active,
            "last_event": self.last_event,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "RobotStatusSnapshot":
        try:
            return cls(
                robot_name=data["robot_name"],
                health_level=data.get("health_level", RobotHealthLevel.UNKNOWN.value),
                mode=data["mode"],
                current_zone=data["current_zone"],
                battery_percentage=data.get("battery_percentage"),
                active_task_id=data.get("active_task_id"),
                active_navigation_goal_id=data.get("active_navigation_goal_id"),
                package_id=data.get("package_id"),
                carrying_package=data.get("carrying_package", False),
                emergency_stop_active=data.get("emergency_stop_active", False),
                last_event=data.get("last_event"),
                timestamp=data.get("timestamp"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required robot status field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid robot status data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "RobotStatusSnapshot":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid robot status JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid robot status JSON: expected a JSON object.")
        return cls.from_dict(data)

    def is_healthy(self) -> bool:
        return self.health_level == RobotHealthLevel.OK

    def has_warning_or_worse(self) -> bool:
        return self.health_level in {
            RobotHealthLevel.WARNING,
            RobotHealthLevel.ERROR,
            RobotHealthLevel.CRITICAL,
        }


@dataclass(slots=True)
class DiagnosticEvent:
    """Diagnostic event derived from robot status for logging and demos."""

    source: DiagnosticSource | str
    health_level: RobotHealthLevel | str
    message: str
    diagnostic_id: str = field(default_factory=lambda: _default_diagnostic_id())
    related_id: Optional[str] = None
    robot_name: Optional[str] = None
    topic: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        from smart_warehouse_robot.common.helpers import (
            parse_diagnostic_source,
            parse_robot_health_level,
        )

        self.diagnostic_id = str(self.diagnostic_id).strip()
        if not self.diagnostic_id:
            raise ValueError("diagnostic_id must be a non-empty string.")
        self.source = parse_diagnostic_source(self.source)
        self.health_level = parse_robot_health_level(self.health_level)
        self.message = str(self.message).strip()
        if not self.message:
            raise ValueError("message must be a non-empty string.")
        self.related_id = str(self.related_id).strip() if self.related_id is not None else None
        self.robot_name = str(self.robot_name).strip() if self.robot_name is not None else None
        self.topic = str(self.topic).strip() if self.topic is not None else None
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "diagnostic_id": self.diagnostic_id,
            "source": self.source.value,
            "health_level": self.health_level.value,
            "message": self.message,
            "related_id": self.related_id,
            "robot_name": self.robot_name,
            "topic": self.topic,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> "DiagnosticEvent":
        try:
            return cls(
                diagnostic_id=data.get("diagnostic_id") or _default_diagnostic_id(),
                source=data["source"],
                health_level=data["health_level"],
                message=data["message"],
                related_id=data.get("related_id"),
                robot_name=data.get("robot_name"),
                topic=data.get("topic"),
                timestamp=data.get("timestamp"),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required diagnostic field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid diagnostic data: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "DiagnosticEvent":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid diagnostic JSON: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("Invalid diagnostic JSON: expected a JSON object.")
        return cls.from_dict(data)

    def is_error_or_worse(self) -> bool:
        return self.health_level in {RobotHealthLevel.ERROR, RobotHealthLevel.CRITICAL}


def _default_diagnostic_id() -> str:
    from smart_warehouse_robot.common.helpers import create_diagnostic_id

    return create_diagnostic_id()
