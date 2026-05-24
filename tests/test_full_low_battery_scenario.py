from smart_warehouse_robot.common.constants import CHARGING_STATION_ZONE
from smart_warehouse_robot.common.helpers import build_charge_navigation_goal
from smart_warehouse_robot.common.models import ChargingStatus, WarehouseZone
from smart_warehouse_robot.services.battery import BatterySimulator
from smart_warehouse_robot.services.navigation import NavigationSimulator


def test_full_low_battery_scenario() -> None:
    battery = BatterySimulator(start_percentage=20.0, start_zone=WarehouseZone.STORAGE_A)
    assert battery.needs_return_to_charge() is True

    charge_command = battery.start_return_to_charge()
    goal = build_charge_navigation_goal(charge_command)
    assert goal.destination_zone.value == CHARGING_STATION_ZONE

    simulator = NavigationSimulator(step_percent=100.0)
    simulator.set_goal(goal)
    arrival = simulator.step()
    assert arrival.status.value == "arrived"

    battery.set_current_zone(WarehouseZone.CHARGING_STATION)
    charging_state = battery.start_charging()
    assert charging_state.charging_status == ChargingStatus.CHARGING

    while battery.get_state().percentage < 100.0:
        battery.charge()
        battery.stop_charging_if_full()

    assert battery.get_state().charging_status in {ChargingStatus.CHARGING, ChargingStatus.CHARGED}
    assert battery.get_state().current_zone == WarehouseZone.CHARGING_STATION
