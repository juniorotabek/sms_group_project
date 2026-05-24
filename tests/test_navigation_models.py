import pytest

from smart_warehouse_robot.common.models import NavigationGoal, NavigationProgress, NavigationStatus, WarehouseZone


def test_create_navigation_goal_successfully():
    goal = NavigationGoal(
        source_zone="receiving",
        destination_zone="packing",
        priority=3,
        task_id="TASK-001",
    )

    assert goal.source_zone == WarehouseZone.RECEIVING
    assert goal.destination_zone == WarehouseZone.PACKING
    assert goal.status == NavigationStatus.IDLE
    assert goal.goal_id.startswith("GOAL-")


def test_navigation_goal_json_round_trip():
    goal = NavigationGoal(
        goal_id="GOAL-001",
        task_id="TASK-001",
        source_zone="receiving",
        destination_zone="shipping",
        priority=4,
        status="moving",
    )

    restored = NavigationGoal.from_json(goal.to_json())
    assert restored.to_dict() == goal.to_dict()


def test_invalid_navigation_status_raises_value_error():
    with pytest.raises(ValueError, match="Invalid navigation status"):
        NavigationGoal(
            source_zone="receiving",
            destination_zone="packing",
            priority=3,
            status="teleporting",
        )


def test_progress_below_zero_becomes_zero():
    progress = NavigationProgress(
        goal_id="GOAL-001",
        task_id="TASK-001",
        current_zone="receiving",
        destination_zone="packing",
        progress_percent=-10,
        status="moving",
        message="moving",
    )
    assert progress.progress_percent == 0.0


def test_progress_above_hundred_becomes_hundred():
    progress = NavigationProgress(
        goal_id="GOAL-001",
        task_id="TASK-001",
        current_zone="packing",
        destination_zone="packing",
        progress_percent=120,
        status="arrived",
        message="arrived",
    )
    assert progress.progress_percent == 100.0


def test_terminal_statuses_work():
    goal = NavigationGoal(
        source_zone="receiving",
        destination_zone="shipping",
        priority=3,
        status="arrived",
    )
    assert goal.is_terminal() is True
    goal.mark_cancelled()
    assert goal.status == NavigationStatus.CANCELLED
    assert goal.is_terminal() is True
