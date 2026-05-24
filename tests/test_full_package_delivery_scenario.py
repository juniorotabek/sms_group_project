import pytest

from smart_warehouse_robot.common.models import PackageState
from smart_warehouse_robot.services.package_handler import PackageHandler
from tests.helpers.scenario_builders import build_sample_package_info


def test_full_package_delivery_scenario() -> None:
    handler = PackageHandler()
    sample_package = build_sample_package_info()
    created = handler.create_package(
        sample_package.source_zone,
        sample_package.destination_zone,
        task_id=sample_package.task_id,
    )
    pickup_event = handler.pickup(created)
    dropoff_event = handler.dropoff()

    assert pickup_event.package_state == PackageState.CARRYING
    assert dropoff_event.package_state == PackageState.DELIVERED
    assert handler.get_current_package() is not None
    assert handler.get_current_package().state == PackageState.DELIVERED

    empty_handler = PackageHandler()
    with pytest.raises(ValueError):
        empty_handler.dropoff()

    carrying_handler = PackageHandler()
    carrying_handler.create_package(sample_package.source_zone, sample_package.destination_zone)
    carrying_handler.pickup()
    with pytest.raises(ValueError):
        carrying_handler.pickup()
