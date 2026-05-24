"""Pure safety monitoring logic for obstacle readings and emergency stops."""

from __future__ import annotations

from typing import Optional

from smart_warehouse_robot.common.constants import (
    DEFAULT_CRITICAL_DISTANCE_METERS,
    DEFAULT_OBSTACLE_DISTANCE_THRESHOLD_METERS,
)
from smart_warehouse_robot.common.helpers import build_emergency_stop_command
from smart_warehouse_robot.common.models import EmergencyStopCommand, ObstacleReading, ObstacleSeverity, SafetyState


class SafetyMonitor:
    """Track obstacle readings and decide when an emergency stop is required."""

    def __init__(
        self,
        distance_threshold_meters: float = DEFAULT_OBSTACLE_DISTANCE_THRESHOLD_METERS,
        critical_distance_meters: float = DEFAULT_CRITICAL_DISTANCE_METERS,
    ) -> None:
        self.distance_threshold_meters = float(distance_threshold_meters)
        self.critical_distance_meters = float(critical_distance_meters)
        self._latest_reading: Optional[ObstacleReading] = None
        self._safety_state = SafetyState.SAFE
        self._active_command: Optional[EmergencyStopCommand] = None

    def process_reading(self, reading: ObstacleReading) -> Optional[EmergencyStopCommand]:
        """Update internal state from a new obstacle reading."""
        self._latest_reading = reading

        if self._active_command is not None and self._active_command.is_active():
            return self._active_command

        if reading.severity in {ObstacleSeverity.CLEAR, ObstacleSeverity.LOW}:
            self._safety_state = SafetyState.SAFE
            return None

        if reading.severity == ObstacleSeverity.MEDIUM:
            self._safety_state = SafetyState.WARNING
            return None

        if reading.severity in {ObstacleSeverity.HIGH, ObstacleSeverity.CRITICAL}:
            self._safety_state = SafetyState.EMERGENCY_STOPPED
            self._active_command = build_emergency_stop_command(reading)
            self._active_command.activate()
            return self._active_command

        self._safety_state = SafetyState.FAULT
        return None

    def get_latest_reading(self) -> Optional[ObstacleReading]:
        """Return the latest obstacle reading processed by the monitor."""
        return self._latest_reading

    def get_safety_state(self) -> SafetyState:
        """Return the current safety state."""
        return self._safety_state

    def is_emergency_active(self) -> bool:
        """Return True when an emergency stop is currently active."""
        return self._active_command is not None and self._active_command.is_active()

    def clear_emergency(self, reason: str = "Obstacle cleared") -> EmergencyStopCommand:
        """Clear the active emergency stop and return a recovery command."""
        zone = self._latest_reading.zone if self._latest_reading is not None else None
        source_reading_id = self._latest_reading.reading_id if self._latest_reading is not None else None
        command = EmergencyStopCommand(
            active=False,
            reason=reason,
            safety_state=SafetyState.SAFE,
            source_reading_id=source_reading_id,
            zone=zone,
        )
        command.clear()
        self._active_command = command
        self._safety_state = SafetyState.SAFE
        return command

    def summary(self) -> dict:
        """Return a compact summary of the current safety state."""
        return {
            "safety_state": self._safety_state.value,
            "emergency_active": self.is_emergency_active(),
            "latest_reading_id": self._latest_reading.reading_id if self._latest_reading else None,
            "latest_severity": self._latest_reading.severity.value if self._latest_reading else None,
            "latest_zone": self._latest_reading.zone.value if self._latest_reading else None,
        }
