import pytest

from smart_warehouse_robot.common.models import PackageInfo, PackageState, PackageStatusEvent


def test_create_package_info_successfully():
    package_info = PackageInfo(
        package_id="PKG-001",
        source_zone="storage_a",
        destination_zone="shipping",
        state="waiting_for_pickup",
    )
    assert package_info.package_id == "PKG-001"
    assert package_info.state == PackageState.WAITING_FOR_PICKUP


def test_package_info_json_round_trip():
    package_info = PackageInfo(
        package_id="PKG-001",
        source_zone="storage_a",
        destination_zone="shipping",
        state="waiting_for_pickup",
        task_id="TASK-001",
    )
    restored = PackageInfo.from_json(package_info.to_json())
    assert restored.to_dict() == package_info.to_dict()


def test_invalid_package_state_raises_value_error():
    with pytest.raises(ValueError, match="Invalid package state"):
        PackageInfo(
            package_id="PKG-001",
            source_zone="storage_a",
            destination_zone="shipping",
            state="teleporting",
        )


def test_mark_waiting_works():
    package_info = PackageInfo("PKG-001", "storage_a", "shipping", "none")
    package_info.mark_waiting()
    assert package_info.state == PackageState.WAITING_FOR_PICKUP


def test_mark_carrying_sets_carried_by_and_state():
    package_info = PackageInfo("PKG-001", "storage_a", "shipping", "waiting_for_pickup")
    package_info.mark_carrying("warehouse_bot_01")
    assert package_info.state == PackageState.CARRYING
    assert package_info.carried_by == "warehouse_bot_01"


def test_mark_delivered_works():
    package_info = PackageInfo("PKG-001", "storage_a", "shipping", "carrying")
    package_info.mark_delivered()
    assert package_info.state == PackageState.DELIVERED


def test_terminal_state_works():
    package_info = PackageInfo("PKG-001", "storage_a", "shipping", "delivered")
    assert package_info.is_terminal() is True


def test_package_status_event_json_round_trip():
    event = PackageStatusEvent(
        event_id="PKG_EVT-001",
        event_type="package_picked_up",
        package_id="PKG-001",
        package_state="carrying",
        robot_name="warehouse_bot_01",
        message="Package picked up",
        source_zone="storage_a",
        destination_zone="shipping",
    )
    restored = PackageStatusEvent.from_json(event.to_json())
    assert restored.to_dict() == event.to_dict()
