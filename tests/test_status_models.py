import pytest

from smart_warehouse_robot.common.models import (
    DiagnosticEvent,
    RobotHealthLevel,
    RobotStatusSnapshot,
)


def test_create_robot_status_snapshot_successfully():
    snapshot = RobotStatusSnapshot(
        robot_name="warehouse_bot_01",
        health_level="ok",
        mode="idle",
        current_zone="receiving",
        battery_percentage=80,
    )
    assert snapshot.robot_name == "warehouse_bot_01"
    assert snapshot.health_level == RobotHealthLevel.OK


def test_robot_status_snapshot_json_round_trip():
    snapshot = RobotStatusSnapshot(
        robot_name="warehouse_bot_01",
        health_level="warning",
        mode="moving",
        current_zone="storage_a",
        battery_percentage=20,
        active_task_id="TASK-001",
    )
    restored = RobotStatusSnapshot.from_json(snapshot.to_json())
    assert restored.active_task_id == "TASK-001"
    assert restored.health_level == RobotHealthLevel.WARNING


def test_battery_percentage_clamps_low_and_high():
    low_snapshot = RobotStatusSnapshot(
        robot_name="warehouse_bot_01",
        health_level="ok",
        mode="idle",
        current_zone="receiving",
        battery_percentage=-5,
    )
    high_snapshot = RobotStatusSnapshot(
        robot_name="warehouse_bot_01",
        health_level="ok",
        mode="idle",
        current_zone="receiving",
        battery_percentage=150,
    )
    assert low_snapshot.battery_percentage == 0.0
    assert high_snapshot.battery_percentage == 100.0


def test_health_level_parsing_and_flags_work():
    snapshot = RobotStatusSnapshot(
        robot_name="warehouse_bot_01",
        health_level="critical",
        mode="error",
        current_zone="packing",
    )
    assert snapshot.health_level == RobotHealthLevel.CRITICAL
    assert snapshot.is_healthy() is False
    assert snapshot.has_warning_or_worse() is True


def test_diagnostic_event_json_round_trip():
    event = DiagnosticEvent(
        source="battery",
        health_level="warning",
        message="Battery below threshold",
        robot_name="warehouse_bot_01",
    )
    restored = DiagnosticEvent.from_json(event.to_json())
    assert restored.source.value == "battery"
    assert restored.health_level.value == "warning"


def test_diagnostic_event_is_error_or_worse_works():
    assert DiagnosticEvent(
        source="system",
        health_level="error",
        message="Controller failure",
    ).is_error_or_worse() is True
    assert DiagnosticEvent(
        source="status",
        health_level="ok",
        message="Healthy",
    ).is_error_or_worse() is False


def test_invalid_health_level_raises_value_error():
    with pytest.raises(ValueError):
        RobotStatusSnapshot(
            robot_name="warehouse_bot_01",
            health_level="bad",
            mode="idle",
            current_zone="receiving",
        )
