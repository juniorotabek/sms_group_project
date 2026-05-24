from smart_warehouse_robot.common.models import NavigationStatus, WarehouseZone
from smart_warehouse_robot.services.navigation import NavigationSimulator
from smart_warehouse_robot.common.models import NavigationGoal


def make_goal() -> NavigationGoal:
    return NavigationGoal(
        goal_id="GOAL-001",
        task_id="TASK-001",
        source_zone="receiving",
        destination_zone="shipping",
        priority=3,
    )


def test_set_goal_marks_goal_received():
    simulator = NavigationSimulator()
    goal = simulator.set_goal(make_goal())

    assert goal.status == NavigationStatus.GOAL_RECEIVED


def test_first_step_moves_status_to_moving():
    simulator = NavigationSimulator(step_percent=25.0)
    simulator.set_goal(make_goal())

    progress = simulator.step()

    assert progress.status == NavigationStatus.MOVING


def test_progress_increases_by_configured_step():
    simulator = NavigationSimulator(step_percent=40.0)
    simulator.set_goal(make_goal())

    progress = simulator.step()

    assert progress.progress_percent == 40.0


def test_arrival_at_hundred_marks_arrived():
    simulator = NavigationSimulator(step_percent=50.0)
    simulator.set_goal(make_goal())
    simulator.step()
    progress = simulator.step()

    assert progress.progress_percent == 100.0
    assert progress.status == NavigationStatus.ARRIVED
    assert progress.current_zone == WarehouseZone.SHIPPING


def test_no_active_goal_returns_idle_progress():
    simulator = NavigationSimulator()

    progress = simulator.step()

    assert progress.status == NavigationStatus.IDLE
    assert progress.progress_percent == 0.0


def test_cancel_goal_marks_cancelled():
    simulator = NavigationSimulator()
    simulator.set_goal(make_goal())

    progress = simulator.cancel_current_goal()

    assert progress.status == NavigationStatus.CANCELLED


def test_block_goal_marks_blocked_and_stops_progress():
    simulator = NavigationSimulator(step_percent=25.0)
    simulator.set_goal(make_goal())
    blocked = simulator.block_current_goal("Obstacle detected")
    after_block = simulator.step()

    assert blocked.status == NavigationStatus.BLOCKED
    assert after_block.status == NavigationStatus.BLOCKED
    assert after_block.progress_percent == 0.0


def test_reset_if_terminal_clears_completed_goal():
    simulator = NavigationSimulator(step_percent=100.0)
    simulator.set_goal(make_goal())
    simulator.step()

    simulator.reset_if_terminal()

    assert simulator.get_current_goal() is None
