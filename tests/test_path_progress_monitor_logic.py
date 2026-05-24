import json

import pytest

from smart_warehouse_robot.common.models import NavigationGoal
from smart_warehouse_robot.nodes.path_progress_monitor import progress_to_ros_message, safe_parse_navigation_goal
from smart_warehouse_robot.services.navigation import NavigationSimulator


def test_safe_parse_navigation_goal_parses_valid_json():
    goal = NavigationGoal(
        source_zone="receiving",
        destination_zone="shipping",
        priority=3,
        task_id="TASK-001",
    )

    parsed = safe_parse_navigation_goal(goal.to_json())

    assert parsed.goal_id == goal.goal_id


def test_safe_parse_navigation_goal_raises_value_error_on_invalid_json():
    with pytest.raises(ValueError):
        safe_parse_navigation_goal("{not valid json}")


def test_progress_to_ros_message_produces_json_string():
    simulator = NavigationSimulator(step_percent=25.0)
    simulator.set_goal(
        NavigationGoal(
            source_zone="receiving",
            destination_zone="packing",
            priority=3,
            task_id="TASK-001",
        )
    )
    progress = simulator.step()
    message = progress_to_ros_message(progress)
    payload = json.loads(message.data)

    assert payload["goal_id"] == progress.goal_id
    assert payload["status"] == progress.status.value
