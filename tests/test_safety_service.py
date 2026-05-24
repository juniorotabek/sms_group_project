from smart_warehouse_robot.common.helpers import (
    build_obstacle_reading,
    classify_obstacle_severity,
    should_trigger_emergency_stop,
)
from smart_warehouse_robot.common.models import ObstacleSeverity, SafetyState
from smart_warehouse_robot.services.safety import SafetyMonitor


def test_no_detection_gives_clear():
    assert classify_obstacle_severity(6.0, False) == ObstacleSeverity.CLEAR


def test_distance_three_gives_low():
    assert classify_obstacle_severity(3.0, True) == ObstacleSeverity.LOW


def test_distance_one_point_five_gives_medium():
    assert classify_obstacle_severity(1.5, True) == ObstacleSeverity.MEDIUM


def test_distance_zero_point_eight_gives_high():
    assert classify_obstacle_severity(0.8, True) == ObstacleSeverity.HIGH


def test_distance_zero_point_two_five_gives_critical():
    assert classify_obstacle_severity(0.25, True) == ObstacleSeverity.CRITICAL


def test_high_and_critical_trigger_emergency_stop():
    assert should_trigger_emergency_stop(build_obstacle_reading("storage_a", 0.8, True)) is True
    assert should_trigger_emergency_stop(build_obstacle_reading("storage_a", 0.25, True)) is True


def test_low_and_medium_do_not_trigger_emergency_stop():
    assert should_trigger_emergency_stop(build_obstacle_reading("storage_a", 3.0, True)) is False
    assert should_trigger_emergency_stop(build_obstacle_reading("storage_a", 1.5, True)) is False


def test_clear_keeps_safe():
    monitor = SafetyMonitor()
    command = monitor.process_reading(build_obstacle_reading("storage_a", 6.0, False))

    assert command is None
    assert monitor.get_safety_state() == SafetyState.SAFE


def test_medium_sets_warning():
    monitor = SafetyMonitor()
    command = monitor.process_reading(build_obstacle_reading("storage_a", 1.5, True))

    assert command is None
    assert monitor.get_safety_state() == SafetyState.WARNING


def test_high_triggers_emergency_command():
    monitor = SafetyMonitor()
    command = monitor.process_reading(build_obstacle_reading("storage_a", 0.8, True))

    assert command is not None
    assert command.active is True


def test_critical_triggers_emergency_command():
    monitor = SafetyMonitor()
    command = monitor.process_reading(build_obstacle_reading("storage_a", 0.25, True))

    assert command is not None
    assert command.active is True


def test_emergency_remains_active_until_cleared():
    monitor = SafetyMonitor()
    monitor.process_reading(build_obstacle_reading("storage_a", 0.25, True))
    monitor.process_reading(build_obstacle_reading("storage_a", 6.0, False))

    assert monitor.is_emergency_active() is True


def test_clear_emergency_sets_safe():
    monitor = SafetyMonitor()
    monitor.process_reading(build_obstacle_reading("storage_a", 0.25, True))
    command = monitor.clear_emergency()

    assert command.active is False
    assert monitor.get_safety_state() == SafetyState.SAFE


def test_summary_includes_expected_keys():
    monitor = SafetyMonitor()
    monitor.process_reading(build_obstacle_reading("storage_a", 1.5, True))
    summary = monitor.summary()

    assert "safety_state" in summary
    assert "emergency_active" in summary
    assert "latest_reading_id" in summary
    assert "latest_severity" in summary
    assert "latest_zone" in summary
