import pytest

from smart_warehouse_robot.common.models import PackageState, WarehouseZone
from smart_warehouse_robot.services.package_handler import PackageHandler


def test_starts_with_no_package():
    handler = PackageHandler()
    assert handler.get_current_package() is None


def test_create_package_creates_waiting_package():
    handler = PackageHandler()
    package_info = handler.create_package(WarehouseZone.STORAGE_A, WarehouseZone.SHIPPING)
    assert package_info.state == PackageState.WAITING_FOR_PICKUP


def test_pickup_marks_carrying():
    handler = PackageHandler()
    handler.create_package(WarehouseZone.STORAGE_A, WarehouseZone.SHIPPING)
    event = handler.pickup()
    assert event.package_state == PackageState.CARRYING


def test_pickup_while_already_carrying_raises_value_error():
    handler = PackageHandler()
    handler.create_package(WarehouseZone.STORAGE_A, WarehouseZone.SHIPPING)
    handler.pickup()
    with pytest.raises(ValueError, match="already carrying"):
        handler.pickup()


def test_dropoff_marks_delivered():
    handler = PackageHandler()
    handler.create_package(WarehouseZone.STORAGE_A, WarehouseZone.SHIPPING)
    handler.pickup()
    event = handler.dropoff()
    assert event.package_state == PackageState.DELIVERED


def test_dropoff_without_package_raises_value_error():
    handler = PackageHandler()
    with pytest.raises(ValueError, match="not carrying"):
        handler.dropoff()


def test_reset_clears_package():
    handler = PackageHandler()
    handler.create_package(WarehouseZone.STORAGE_A, WarehouseZone.SHIPPING)
    handler.reset()
    assert handler.get_current_package() is None


def test_summary_includes_expected_keys():
    handler = PackageHandler()
    summary = handler.summary()
    assert "robot_name" in summary
    assert "has_package" in summary
    assert "current_package_id" in summary
    assert "package_state" in summary
