from smart_warehouse_robot.common.helpers import classify_battery_level
from smart_warehouse_robot.common.models import BatteryLevel, BatteryState, ChargeCommand, ChargingStatus


def test_create_battery_state_successfully():
    state = BatteryState(
        robot_name="warehouse_bot_01",
        percentage=20,
        charging_status="not_charging",
        current_zone="storage_a",
    )

    assert state.robot_name == "warehouse_bot_01"
    assert state.level == BatteryLevel.LOW


def test_battery_state_json_round_trip():
    state = BatteryState(
        battery_id="BAT-001",
        robot_name="warehouse_bot_01",
        percentage=50,
        level="normal",
        charging_status="not_charging",
        current_zone="packing",
    )

    restored = BatteryState.from_json(state.to_json())
    assert restored.to_dict() == state.to_dict()


def test_percentage_below_zero_clamps_to_zero():
    state = BatteryState(robot_name="warehouse_bot_01", percentage=-5, charging_status="not_charging", current_zone="receiving")
    assert state.percentage == 0.0


def test_percentage_above_hundred_clamps_to_hundred():
    state = BatteryState(robot_name="warehouse_bot_01", percentage=120, charging_status="not_charging", current_zone="receiving")
    assert state.percentage == 100.0


def test_classify_levels_correctly():
    assert classify_battery_level(100) == BatteryLevel.FULL
    assert classify_battery_level(50) == BatteryLevel.NORMAL
    assert classify_battery_level(20) == BatteryLevel.LOW
    assert classify_battery_level(5) == BatteryLevel.CRITICAL
    assert classify_battery_level(0) == BatteryLevel.EMPTY


def test_battery_state_predicates_work():
    state = BatteryState(robot_name="warehouse_bot_01", percentage=5, charging_status="charging", current_zone="charging_station")
    assert state.is_low() is True
    assert state.is_critical() is True
    assert state.is_empty() is False
    assert state.is_charging() is True


def test_charge_command_json_round_trip():
    command = ChargeCommand(
        command_id="CHARGE-001",
        robot_name="warehouse_bot_01",
        active=True,
        reason="Low battery",
        target_zone="charging_station",
        battery_percentage=20,
        charging_status="returning_to_charge",
        source_battery_id="BAT-001",
    )

    restored = ChargeCommand.from_json(command.to_json())
    assert restored.to_dict() == command.to_dict()


def test_active_charge_command_works():
    command = ChargeCommand(
        robot_name="warehouse_bot_01",
        active=False,
        reason="Low battery",
        target_zone="charging_station",
        battery_percentage=20,
        charging_status=ChargingStatus.NOT_CHARGING,
    )
    command.activate()
    assert command.is_active() is True
    command.clear()
    assert command.is_active() is False
