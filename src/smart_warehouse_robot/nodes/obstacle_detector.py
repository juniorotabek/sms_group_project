"""ROS 1 node that simulates obstacle readings for safety testing."""

from __future__ import annotations

from itertools import cycle

from smart_warehouse_robot.common.constants import DEFAULT_OBSTACLE_DETECTION_INTERVAL_SECONDS, OBSTACLE_TOPIC
from smart_warehouse_robot.common.helpers import build_obstacle_reading, format_obstacle_summary, parse_warehouse_zone
from smart_warehouse_robot.common.models import ObstacleReading, WarehouseZone

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def create_simulated_obstacle_readings(zone: WarehouseZone) -> list[ObstacleReading]:
    """Create a fixed sequence of simulated obstacle readings."""
    return [
        build_obstacle_reading(zone, 6.0, False, "No obstacle detected"),
        build_obstacle_reading(zone, 3.0, True, "Low-severity obstacle detected"),
        build_obstacle_reading(zone, 1.5, True, "Medium obstacle ahead"),
        build_obstacle_reading(zone, 0.8, True, "High obstacle risk"),
        build_obstacle_reading(zone, 0.25, True, "Critical obstacle detected"),
    ]


def obstacle_reading_to_ros_message(reading: ObstacleReading) -> String:
    """Convert an obstacle reading into a ROS String message."""
    return String(data=reading.to_json())


class ObstacleDetectorNode:
    """Publish simulated obstacle readings to the safety topic."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run ObstacleDetectorNode.")

        detection_interval_seconds = float(
            rospy.get_param("~detection_interval_seconds", DEFAULT_OBSTACLE_DETECTION_INTERVAL_SECONDS)
        )
        self.simulation_enabled = bool(rospy.get_param("~simulation_enabled", True))
        default_zone = parse_warehouse_zone(rospy.get_param("~default_zone", "storage_a"))

        self.publisher = rospy.Publisher(OBSTACLE_TOPIC, String, queue_size=10)
        self._reading_iterator = cycle(create_simulated_obstacle_readings(default_zone))
        self.timer = None
        if self.simulation_enabled:
            self.timer = rospy.Timer(rospy.Duration(detection_interval_seconds), self.publish_simulated_reading)

        rospy.loginfo(
            "ObstacleDetectorNode started. Publishing to %s with simulation_enabled=%s",
            OBSTACLE_TOPIC,
            self.simulation_enabled,
        )

    def publish_simulated_reading(self, _event=None) -> None:
        """Publish the next simulated obstacle reading."""
        reading = next(self._reading_iterator)
        self.publisher.publish(obstacle_reading_to_ros_message(reading))
        rospy.loginfo("%s", format_obstacle_summary(reading))


def main() -> None:
    """Run the obstacle detector node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("obstacle_detector")
    ObstacleDetectorNode()
    rospy.spin()


if __name__ == "__main__":
    main()
