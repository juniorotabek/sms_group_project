from smart_warehouse_robot.common.models import BatteryState, NavigationGoal, ObstacleReading, WarehouseTask


def test_models_module_smoke_imports():
    assert WarehouseTask is not None
    assert NavigationGoal is not None
    assert ObstacleReading is not None
    assert BatteryState is not None
