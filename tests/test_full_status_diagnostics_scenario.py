from smart_warehouse_robot.common.models import RobotHealthLevel
from smart_warehouse_robot.services.status import DiagnosticLogger, RobotStatusAggregator


def test_full_status_diagnostics_scenario() -> None:
    aggregator = RobotStatusAggregator()
    aggregator.update_from_task_status({"event_type": "task_started", "task_id": "TASK-001"})
    aggregator.update_from_navigation_progress(
        {
            "goal_id": "GOAL-001",
            "current_zone": "packing",
            "status": "blocked",
            "message": "Navigation blocked by safety stop.",
        }
    )
    aggregator.update_from_battery_state({"percentage": 9})
    aggregator.update_from_package_status(
        {
            "package_id": "PKG-001",
            "package_state": "carrying",
            "message": "Package onboard.",
        }
    )
    aggregator.update_from_emergency_stop(
        {"active": True, "reason": "Emergency stop active because of obstacle."}
    )
    snapshot = aggregator.get_snapshot()

    logger = DiagnosticLogger()
    event = logger.add_event(logger.event_from_snapshot(snapshot))

    assert snapshot.health_level == RobotHealthLevel.CRITICAL
    assert snapshot.active_task_id == "TASK-001"
    assert snapshot.active_navigation_goal_id == "GOAL-001"
    assert snapshot.carrying_package is True
    assert event.health_level == RobotHealthLevel.CRITICAL
