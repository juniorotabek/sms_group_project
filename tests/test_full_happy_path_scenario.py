from smart_warehouse_robot.common.helpers import build_diagnostic_event
from smart_warehouse_robot.common.models import NavigationStatus, PackageState, RobotHealthLevel, TaskStatus
from smart_warehouse_robot.services.navigation import NavigationSimulator
from smart_warehouse_robot.services.package_handler import PackageHandler
from smart_warehouse_robot.services.status import DiagnosticLogger, RobotStatusAggregator
from smart_warehouse_robot.services.task_queue import TaskQueue
from tests.helpers.scenario_builders import (
    build_sample_navigation_goal,
    build_sample_package_info,
    build_sample_task,
)


def test_full_happy_path_scenario() -> None:
    task = build_sample_task()
    queue = TaskQueue()
    queued_task = queue.add_task(task)
    started_task = queue.start_next_task("warehouse_bot_01")
    assert queued_task.status == TaskStatus.IN_PROGRESS
    assert started_task is not None

    goal = build_sample_navigation_goal()
    simulator = NavigationSimulator(step_percent=50.0)
    simulator.set_goal(goal)
    final_progress = simulator.step()
    final_progress = simulator.step()
    assert final_progress.status == NavigationStatus.ARRIVED

    package_handler = PackageHandler()
    package = package_handler.create_package(
        build_sample_package_info().source_zone,
        build_sample_package_info().destination_zone,
        task_id=started_task.task_id,
    )
    pickup_event = package_handler.pickup(package)
    dropoff_event = package_handler.dropoff()
    assert dropoff_event.package_state == PackageState.DELIVERED

    queue.complete_task(started_task.task_id)

    aggregator = RobotStatusAggregator()
    aggregator.update_from_task_status({"event_type": "task_completed", "task_id": started_task.task_id})
    aggregator.update_from_navigation_progress(final_progress.to_dict())
    aggregator.update_from_package_status(dropoff_event.to_dict())
    aggregator.update_from_battery_state({"percentage": 80})
    snapshot = aggregator.get_snapshot()

    logger = DiagnosticLogger()
    event = logger.add_event(logger.event_from_snapshot(snapshot))

    assert snapshot.health_level == RobotHealthLevel.OK
    assert package_handler.get_current_package() is not None
    assert package_handler.get_current_package().state == PackageState.DELIVERED
    assert queue.get_task(started_task.task_id).status == TaskStatus.COMPLETED
    assert event.health_level == RobotHealthLevel.OK
