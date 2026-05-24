"""ROS 1 node that simulates path progress from navigation goals."""

from __future__ import annotations

from smart_warehouse_robot.common.constants import (
    DEFAULT_NAVIGATION_STEP_PERCENT,
    DEFAULT_NAVIGATION_UPDATE_SECONDS,
    EMERGENCY_STOP_TOPIC,
    NAVIGATION_GOAL_TOPIC,
    NAVIGATION_PROGRESS_TOPIC,
)
from smart_warehouse_robot.common.helpers import format_navigation_progress_summary
from smart_warehouse_robot.common.models import EmergencyStopCommand, NavigationGoal, NavigationProgress, NavigationStatus
from smart_warehouse_robot.services.navigation import NavigationSimulator

try:
    import rospy
    from std_msgs.msg import String
except ImportError:  # pragma: no cover
    rospy = None

    class String:  # pragma: no cover
        def __init__(self, data: str = "") -> None:
            self.data = data


def safe_parse_navigation_goal(message_text: str) -> NavigationGoal:
    """Parse navigation goal JSON from a ROS message."""
    return NavigationGoal.from_json(message_text)


def progress_to_ros_message(progress: NavigationProgress) -> String:
    """Convert navigation progress into a ROS String message."""
    return String(data=progress.to_json())


def safe_parse_emergency_stop_command(message_text: str) -> EmergencyStopCommand:
    """Parse emergency-stop JSON from a ROS message."""
    return EmergencyStopCommand.from_json(message_text)


class PathProgressMonitorNode:
    """Simulate waypoint progress and publish navigation updates."""

    def __init__(self) -> None:
        if rospy is None:  # pragma: no cover
            raise RuntimeError("rospy is required to run PathProgressMonitorNode.")

        step_percent = float(rospy.get_param("~navigation_step_percent", DEFAULT_NAVIGATION_STEP_PERCENT))
        update_seconds = float(rospy.get_param("~navigation_update_seconds", DEFAULT_NAVIGATION_UPDATE_SECONDS))

        self.simulator = NavigationSimulator(step_percent=step_percent)
        self.subscription = rospy.Subscriber(NAVIGATION_GOAL_TOPIC, String, self.handle_goal, queue_size=10)
        self.emergency_subscription = rospy.Subscriber(EMERGENCY_STOP_TOPIC, String, self.handle_emergency_stop, queue_size=10)
        self.progress_publisher = rospy.Publisher(NAVIGATION_PROGRESS_TOPIC, String, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(update_seconds), self.publish_progress_step)
        rospy.loginfo(
            "PathProgressMonitorNode started. Listening on %s and publishing to %s every %.1fs",
            NAVIGATION_GOAL_TOPIC,
            NAVIGATION_PROGRESS_TOPIC,
            update_seconds,
        )

    def handle_goal(self, msg: String) -> None:
        """Accept and publish a newly received navigation goal."""
        try:
            goal = safe_parse_navigation_goal(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse navigation goal: %s", exc)
            return
        self.simulator.set_goal(goal)
        initial_progress = self.simulator.step()
        self.progress_publisher.publish(progress_to_ros_message(initial_progress))
        rospy.loginfo("Received goal and published progress: %s", format_navigation_progress_summary(initial_progress))

    def handle_emergency_stop(self, msg: String) -> None:
        """Block the active navigation goal when an emergency stop becomes active."""
        try:
            command = safe_parse_emergency_stop_command(msg.data)
        except ValueError as exc:
            rospy.logerr("Failed to parse emergency stop command: %s", exc)
            return
        if not command.active:
            rospy.loginfo("Received emergency-stop clear command. Navigation will remain paused until a new goal.")
            return
        progress = self.simulator.block_current_goal(command.reason)
        if progress.status == NavigationStatus.IDLE:
            return
        self.progress_publisher.publish(progress_to_ros_message(progress))
        rospy.logwarn("%s", format_navigation_progress_summary(progress))

    def publish_progress_step(self, _event=None) -> None:
        """Advance the simulator and publish a new progress update."""
        progress = self.simulator.step()
        if progress.status == NavigationStatus.IDLE and progress.goal_id == "GOAL-IDLE":
            return
        self.progress_publisher.publish(progress_to_ros_message(progress))
        rospy.loginfo("%s", format_navigation_progress_summary(progress))
        if progress.status == NavigationStatus.ARRIVED:
            self.simulator.reset_if_terminal()


def main() -> None:
    """Run the path progress monitor node."""
    if rospy is None:
        raise RuntimeError("rospy is not installed. Run this node on Ubuntu with ROS 1 Noetic.")

    rospy.init_node("path_progress_monitor")
    PathProgressMonitorNode()
    rospy.spin()


if __name__ == "__main__":
    main()
