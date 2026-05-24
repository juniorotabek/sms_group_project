from smart_warehouse_robot.common.models import NavigationStatus, RobotHealthLevel
from smart_warehouse_robot.services.navigation import NavigationSimulator
from smart_warehouse_robot.services.safety import SafetyMonitor
from smart_warehouse_robot.services.status import DiagnosticLogger, RobotStatusAggregator
from tests.helpers.scenario_builders import build_sample_navigation_goal, build_sample_obstacle_reading


def test_full_emergency_stop_scenario() -> None:
    goal = build_sample_navigation_goal()
    simulator = NavigationSimulator(step_percent=25.0)
    simulator.set_goal(goal)
    moving_progress = simulator.step()
    assert moving_progress.status == NavigationStatus.MOVING

    reading = build_sample_obstacle_reading()
    monitor = SafetyMonitor()
    command = monitor.process_reading(reading)
    assert command is not None
    blocked_progress = simulator.block_current_goal(command.reason)
    assert blocked_progress.status == NavigationStatus.BLOCKED

    aggregator = RobotStatusAggregator()
    aggregator.update_from_navigation_progress(blocked_progress.to_dict())
    aggregator.update_from_emergency_stop(command.to_dict())
    snapshot = aggregator.get_snapshot()

    logger = DiagnosticLogger()
    event = logger.add_event(logger.event_from_snapshot(snapshot))

    assert snapshot.emergency_stop_active is True
    assert snapshot.health_level == RobotHealthLevel.CRITICAL
    assert event.health_level == RobotHealthLevel.CRITICAL
