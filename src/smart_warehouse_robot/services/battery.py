"""Pure battery simulation logic for low-battery and charging behavior."""

from __future__ import annotations

from smart_warehouse_robot.common.constants import (
    CHARGING_STATION_ZONE,
    DEFAULT_BATTERY_CHARGE_PERCENT,
    DEFAULT_BATTERY_DRAIN_PERCENT,
    DEFAULT_CRITICAL_BATTERY_THRESHOLD,
    DEFAULT_LOW_BATTERY_THRESHOLD,
    DEFAULT_ROBOT_NAME,
)
from smart_warehouse_robot.common.helpers import build_battery_state, build_charge_command, should_emergency_stop_for_battery, should_return_to_charge
from smart_warehouse_robot.common.models import BatteryState, ChargingStatus, ChargeCommand, WarehouseZone


class BatterySimulator:
    """Simulate battery drain, charging, and return-to-charge behavior."""

    def __init__(
        self,
        robot_name: str = DEFAULT_ROBOT_NAME,
        start_percentage: float = 100.0,
        start_zone: WarehouseZone = WarehouseZone.RECEIVING,
        drain_percent: float = DEFAULT_BATTERY_DRAIN_PERCENT,
        charge_percent: float = DEFAULT_BATTERY_CHARGE_PERCENT,
        low_threshold: float = DEFAULT_LOW_BATTERY_THRESHOLD,
        critical_threshold: float = DEFAULT_CRITICAL_BATTERY_THRESHOLD,
    ) -> None:
        self.robot_name = robot_name
        self.drain_percent = float(drain_percent)
        self.charge_percent = float(charge_percent)
        self.low_threshold = float(low_threshold)
        self.critical_threshold = float(critical_threshold)
        self._active_charge_command: ChargeCommand | None = None
        self._state = build_battery_state(
            robot_name=robot_name,
            percentage=start_percentage,
            current_zone=start_zone,
            charging_status=ChargingStatus.NOT_CHARGING,
        )

    def get_state(self) -> BatteryState:
        """Return the current battery state."""
        return self._state

    def drain(self) -> BatteryState:
        """Decrease battery unless the robot is currently charging."""
        if self._state.charging_status == ChargingStatus.CHARGING:
            return self._state

        self._state = BatteryState(
            battery_id=self._state.battery_id,
            robot_name=self.robot_name,
            percentage=self._state.percentage - self.drain_percent,
            charging_status=self._state.charging_status,
            current_zone=self._state.current_zone,
            voltage=self._state.voltage,
            temperature_celsius=self._state.temperature_celsius,
        )
        return self._state

    def charge(self) -> BatteryState:
        """Increase battery only when the robot is in charging state."""
        if self._state.charging_status != ChargingStatus.CHARGING:
            return self._state

        self._state = BatteryState(
            battery_id=self._state.battery_id,
            robot_name=self.robot_name,
            percentage=self._state.percentage + self.charge_percent,
            charging_status=ChargingStatus.CHARGING,
            current_zone=self._state.current_zone,
            voltage=self._state.voltage,
            temperature_celsius=self._state.temperature_celsius,
        )
        return self._state

    def set_current_zone(self, zone: WarehouseZone) -> BatteryState:
        """Update the robot's current zone while preserving the rest of the state."""
        self._state = BatteryState(
            battery_id=self._state.battery_id,
            robot_name=self._state.robot_name,
            percentage=self._state.percentage,
            level=self._state.level,
            charging_status=self._state.charging_status,
            current_zone=zone,
            voltage=self._state.voltage,
            temperature_celsius=self._state.temperature_celsius,
        )
        return self._state

    def start_return_to_charge(self) -> ChargeCommand:
        """Create and track an active return-to-charge command."""
        self._active_charge_command = build_charge_command(self._state)
        self._active_charge_command.activate()
        self._state = BatteryState(
            battery_id=self._state.battery_id,
            robot_name=self._state.robot_name,
            percentage=self._state.percentage,
            charging_status=ChargingStatus.RETURNING_TO_CHARGE,
            current_zone=self._state.current_zone,
            voltage=self._state.voltage,
            temperature_celsius=self._state.temperature_celsius,
        )
        return self._active_charge_command

    def start_charging(self) -> BatteryState:
        """Start charging when the robot is at the charging station."""
        if self._state.current_zone == WarehouseZone(CHARGING_STATION_ZONE):
            self._state = BatteryState(
                battery_id=self._state.battery_id,
                robot_name=self._state.robot_name,
                percentage=self._state.percentage,
                charging_status=ChargingStatus.CHARGING,
                current_zone=self._state.current_zone,
                voltage=self._state.voltage,
                temperature_celsius=self._state.temperature_celsius,
            )
        return self._state

    def stop_charging_if_full(self) -> BatteryState:
        """Mark charging complete once the battery reaches 100 percent."""
        if self._state.percentage >= 100.0:
            self._state = BatteryState(
                battery_id=self._state.battery_id,
                robot_name=self._state.robot_name,
                percentage=100.0,
                charging_status=ChargingStatus.CHARGED,
                current_zone=self._state.current_zone,
                voltage=self._state.voltage,
                temperature_celsius=self._state.temperature_celsius,
            )
            if self._active_charge_command is not None:
                self._active_charge_command.clear()
        return self._state

    def needs_return_to_charge(self) -> bool:
        """Return True when the battery is at or below the low threshold."""
        return should_return_to_charge(self._state.percentage, self.low_threshold)

    def needs_emergency_stop(self) -> bool:
        """Return True when the battery is at or below the critical threshold."""
        return should_emergency_stop_for_battery(self._state.percentage, self.critical_threshold)

    def summary(self) -> dict:
        """Return a compact summary for CLI and logging."""
        return {
            "percentage": self._state.percentage,
            "level": self._state.level.value,
            "charging_status": self._state.charging_status.value,
            "current_zone": self._state.current_zone.value,
            "needs_return_to_charge": self.needs_return_to_charge(),
            "needs_emergency_stop": self.needs_emergency_stop(),
        }
