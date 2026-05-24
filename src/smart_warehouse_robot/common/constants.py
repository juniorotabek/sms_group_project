"""Project-wide constants for topics, services, and default values."""

from smart_warehouse_robot.common.models import WarehouseZone


DEFAULT_ROBOT_NAME = "warehouse_bot_01"

TASK_NEW_TOPIC = "/warehouse/tasks/new"
TASK_STATUS_TOPIC = "/warehouse/tasks/status"
NAVIGATION_GOAL_TOPIC = "/warehouse/navigation/goal"
NAVIGATION_PROGRESS_TOPIC = "/warehouse/navigation/progress"
OBSTACLE_TOPIC = "/warehouse/safety/obstacle"
EMERGENCY_STOP_TOPIC = "/warehouse/safety/emergency_stop"
BATTERY_STATE_TOPIC = "/warehouse/battery/state"
RETURN_TO_CHARGE_TOPIC = "/warehouse/battery/return_to_charge"
PACKAGE_STATUS_TOPIC = "/warehouse/package/status"
ROBOT_STATUS_TOPIC = "/warehouse/robot/status"
DIAGNOSTICS_TOPIC = "/warehouse/robot/diagnostics"

PACKAGE_PICKUP_SERVICE = "/warehouse/package/pickup"
PACKAGE_DROPOFF_SERVICE = "/warehouse/package/dropoff"
PACKAGE_RESET_SERVICE = "/warehouse/package/reset"
RETURN_TO_CHARGE_SERVICE = "/warehouse/robot/return_to_charge"

WAREHOUSE_ZONES = [zone.value for zone in WarehouseZone]

DEFAULT_BATTERY_THRESHOLD = 25
DEFAULT_CLI_PRIORITY = 3
DEFAULT_TASK_PUBLISH_INTERVAL_SECONDS = 5.0
DEFAULT_TASK_COMPLETION_CYCLES = 2
DEFAULT_STATUS_PUBLISH_INTERVAL = 3.0
DEFAULT_STATUS_PUBLISH_INTERVAL_SECONDS = 2.0
DEFAULT_DIAGNOSTIC_LOG_INTERVAL_SECONDS = 5.0
DEFAULT_NAVIGATION_STEP_PERCENT = 25.0
DEFAULT_NAVIGATION_UPDATE_SECONDS = 2.0
DEFAULT_OBSTACLE_DETECTION_INTERVAL_SECONDS = 2.0
DEFAULT_OBSTACLE_DISTANCE_THRESHOLD_METERS = 1.0
DEFAULT_CRITICAL_DISTANCE_METERS = 0.4
DEFAULT_BATTERY_PUBLISH_INTERVAL_SECONDS = 3.0
DEFAULT_BATTERY_DRAIN_PERCENT = 5.0
DEFAULT_BATTERY_CHARGE_PERCENT = 10.0
DEFAULT_LOW_BATTERY_THRESHOLD = 25.0
DEFAULT_CRITICAL_BATTERY_THRESHOLD = 10.0
MIN_TASK_PRIORITY = 1
MAX_TASK_PRIORITY = 5
MIN_OBSTACLE_DISTANCE_METERS = 0.0
CHARGING_STATION_ZONE = "charging_station"
DEFAULT_PACKAGE_ID_PREFIX = "PKG"

WAREHOUSE_ZONE_COORDINATES = {
    "receiving": {"x": 0.0, "y": 0.0},
    "storage_a": {"x": 3.0, "y": 1.0},
    "storage_b": {"x": 3.0, "y": -1.0},
    "packing": {"x": 6.0, "y": 0.0},
    "shipping": {"x": 9.0, "y": 0.0},
    "charging_station": {"x": 1.0, "y": -3.0},
}

# Backward-compatible aliases for earlier foundation files.
TASK_TOPIC_NEW = TASK_NEW_TOPIC
DEFAULT_TASK_PUBLISH_INTERVAL = DEFAULT_TASK_PUBLISH_INTERVAL_SECONDS
