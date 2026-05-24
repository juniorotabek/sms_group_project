"""Pure package handling logic for pickup and dropoff simulation."""

from __future__ import annotations

from typing import Optional

from smart_warehouse_robot.common.constants import DEFAULT_ROBOT_NAME
from smart_warehouse_robot.common.helpers import build_package_info, build_package_status_event
from smart_warehouse_robot.common.models import PackageInfo, PackageState, PackageStatusEvent, WarehouseZone


class PackageHandler:
    """Track one active package for the robot and simulate pickup/dropoff."""

    def __init__(self, robot_name: str = DEFAULT_ROBOT_NAME) -> None:
        self.robot_name = robot_name
        self._current_package: Optional[PackageInfo] = None

    def has_package(self) -> bool:
        """Return True when the robot is currently carrying a package."""
        return self._current_package is not None and self._current_package.state == PackageState.CARRYING

    def get_current_package(self) -> Optional[PackageInfo]:
        """Return the current package if one exists."""
        return self._current_package

    def create_package(
        self,
        source_zone: WarehouseZone,
        destination_zone: WarehouseZone,
        task_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> PackageInfo:
        """Create a package in waiting state and store it as the current package."""
        self._current_package = build_package_info(
            package_id=None,
            source_zone=source_zone,
            destination_zone=destination_zone,
            task_id=task_id,
            notes=notes,
        )
        return self._current_package

    def pickup(self, package_info: Optional[PackageInfo] = None) -> PackageStatusEvent:
        """Mark the current package as being carried by the robot."""
        if self.has_package():
            raise ValueError("Cannot pickup package: robot is already carrying a package.")

        if package_info is not None:
            self._current_package = package_info

        if self._current_package is None:
            raise ValueError("Cannot pickup package: no package is available.")

        self._current_package.mark_carrying(self.robot_name)
        return build_package_status_event(
            event_type="package_picked_up",
            package_info=self._current_package,
            robot_name=self.robot_name,
            message="Package pickup completed.",
        )

    def dropoff(self) -> PackageStatusEvent:
        """Mark the carried package as delivered."""
        if self._current_package is None or self._current_package.state != PackageState.CARRYING:
            raise ValueError("Cannot dropoff package: robot is not carrying a package.")

        self._current_package.mark_delivered()
        event = build_package_status_event(
            event_type="package_delivered",
            package_info=self._current_package,
            robot_name=self.robot_name,
            message="Package dropoff completed.",
        )
        return event

    def reset(self) -> PackageStatusEvent:
        """Clear the current package and publish a reset event."""
        previous_package = self._current_package
        self._current_package = None
        return build_package_status_event(
            event_type="package_reset",
            package_info=previous_package,
            robot_name=self.robot_name,
            message="Package handler reset.",
        )

    def summary(self) -> dict:
        """Return a compact summary for CLI output and logs."""
        return {
            "robot_name": self.robot_name,
            "has_package": self.has_package(),
            "current_package_id": self._current_package.package_id if self._current_package is not None else None,
            "package_state": self._current_package.state.value if self._current_package is not None else PackageState.NONE.value,
        }
