import json

from smart_warehouse_robot.common.models import ObstacleSeverity, WarehouseZone
from smart_warehouse_robot.nodes.obstacle_detector import create_simulated_obstacle_readings, obstacle_reading_to_ros_message


def test_create_simulated_obstacle_readings_returns_five_readings():
    readings = create_simulated_obstacle_readings(WarehouseZone.STORAGE_A)
    assert len(readings) == 5


def test_simulated_readings_include_all_expected_severities():
    readings = create_simulated_obstacle_readings(WarehouseZone.STORAGE_A)
    severities = {reading.severity for reading in readings}

    assert severities == {
        ObstacleSeverity.CLEAR,
        ObstacleSeverity.LOW,
        ObstacleSeverity.MEDIUM,
        ObstacleSeverity.HIGH,
        ObstacleSeverity.CRITICAL,
    }


def test_obstacle_reading_to_ros_message_produces_json_string():
    reading = create_simulated_obstacle_readings(WarehouseZone.STORAGE_A)[3]
    message = obstacle_reading_to_ros_message(reading)
    payload = json.loads(message.data)

    assert payload["reading_id"] == reading.reading_id
    assert payload["severity"] == reading.severity.value
