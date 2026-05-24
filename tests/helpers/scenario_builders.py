"""Pure scenario builders for final pytest validation."""

from __future__ import annotations

from smart_warehouse_robot.common.helpers import (
    build_battery_state,
    build_charge_command,
    build_charge_navigation_goal,
    build_diagnostic_event,
    build_emergency_stop_command,
    build_obstacle_reading,
    build_package_info,
    build_package_status_event,
    build_robot_status_snapshot,
)
from smart_warehouse_robot.common.models import (
    DiagnosticEvent,
    NavigationGoal,
    NavigationProgress,
    ObstacleReading,
    PackageInfo,
    PackageStatusEvent,
    RobotStatusSnapshot,
    WarehouseTask,
)


def build_sample_task() -> WarehouseTask:
    return WarehouseTask(
        task_type="pickup",
        source_zone="receiving",
        destination_zone="shipping",
        priority=4,
        notes="Scenario sample task",
    )


def build_sample_navigation_goal() -> NavigationGoal:
    task = build_sample_task()
    return NavigationGoal(
        task_id=task.task_id,
        source_zone=task.source_zone,
        destination_zone=task.destination_zone,
        priority=task.priority,
    )


def build_sample_navigation_progress_sequence() -> list[NavigationProgress]:
    goal = build_sample_navigation_goal()
    return [
        NavigationProgress(
            goal_id=goal.goal_id,
            task_id=goal.task_id,
            current_zone="receiving",
            destination_zone="shipping",
            progress_percent=25,
            status="moving",
            message="Robot started moving.",
        ),
        NavigationProgress(
            goal_id=goal.goal_id,
            task_id=goal.task_id,
            current_zone="packing",
            destination_zone="shipping",
            progress_percent=75,
            status="moving",
            message="Robot is near shipping.",
        ),
        NavigationProgress(
            goal_id=goal.goal_id,
            task_id=goal.task_id,
            current_zone="shipping",
            destination_zone="shipping",
            progress_percent=100,
            status="arrived",
            message="Robot arrived at shipping.",
        ),
    ]


def build_sample_obstacle_reading() -> ObstacleReading:
    return build_obstacle_reading("packing", 0.25, True, description="Critical pallet obstacle")


def build_sample_emergency_stop():
    return build_emergency_stop_command(build_sample_obstacle_reading())


def build_sample_battery_state():
    return build_battery_state("warehouse_bot_01", 20, "storage_a")


def build_sample_charge_command():
    return build_charge_command(build_sample_battery_state())


def build_sample_package_info() -> PackageInfo:
    task = build_sample_task()
    return build_package_info(None, "receiving", "shipping", task_id=task.task_id)


def build_sample_package_status_events() -> list[PackageStatusEvent]:
    package = build_sample_package_info()
    carrying = PackageInfo.from_json(package.to_json()).mark_carrying("warehouse_bot_01")
    delivered = PackageInfo.from_json(carrying.to_json()).mark_delivered()
    return [
        build_package_status_event(
            "package_picked_up",
            carrying,
            "warehouse_bot_01",
            "Package pickup completed.",
        ),
        build_package_status_event(
            "package_delivered",
            delivered,
            "warehouse_bot_01",
            "Package dropoff completed.",
        ),
    ]


def build_sample_robot_status() -> RobotStatusSnapshot:
    task = build_sample_task()
    goal = build_sample_navigation_goal()
    package = build_sample_package_info()
    return build_robot_status_snapshot(
        robot_name="warehouse_bot_01",
        current_zone="shipping",
        mode="unloading",
        battery_percentage=80,
        active_task_id=task.task_id,
        active_navigation_goal_id=goal.goal_id,
        package_id=package.package_id,
        carrying_package=False,
        emergency_stop_active=False,
        last_event="Package delivered successfully.",
    )


def build_sample_diagnostic_event() -> DiagnosticEvent:
    snapshot = build_sample_robot_status()
    return build_diagnostic_event(
        source="status",
        health_level=snapshot.health_level,
        message="Robot status is healthy in scenario.",
        related_id=snapshot.active_task_id,
        robot_name=snapshot.robot_name,
        topic="/warehouse/robot/diagnostics",
    )


def build_full_happy_path_scenario() -> dict:
    return {
        "task": build_sample_task(),
        "navigation_goal": build_sample_navigation_goal(),
        "navigation_progress": build_sample_navigation_progress_sequence(),
        "package": build_sample_package_info(),
        "package_events": build_sample_package_status_events(),
        "robot_status": build_sample_robot_status(),
        "diagnostic": build_sample_diagnostic_event(),
    }


def build_full_emergency_scenario() -> dict:
    goal = build_sample_navigation_goal()
    obstacle = build_sample_obstacle_reading()
    emergency = build_sample_emergency_stop()
    status = build_robot_status_snapshot(
        robot_name="warehouse_bot_01",
        current_zone="packing",
        mode="error",
        battery_percentage=50,
        active_navigation_goal_id=goal.goal_id,
        emergency_stop_active=True,
        last_event=emergency.reason,
    )
    diagnostic = build_diagnostic_event(
        source="safety",
        health_level="critical",
        message="Emergency stop active because of obstacle.",
        related_id=goal.goal_id,
        robot_name=status.robot_name,
        topic="/warehouse/robot/diagnostics",
    )
    return {
        "navigation_goal": goal,
        "obstacle": obstacle,
        "emergency_stop": emergency,
        "robot_status": status,
        "diagnostic": diagnostic,
    }


def build_full_low_battery_scenario() -> dict:
    battery = build_sample_battery_state()
    charge_command = build_sample_charge_command()
    navigation_goal = build_charge_navigation_goal(charge_command)
    status = build_robot_status_snapshot(
        robot_name="warehouse_bot_01",
        current_zone="charging_station",
        mode="charging",
        battery_percentage=battery.percentage,
        active_navigation_goal_id=navigation_goal.goal_id,
        last_event="Returning to charging station.",
    )
    diagnostic = build_diagnostic_event(
        source="battery",
        health_level="warning",
        message="Battery is below threshold and charging is required.",
        related_id=charge_command.command_id,
        robot_name=status.robot_name,
        topic="/warehouse/robot/diagnostics",
    )
    return {
        "battery": battery,
        "charge_command": charge_command,
        "navigation_goal": navigation_goal,
        "robot_status": status,
        "diagnostic": diagnostic,
    }
