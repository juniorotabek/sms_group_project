import pytest

from smart_warehouse_robot.common.helpers import parse_obstacle_severity
from smart_warehouse_robot.common.models import EmergencyStopCommand, ObstacleReading, ObstacleSeverity, SafetyState


def test_create_obstacle_reading_successfully():
    reading = ObstacleReading(
        zone="storage_a",
        distance_meters=0.8,
        severity="high",
        obstacle_detected=True,
        description="Box detected",
    )

    assert reading.zone.value == "storage_a"
    assert reading.severity == ObstacleSeverity.HIGH
    assert reading.obstacle_detected is True


def test_obstacle_reading_json_round_trip():
    reading = ObstacleReading(
        reading_id="OBS-001",
        zone="storage_a",
        distance_meters=1.5,
        severity="medium",
        obstacle_detected=True,
        description="Pallet ahead",
    )

    restored = ObstacleReading.from_json(reading.to_json())
    assert restored.to_dict() == reading.to_dict()


def test_negative_distance_clamps_to_zero():
    reading = ObstacleReading(
        zone="storage_a",
        distance_meters=-2.0,
        severity="critical",
        obstacle_detected=True,
    )
    assert reading.distance_meters == 0.0


def test_severity_parsing_works():
    assert parse_obstacle_severity("HIGH") == ObstacleSeverity.HIGH
    assert parse_obstacle_severity("critical") == ObstacleSeverity.CRITICAL


def test_dangerous_readings_work():
    assert ObstacleReading(zone="storage_a", distance_meters=0.8, severity="high", obstacle_detected=True).is_dangerous()
    assert not ObstacleReading(zone="storage_a", distance_meters=3.0, severity="low", obstacle_detected=True).is_dangerous()


def test_emergency_stop_command_json_round_trip():
    command = EmergencyStopCommand(
        command_id="ESTOP-001",
        active=True,
        reason="Critical obstacle detected",
        safety_state="emergency_stopped",
        source_reading_id="OBS-001",
        zone="storage_a",
    )

    restored = EmergencyStopCommand.from_json(command.to_json())
    assert restored.to_dict() == command.to_dict()


def test_active_emergency_command_works():
    command = EmergencyStopCommand(
        active=True,
        reason="High obstacle detected",
        safety_state=SafetyState.STOP_REQUIRED,
    )
    assert command.is_active() is True
    command.clear()
    assert command.is_active() is False
    assert command.safety_state == SafetyState.SAFE
