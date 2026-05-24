from smart_warehouse_robot.common.helpers import (
    build_diagnostic_event,
    build_robot_status_snapshot,
    determine_health_level,
)
from smart_warehouse_robot.common.models import DiagnosticSource, RobotHealthLevel, WarehouseZone
from smart_warehouse_robot.services.status import DiagnosticLogger, RobotStatusAggregator


def test_determine_health_level_rules_work():
    assert determine_health_level() == RobotHealthLevel.OK
    assert determine_health_level(battery_percentage=20) == RobotHealthLevel.WARNING
    assert determine_health_level(battery_percentage=5) == RobotHealthLevel.CRITICAL
    assert determine_health_level(emergency_stop_active=True) == RobotHealthLevel.CRITICAL
    assert determine_health_level(navigation_blocked=True) == RobotHealthLevel.WARNING
    assert determine_health_level(package_failed=True) == RobotHealthLevel.ERROR


def test_build_robot_status_snapshot_returns_valid_snapshot():
    snapshot = build_robot_status_snapshot(
        robot_name="warehouse_bot_01",
        current_zone="receiving",
        mode="idle",
        battery_percentage=80,
    )
    assert snapshot.current_zone == WarehouseZone.RECEIVING
    assert snapshot.health_level == RobotHealthLevel.OK


def test_build_diagnostic_event_returns_valid_event():
    event = build_diagnostic_event(
        source="status",
        health_level="warning",
        message="Robot requires attention",
    )
    assert event.source == DiagnosticSource.STATUS
    assert event.health_level == RobotHealthLevel.WARNING


def test_robot_status_aggregator_starts_with_default_state():
    aggregator = RobotStatusAggregator()
    snapshot = aggregator.get_snapshot()
    assert snapshot.current_zone == WarehouseZone.RECEIVING
    assert snapshot.health_level == RobotHealthLevel.OK


def test_update_from_task_status_sets_active_task():
    aggregator = RobotStatusAggregator()
    aggregator.update_from_task_status({"event_type": "task_started", "task_id": "TASK-001"})
    assert aggregator.get_snapshot().active_task_id == "TASK-001"


def test_update_from_navigation_progress_sets_zone_and_goal():
    aggregator = RobotStatusAggregator()
    aggregator.update_from_navigation_progress(
        {"goal_id": "GOAL-001", "current_zone": "packing", "status": "moving"}
    )
    snapshot = aggregator.get_snapshot()
    assert snapshot.current_zone == WarehouseZone.PACKING
    assert snapshot.active_navigation_goal_id == "GOAL-001"


def test_update_from_emergency_stop_sets_active_flag():
    aggregator = RobotStatusAggregator()
    aggregator.update_from_emergency_stop({"active": True, "reason": "Emergency stop"})
    assert aggregator.get_snapshot().emergency_stop_active is True


def test_update_from_battery_state_sets_percentage():
    aggregator = RobotStatusAggregator()
    aggregator.update_from_battery_state({"percentage": 18})
    assert aggregator.get_snapshot().battery_percentage == 18.0


def test_update_from_package_status_sets_package_and_carrying_state():
    aggregator = RobotStatusAggregator()
    aggregator.update_from_package_status(
        {"package_id": "PKG-001", "package_state": "carrying", "message": "Picked up"}
    )
    snapshot = aggregator.get_snapshot()
    assert snapshot.package_id == "PKG-001"
    assert snapshot.carrying_package is True


def test_get_snapshot_returns_correct_health_level():
    aggregator = RobotStatusAggregator()
    aggregator.update_from_battery_state({"percentage": 9})
    assert aggregator.get_snapshot().health_level == RobotHealthLevel.CRITICAL


def test_summary_includes_expected_keys():
    aggregator = RobotStatusAggregator()
    summary = aggregator.summary()
    assert "robot_name" in summary
    assert "health_level" in summary
    assert "current_zone" in summary
    assert "carrying_package" in summary


def test_diagnostic_logger_add_event_and_limit():
    logger = DiagnosticLogger(max_events=2)
    logger.add_event(logger.event_from_snapshot(build_robot_status_snapshot("warehouse_bot_01", "receiving", "idle")))
    logger.add_event(logger.event_from_snapshot(build_robot_status_snapshot("warehouse_bot_01", "storage_a", "moving", battery_percentage=20)))
    logger.add_event(logger.event_from_snapshot(build_robot_status_snapshot("warehouse_bot_01", "packing", "error", battery_percentage=5, emergency_stop_active=True)))
    assert len(logger.events) == 2


def test_event_from_snapshot_creates_ok_and_critical_events():
    logger = DiagnosticLogger()
    ok_event = logger.event_from_snapshot(build_robot_status_snapshot("warehouse_bot_01", "receiving", "idle", battery_percentage=80))
    critical_event = logger.event_from_snapshot(
        build_robot_status_snapshot(
            "warehouse_bot_01",
            "packing",
            "error",
            battery_percentage=5,
            emergency_stop_active=True,
            last_event="Emergency stop active",
        )
    )
    assert ok_event.health_level == RobotHealthLevel.OK
    assert critical_event.health_level == RobotHealthLevel.CRITICAL


def test_list_events_filters_and_latest_event_work():
    logger = DiagnosticLogger()
    first = logger.add_event(
        logger.event_from_snapshot(build_robot_status_snapshot("warehouse_bot_01", "receiving", "idle", battery_percentage=80))
    )
    second = logger.add_event(
        logger.event_from_snapshot(build_robot_status_snapshot("warehouse_bot_01", "storage_a", "moving", battery_percentage=20))
    )
    filtered = logger.list_events(source=DiagnosticSource.STATUS, min_level=RobotHealthLevel.WARNING)
    assert first not in filtered
    assert second in filtered
    assert logger.latest_event() == second


def test_diagnostic_summary_includes_expected_keys():
    logger = DiagnosticLogger()
    logger.add_event(logger.event_from_snapshot(build_robot_status_snapshot("warehouse_bot_01", "receiving", "idle", battery_percentage=80)))
    summary = logger.summary()
    assert "total_events" in summary
    assert "latest_level" in summary
    assert "latest_message" in summary
