from smart_warehouse_robot.common.constants import CHARGING_STATION_ZONE
from smart_warehouse_robot.common.helpers import (
    build_battery_state,
    build_charge_navigation_goal,
    classify_battery_level,
    should_emergency_stop_for_battery,
    should_return_to_charge,
)
from smart_warehouse_robot.common.models import BatteryLevel, ChargingStatus, WarehouseZone
from smart_warehouse_robot.services.battery import BatterySimulator


def test_threshold_helpers_work():
    assert classify_battery_level(100) == BatteryLevel.FULL
    assert classify_battery_level(50) == BatteryLevel.NORMAL
    assert classify_battery_level(20) == BatteryLevel.LOW
    assert classify_battery_level(5) == BatteryLevel.CRITICAL
    assert classify_battery_level(0) == BatteryLevel.EMPTY
    assert should_return_to_charge(20) is True
    assert should_emergency_stop_for_battery(5) is True


def test_build_charge_navigation_goal_uses_charging_station():
    state = build_battery_state("warehouse_bot_01", 20, "storage_a")
    from smart_warehouse_robot.common.helpers import build_charge_command

    command = build_charge_command(state)
    goal = build_charge_navigation_goal(command)
    assert goal.destination_zone.value == CHARGING_STATION_ZONE


def test_drain_decreases_percentage():
    simulator = BatterySimulator(start_percentage=100.0)
    state = simulator.drain()
    assert state.percentage == 95.0


def test_charge_increases_percentage():
    simulator = BatterySimulator(start_percentage=50.0, start_zone=WarehouseZone.CHARGING_STATION)
    simulator.start_charging()
    state = simulator.charge()
    assert state.percentage == 60.0


def test_battery_never_below_zero():
    simulator = BatterySimulator(start_percentage=2.0, drain_percent=10.0)
    state = simulator.drain()
    assert state.percentage == 0.0


def test_battery_never_above_hundred():
    simulator = BatterySimulator(start_percentage=95.0, charge_percent=10.0, start_zone=WarehouseZone.CHARGING_STATION)
    simulator.start_charging()
    state = simulator.charge()
    assert state.percentage == 100.0


def test_low_battery_needs_return():
    simulator = BatterySimulator(start_percentage=20.0)
    assert simulator.needs_return_to_charge() is True


def test_critical_battery_needs_warning():
    simulator = BatterySimulator(start_percentage=5.0)
    assert simulator.needs_emergency_stop() is True


def test_start_return_to_charge_returns_active_command():
    simulator = BatterySimulator(start_percentage=20.0)
    command = simulator.start_return_to_charge()
    assert command.active is True
    assert simulator.get_state().charging_status == ChargingStatus.RETURNING_TO_CHARGE


def test_start_charging_sets_charging():
    simulator = BatterySimulator(start_percentage=20.0, start_zone=WarehouseZone.CHARGING_STATION)
    simulator.start_return_to_charge()
    state = simulator.start_charging()
    assert state.charging_status == ChargingStatus.CHARGING


def test_stop_charging_if_full_sets_charged():
    simulator = BatterySimulator(start_percentage=95.0, charge_percent=10.0, start_zone=WarehouseZone.CHARGING_STATION)
    simulator.start_return_to_charge()
    simulator.start_charging()
    simulator.charge()
    state = simulator.stop_charging_if_full()
    assert state.charging_status == ChargingStatus.CHARGED


def test_summary_includes_expected_keys():
    simulator = BatterySimulator(start_percentage=50.0)
    summary = simulator.summary()
    assert "percentage" in summary
    assert "level" in summary
    assert "charging_status" in summary
    assert "current_zone" in summary
    assert "needs_return_to_charge" in summary
    assert "needs_emergency_stop" in summary
