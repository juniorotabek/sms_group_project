"""Click-based CLI for task management and simple warehouse operations."""

from __future__ import annotations

import json
from pathlib import Path

import click

from smart_warehouse_robot.common.constants import (
    BATTERY_STATE_TOPIC,
    CHARGING_STATION_ZONE,
    DIAGNOSTICS_TOPIC,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_BATTERY_CHARGE_PERCENT,
    DEFAULT_BATTERY_DRAIN_PERCENT,
    DEFAULT_CRITICAL_BATTERY_THRESHOLD,
    DEFAULT_CLI_PRIORITY,
    DEFAULT_LOW_BATTERY_THRESHOLD,
    DEFAULT_NAVIGATION_STEP_PERCENT,
    DEFAULT_OBSTACLE_DETECTION_INTERVAL_SECONDS,
    DEFAULT_ROBOT_NAME,
    EMERGENCY_STOP_TOPIC,
    NAVIGATION_GOAL_TOPIC,
    NAVIGATION_PROGRESS_TOPIC,
    OBSTACLE_TOPIC,
    PACKAGE_DROPOFF_SERVICE,
    PACKAGE_PICKUP_SERVICE,
    PACKAGE_RESET_SERVICE,
    PACKAGE_STATUS_TOPIC,
    RETURN_TO_CHARGE_TOPIC,
    ROBOT_STATUS_TOPIC,
    TASK_NEW_TOPIC,
    TASK_STATUS_TOPIC,
    WAREHOUSE_ZONES,
)
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
    calculate_distance,
    classify_battery_level,
    classify_obstacle_severity,
    create_goal_id,
    build_task_json,
    determine_health_level,
    format_battery_summary,
    format_charge_command_summary,
    format_diagnostic_event_summary,
    format_emergency_stop_summary,
    format_navigation_goal_summary,
    format_navigation_progress_summary,
    format_package_event_summary,
    format_package_summary,
    format_obstacle_summary,
    format_robot_status_summary,
    format_task_summary,
    get_waypoint_for_zone,
    parse_robot_health_level,
    parse_robot_mode,
    parse_warehouse_zone,
    should_emergency_stop_for_battery,
    should_return_to_charge,
    should_trigger_emergency_stop,
    validate_zone,
)
from smart_warehouse_robot.common.models import (
    BatteryState,
    DiagnosticEvent,
    DiagnosticSource,
    NavigationGoal,
    NavigationProgress,
    NavigationStatus,
    ObstacleReading,
    PackageInfo,
    PackageState,
    RobotHealthLevel,
    RobotMode,
    RobotStatusSnapshot,
    WarehouseTask,
    WarehouseZone,
)
from smart_warehouse_robot.services.battery import BatterySimulator
from smart_warehouse_robot.nodes.obstacle_detector import create_simulated_obstacle_readings
from smart_warehouse_robot.nodes.task_publisher import create_sample_tasks
from smart_warehouse_robot.services.navigation import NavigationSimulator
from smart_warehouse_robot.services.package_handler import PackageHandler
from smart_warehouse_robot.services.safety import SafetyMonitor
from smart_warehouse_robot.services.status import DiagnosticLogger, RobotStatusAggregator
from smart_warehouse_robot.services.task_queue import TaskQueue


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FINAL_BAG_COMMAND = (
    "rosbag record -O bags/final_demo.bag "
    "/warehouse/tasks/new /warehouse/tasks/status /warehouse/navigation/goal "
    "/warehouse/navigation/progress /warehouse/safety/obstacle "
    "/warehouse/safety/emergency_stop /warehouse/battery/state "
    "/warehouse/battery/return_to_charge /warehouse/package/status "
    "/warehouse/robot/status /warehouse/robot/diagnostics"
)


def build_sample_status_payload() -> dict:
    """Return a simple JSON-serializable robot status sample for demos."""
    snapshot = build_robot_status_snapshot(
        robot_name=DEFAULT_ROBOT_NAME,
        current_zone=WarehouseZone.CHARGING_STATION,
        mode=RobotMode.IDLE,
        battery_percentage=DEFAULT_BATTERY_THRESHOLD + 15,
    )
    return snapshot.to_dict()


def print_section(title: str) -> None:
    """Print a clear section header for terminal demos."""
    click.echo(f"\n=== {title} ===")


def print_success(message: str) -> None:
    """Print a success line."""
    click.echo(f"[OK] {message}")


def print_warning(message: str) -> None:
    """Print a warning line."""
    click.echo(f"[WARN] {message}")


def print_error(message: str) -> None:
    """Print an error line."""
    click.echo(f"[ERROR] {message}")


def print_json(data: dict) -> None:
    """Print JSON with stable formatting."""
    click.echo(json.dumps(data, indent=2, sort_keys=True))


def print_command(command: str, description: str | None = None) -> None:
    """Print a shell command with an optional one-line description."""
    if description:
        click.echo(f"{command}  # {description}")
        return
    click.echo(command)


def format_table(rows: list[dict], columns: list[str]) -> str:
    """Format a simple plain-text table without external dependencies."""
    if not columns:
        return ""

    widths = {column: len(column) for column in columns}
    for row in rows:
        for column in columns:
            widths[column] = max(widths[column], len(str(row.get(column, ""))))

    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)
    body = [
        " | ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns)
        for row in rows
    ]
    return "\n".join([header, separator, *body])


@click.group(help="Smart Warehouse Robot operations CLI.")
def main() -> None:
    """Entry point for warehouse CLI commands."""


@main.command("create-task")
@click.option("--type", "task_type_value", "-t", required=True, help="Task type: pickup, dropoff, move, charge.")
@click.option("--source", "-s", required=True, help="Source warehouse zone.")
@click.option("--destination", "-d", required=True, help="Destination warehouse zone.")
@click.option("--priority", "-p", default=DEFAULT_CLI_PRIORITY, show_default=True, type=int, help="Task priority from 1 to 5.")
@click.option("--notes", "-n", default=None, help="Optional notes for the task.")
@click.option("--json-output", is_flag=True, help="Print only JSON output.")
def create_task_command(
    task_type_value: str,
    source: str,
    destination: str,
    priority: int,
    notes: str | None,
    json_output: bool,
) -> None:
    """Create a task and print either JSON or a readable summary."""
    try:
        task_json = build_task_json(task_type_value, source, destination, priority, notes=notes)
        task = WarehouseTask.from_json(task_json)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(task_json)
        return

    click.echo(format_task_summary(task))
    click.echo(task_json)


@main.command("sample-tasks")
def sample_tasks_command() -> None:
    """Print the rotating sample tasks used by the publisher node."""
    for task in create_sample_tasks():
        click.echo(format_task_summary(task))
        click.echo(task.to_json())


@main.command("queue-demo")
def queue_demo_command() -> None:
    """Demonstrate TaskQueue behavior without needing ROS to run."""
    queue = TaskQueue()
    for task in create_sample_tasks()[:3]:
        queue.add_task(task)

    started_task = queue.start_next_task(DEFAULT_ROBOT_NAME)
    if started_task is not None:
        queue.complete_task(started_task.task_id)

    click.echo(json.dumps(queue.summary(), indent=2, sort_keys=True))


@main.command("validate-task")
@click.option("--task-json", required=True, help="JSON text representing a warehouse task.")
def validate_task_command(task_json: str) -> None:
    """Validate a task JSON payload."""
    try:
        task = WarehouseTask.from_json(task_json)
    except ValueError as exc:
        raise click.ClickException(f"Invalid task JSON: {exc}") from exc

    click.echo(f"Valid task: {task.task_id}")


@main.command("create-nav-goal")
@click.option("--task-id", default=None, help="Optional related task id.")
@click.option("--source", "-s", required=True, help="Source warehouse zone.")
@click.option("--destination", "-d", required=True, help="Destination warehouse zone.")
@click.option("--priority", "-p", default=DEFAULT_CLI_PRIORITY, show_default=True, type=int, help="Goal priority from 1 to 5.")
@click.option("--json-output", is_flag=True, help="Print only JSON output.")
def create_nav_goal_command(task_id: str | None, source: str, destination: str, priority: int, json_output: bool) -> None:
    """Create a navigation goal and print JSON or a readable summary."""
    try:
        goal = NavigationGoal(
            goal_id=create_goal_id(),
            task_id=task_id,
            source_zone=source,
            destination_zone=destination,
            priority=priority,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(goal.to_json())
        return

    click.echo(format_navigation_goal_summary(goal))
    click.echo(goal.to_json())


@main.command("nav-demo")
def nav_demo_command() -> None:
    """Simulate navigation progress without ROS."""
    goal = NavigationGoal(
        source_zone="receiving",
        destination_zone="packing",
        priority=3,
        task_id="TASK-DEMO",
    )
    simulator = NavigationSimulator(step_percent=DEFAULT_NAVIGATION_STEP_PERCENT)
    simulator.set_goal(goal)

    while True:
        progress = simulator.step()
        click.echo(format_navigation_progress_summary(progress))
        if progress.status in {NavigationStatus.ARRIVED, NavigationStatus.CANCELLED, NavigationStatus.FAILED}:
            simulator.reset_if_terminal()
            break


@main.command("zone-distance")
@click.option("--source", "-s", required=True, help="Source warehouse zone.")
@click.option("--destination", "-d", required=True, help="Destination warehouse zone.")
def zone_distance_command(source: str, destination: str) -> None:
    """Print the Euclidean distance between two warehouse zones."""
    try:
        source_waypoint = get_waypoint_for_zone(source)
        destination_waypoint = get_waypoint_for_zone(destination)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    distance = calculate_distance(source_waypoint, destination_waypoint)
    click.echo(
        f"Distance from {source_waypoint.zone.value} to {destination_waypoint.zone.value}: {distance:.2f}"
    )


@main.command("validate-nav-goal")
@click.option("--goal-json", required=True, help="JSON text representing a navigation goal.")
def validate_nav_goal_command(goal_json: str) -> None:
    """Validate a navigation goal JSON payload."""
    try:
        goal = NavigationGoal.from_json(goal_json)
    except ValueError as exc:
        raise click.ClickException(f"Invalid navigation goal JSON: {exc}") from exc

    click.echo(f"Valid navigation goal: {goal.goal_id}")


@main.command("obstacle-sample")
@click.option("--zone", "-z", required=True, help="Warehouse zone for the obstacle reading.")
@click.option("--distance", "-d", required=True, type=float, help="Distance to the obstacle in meters.")
@click.option("--detected/--clear", default=True, help="Whether an obstacle is detected.")
@click.option("--json-output", is_flag=True, help="Print only JSON output.")
def obstacle_sample_command(zone: str, distance: float, detected: bool, json_output: bool) -> None:
    """Create an obstacle reading and print JSON or a readable summary."""
    try:
        reading = build_obstacle_reading(zone, distance, detected)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(reading.to_json())
        return

    click.echo(format_obstacle_summary(reading))
    click.echo(reading.to_json())


@main.command("emergency-stop-sample")
@click.option("--zone", "-z", required=True, help="Warehouse zone for the obstacle reading.")
@click.option("--distance", "-d", required=True, type=float, help="Distance to the obstacle in meters.")
@click.option("--reason", "-r", default=None, help="Optional emergency stop reason.")
@click.option("--json-output", is_flag=True, help="Print only JSON output.")
def emergency_stop_sample_command(zone: str, distance: float, reason: str | None, json_output: bool) -> None:
    """Create an emergency stop command from an obstacle reading."""
    try:
        reading = build_obstacle_reading(zone, distance, True)
        command = build_emergency_stop_command(reading, reason=reason)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(command.to_json())
        return

    click.echo(format_emergency_stop_summary(command))
    click.echo(command.to_json())


@main.command("safety-demo")
def safety_demo_command() -> None:
    """Run simulated obstacle readings through the safety monitor."""
    monitor = SafetyMonitor()
    readings = create_simulated_obstacle_readings(WarehouseZone.STORAGE_A)
    for reading in readings:
        click.echo(format_obstacle_summary(reading))
        command = monitor.process_reading(reading)
        if command is not None:
            click.echo(f"EMERGENCY: {format_emergency_stop_summary(command)}")
        else:
            click.echo(f"Safety state: {monitor.get_safety_state().value}")


@main.command("classify-obstacle")
@click.option("--distance", "-d", required=True, type=float, help="Distance to the obstacle in meters.")
@click.option("--detected/--clear", default=True, help="Whether an obstacle is detected.")
def classify_obstacle_command(distance: float, detected: bool) -> None:
    """Print obstacle severity and whether it triggers emergency stop."""
    severity = classify_obstacle_severity(distance, detected)
    reading = build_obstacle_reading("storage_a", distance, detected)
    click.echo(
        f"Severity: {severity.value}, emergency_stop_required: {should_trigger_emergency_stop(reading)}"
    )


@main.command("validate-obstacle")
@click.option("--obstacle-json", required=True, help="JSON text representing an obstacle reading.")
def validate_obstacle_command(obstacle_json: str) -> None:
    """Validate an obstacle reading JSON payload."""
    try:
        reading = ObstacleReading.from_json(obstacle_json)
    except ValueError as exc:
        raise click.ClickException(f"Invalid obstacle JSON: {exc}") from exc

    click.echo(f"Valid obstacle reading: {reading.reading_id}")


@main.command("battery-sample")
@click.option("--robot-name", default=DEFAULT_ROBOT_NAME, show_default=True)
@click.option("--percentage", "-p", required=True, type=float)
@click.option("--zone", "-z", required=True)
@click.option("--charging-status", default="not_charging", show_default=True)
@click.option("--json-output", is_flag=True)
def battery_sample_command(robot_name: str, percentage: float, zone: str, charging_status: str, json_output: bool) -> None:
    """Create a battery state and print JSON or a readable summary."""
    try:
        state = build_battery_state(robot_name, percentage, zone, charging_status=charging_status)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(state.to_json())
        return

    click.echo(format_battery_summary(state))
    click.echo(state.to_json())


@main.command("charge-command-sample")
@click.option("--robot-name", default=DEFAULT_ROBOT_NAME, show_default=True)
@click.option("--percentage", "-p", required=True, type=float)
@click.option("--zone", "-z", required=True)
@click.option("--reason", "-r", default=None)
@click.option("--json-output", is_flag=True)
def charge_command_sample_command(
    robot_name: str,
    percentage: float,
    zone: str,
    reason: str | None,
    json_output: bool,
) -> None:
    """Create a charge command from a battery state."""
    try:
        state = build_battery_state(robot_name, percentage, zone)
        command = build_charge_command(state, reason=reason)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(command.to_json())
        return

    click.echo(format_charge_command_summary(command))
    click.echo(command.to_json())


@main.command("battery-demo")
def battery_demo_command() -> None:
    """Drain battery until low, return to charge, then charge to full."""
    simulator = BatterySimulator(
        robot_name=DEFAULT_ROBOT_NAME,
        start_percentage=100.0,
        start_zone=WarehouseZone.RECEIVING,
        drain_percent=DEFAULT_BATTERY_DRAIN_PERCENT,
        charge_percent=DEFAULT_BATTERY_CHARGE_PERCENT,
    )

    while not simulator.needs_return_to_charge():
        state = simulator.drain()
        click.echo(format_battery_summary(state))

    command = simulator.start_return_to_charge()
    click.echo(format_charge_command_summary(command))
    goal = build_charge_navigation_goal(command)
    click.echo(format_navigation_goal_summary(goal))

    simulator.set_current_zone(WarehouseZone.CHARGING_STATION)
    simulator.start_charging()
    while simulator.get_state().percentage < 100.0:
        state = simulator.charge()
        state = simulator.stop_charging_if_full()
        click.echo(format_battery_summary(state))

    click.echo(json.dumps(simulator.summary(), indent=2, sort_keys=True))


@main.command("classify-battery")
@click.option("--percentage", "-p", required=True, type=float)
def classify_battery_command(percentage: float) -> None:
    """Print battery level and threshold decisions."""
    level = classify_battery_level(percentage)
    click.echo(
        f"Battery level: {level.value}, "
        f"return_to_charge_required: {should_return_to_charge(percentage, DEFAULT_LOW_BATTERY_THRESHOLD)}, "
        f"critical_battery_warning: {should_emergency_stop_for_battery(percentage, DEFAULT_CRITICAL_BATTERY_THRESHOLD)}"
    )


@main.command("validate-battery")
@click.option("--battery-json", required=True)
def validate_battery_command(battery_json: str) -> None:
    """Validate a battery state JSON payload."""
    try:
        state = BatteryState.from_json(battery_json)
    except ValueError as exc:
        raise click.ClickException(f"Invalid battery JSON: {exc}") from exc

    click.echo(f"Valid battery state: {state.battery_id}")


@main.command("package-sample")
@click.option("--package-id", default=None)
@click.option("--source", "-s", required=True)
@click.option("--destination", "-d", required=True)
@click.option("--task-id", default=None)
@click.option("--notes", default=None)
@click.option("--json-output", is_flag=True)
def package_sample_command(
    package_id: str | None,
    source: str,
    destination: str,
    task_id: str | None,
    notes: str | None,
    json_output: bool,
) -> None:
    """Create package info and print JSON or a readable summary."""
    try:
        package_info = build_package_info(package_id, source, destination, task_id=task_id, notes=notes)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(package_info.to_json())
        return

    click.echo(format_package_summary(package_info))
    click.echo(package_info.to_json())


@main.command("package-demo")
def package_demo_command() -> None:
    """Create a package, pickup it, drop it off, and print the summary."""
    handler = PackageHandler()
    package_info = handler.create_package(WarehouseZone.STORAGE_A, WarehouseZone.SHIPPING)
    click.echo(format_package_summary(package_info))
    pickup_event = handler.pickup()
    click.echo(format_package_event_summary(pickup_event))
    dropoff_event = handler.dropoff()
    click.echo(format_package_event_summary(dropoff_event))
    click.echo(json.dumps(handler.summary(), indent=2, sort_keys=True))


@main.command("package-status-event")
@click.option("--event-type", required=True)
@click.option("--package-id", default=None)
@click.option("--source", default=None)
@click.option("--destination", default=None)
@click.option("--robot-name", default=DEFAULT_ROBOT_NAME, show_default=True)
@click.option("--message", required=True)
@click.option("--json-output", is_flag=True)
def package_status_event_command(
    event_type: str,
    package_id: str | None,
    source: str | None,
    destination: str | None,
    robot_name: str,
    message: str,
    json_output: bool,
) -> None:
    """Create a package status event sample."""
    package_info = None
    if source is not None and destination is not None:
        package_info = build_package_info(package_id, source, destination)
    event = build_package_status_event(event_type, package_info, robot_name, message)
    if json_output:
        click.echo(event.to_json())
        return
    click.echo(format_package_event_summary(event))
    click.echo(event.to_json())


@main.command("validate-package")
@click.option("--package-json", required=True)
def validate_package_command(package_json: str) -> None:
    """Validate a package JSON payload."""
    try:
        package_info = PackageInfo.from_json(package_json)
    except ValueError as exc:
        raise click.ClickException(f"Invalid package JSON: {exc}") from exc

    click.echo(f"Valid package: {package_info.package_id}")


@main.command("package-ros-commands")
def package_ros_commands_command() -> None:
    """Print useful ROS 1 service and topic commands for package handling."""
    commands = [
        "rosservice list",
        "rosservice call /warehouse/package/pickup",
        "rosservice call /warehouse/package/dropoff",
        "rosservice call /warehouse/package/reset",
        "rostopic echo /warehouse/package/status",
    ]
    for command in commands:
        click.echo(command)


@main.command("robot-status-sample")
@click.option("--robot-name", default=DEFAULT_ROBOT_NAME, show_default=True)
@click.option("--zone", "-z", required=True)
@click.option("--mode", default=RobotMode.IDLE.value, show_default=True)
@click.option("--battery-percentage", default=None, type=float)
@click.option("--emergency-stop/--no-emergency-stop", default=False)
@click.option("--json-output", is_flag=True)
def robot_status_sample_command(
    robot_name: str,
    zone: str,
    mode: str,
    battery_percentage: float | None,
    emergency_stop: bool,
    json_output: bool,
) -> None:
    """Create a robot status snapshot and print JSON or a readable summary."""
    try:
        snapshot = build_robot_status_snapshot(
            robot_name=robot_name,
            current_zone=zone,
            mode=mode,
            battery_percentage=battery_percentage,
            emergency_stop_active=emergency_stop,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(snapshot.to_json())
        return

    click.echo(format_robot_status_summary(snapshot))
    click.echo(snapshot.to_json())


@main.command("diagnostic-sample")
@click.option("--source", required=True)
@click.option("--level", required=True)
@click.option("--message", required=True)
@click.option("--related-id", default=None)
@click.option("--json-output", is_flag=True)
def diagnostic_sample_command(
    source: str,
    level: str,
    message: str,
    related_id: str | None,
    json_output: bool,
) -> None:
    """Create a diagnostic event sample."""
    try:
        event = build_diagnostic_event(
            source=source,
            health_level=level,
            message=message,
            related_id=related_id,
            robot_name=DEFAULT_ROBOT_NAME,
            topic="/warehouse/robot/diagnostics",
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_output:
        click.echo(event.to_json())
        return

    click.echo(format_diagnostic_event_summary(event))
    click.echo(event.to_json())


@main.command("status-demo")
def status_demo_command() -> None:
    """Simulate status aggregation from multiple subsystem events."""
    aggregator = RobotStatusAggregator(robot_name=DEFAULT_ROBOT_NAME, start_zone=WarehouseZone.RECEIVING)
    aggregator.update_from_task_status({"event_type": "task_started", "task_id": "TASK-DEMO"})
    aggregator.update_from_navigation_progress(
        {
            "goal_id": "GOAL-DEMO",
            "current_zone": "packing",
            "status": "moving",
            "message": "Robot is moving to packing.",
        }
    )
    aggregator.update_from_battery_state({"percentage": 22.0})
    aggregator.update_from_package_status(
        {
            "package_id": "PKG-DEMO",
            "package_state": "carrying",
            "message": "Package pickup completed.",
        }
    )
    snapshot = aggregator.get_snapshot()
    click.echo(format_robot_status_summary(snapshot))
    click.echo(snapshot.to_json())


@main.command("diagnostics-demo")
def diagnostics_demo_command() -> None:
    """Create several snapshots and convert them into diagnostic events."""
    logger = DiagnosticLogger(robot_name=DEFAULT_ROBOT_NAME)
    snapshots = [
        build_robot_status_snapshot(
            robot_name=DEFAULT_ROBOT_NAME,
            current_zone="receiving",
            mode="idle",
            battery_percentage=80,
        ),
        build_robot_status_snapshot(
            robot_name=DEFAULT_ROBOT_NAME,
            current_zone="storage_a",
            mode="moving",
            battery_percentage=20,
            last_event="Battery below threshold",
        ),
        build_robot_status_snapshot(
            robot_name=DEFAULT_ROBOT_NAME,
            current_zone="packing",
            mode="error",
            battery_percentage=8,
            emergency_stop_active=True,
            last_event="Emergency stop is active",
        ),
    ]
    for snapshot in snapshots:
        event = logger.add_event(logger.event_from_snapshot(snapshot))
        click.echo(format_diagnostic_event_summary(event))
    click.echo(json.dumps(logger.summary(), indent=2, sort_keys=True))


@main.command("validate-status")
@click.option("--status-json", required=True)
def validate_status_command(status_json: str) -> None:
    """Validate a robot status snapshot JSON payload."""
    try:
        snapshot = RobotStatusSnapshot.from_json(status_json)
    except ValueError as exc:
        raise click.ClickException(f"Invalid robot status JSON: {exc}") from exc

    click.echo(f"Valid robot status: {snapshot.robot_name}")


@main.command("validate-diagnostic")
@click.option("--diagnostic-json", required=True)
def validate_diagnostic_command(diagnostic_json: str) -> None:
    """Validate a diagnostic event JSON payload."""
    try:
        event = DiagnosticEvent.from_json(diagnostic_json)
    except ValueError as exc:
        raise click.ClickException(f"Invalid diagnostic JSON: {exc}") from exc

    click.echo(f"Valid diagnostic event: {event.diagnostic_id}")


@main.command("status-ros-commands")
def status_ros_commands_command() -> None:
    """Print useful ROS 1 status and diagnostics commands."""
    commands = [
        "rostopic echo /warehouse/robot/status",
        "rostopic echo /warehouse/robot/diagnostics",
        "rosrun smart_warehouse_robot status_publisher_node.py",
        "rosrun smart_warehouse_robot diagnostic_logger_node.py",
    ]
    for command in commands:
        click.echo(command)


@main.command("overview")
def overview_command() -> None:
    """Print a concise overview of the project, nodes, topics, and services."""
    print_section("Project")
    click.echo("Project name: Smart Warehouse Mobility Robot")
    click.echo("ROS version: ROS 1 Noetic")
    click.echo("Implemented modules: task, navigation, safety, battery, package, status, diagnostics, operations CLI")

    print_section("Implemented Members")
    members = [
        "Member 1 Task Management",
        "Member 2 Navigation",
        "Member 3 Obstacle Safety",
        "Member 4 Battery System",
        "Member 5 Package Handling",
        "Member 6 Robot Status + Diagnostics",
        "Member 7 Advanced CLI + Operations",
    ]
    for member in members:
        click.echo(member)

    print_section("ROS Nodes")
    nodes = [
        "task_publisher_node.py",
        "task_queue_manager_node.py",
        "waypoint_goal_publisher_node.py",
        "path_progress_monitor_node.py",
        "obstacle_detector_node.py",
        "emergency_stop_node.py",
        "battery_publisher_node.py",
        "charging_controller_node.py",
        "package_handler_node.py",
        "status_publisher_node.py",
        "diagnostic_logger_node.py",
    ]
    for node in nodes:
        click.echo(node)

    print_section("Topics")
    for topic in [
        TASK_NEW_TOPIC,
        TASK_STATUS_TOPIC,
        NAVIGATION_GOAL_TOPIC,
        NAVIGATION_PROGRESS_TOPIC,
        OBSTACLE_TOPIC,
        EMERGENCY_STOP_TOPIC,
        BATTERY_STATE_TOPIC,
        RETURN_TO_CHARGE_TOPIC,
        PACKAGE_STATUS_TOPIC,
        ROBOT_STATUS_TOPIC,
        DIAGNOSTICS_TOPIC,
    ]:
        click.echo(topic)

    print_section("Services")
    for service_name in [PACKAGE_PICKUP_SERVICE, PACKAGE_DROPOFF_SERVICE, PACKAGE_RESET_SERVICE]:
        click.echo(service_name)

    print_section("Run")
    print_command("roslaunch smart_warehouse_robot warehouse_demo.launch", "Full demo launch")
    print_command(FINAL_BAG_COMMAND, "Final rosbag recording")
    print_command("pytest", "Run pytest scenarios")


@main.command("demo-plan")
def demo_plan_command() -> None:
    """Print a structured 25-minute demo plan."""
    print_section("25-minute Demo Plan")
    steps = [
        "1. Start roscore",
        "2. Launch full warehouse demo",
        "3. Show active topics with rostopic list",
        "4. Show task publishing and queue status",
        "5. Show navigation goal and progress flow",
        "6. Show obstacle emergency stop behavior",
        "7. Show battery return-to-charge behavior",
        "8. Show package pickup and dropoff services",
        "9. Show robot status and diagnostics topics",
        "10. Record rosbag for the final demo",
        "11. Run pytest and explain logic validation",
        "12. Explain team member contributions",
    ]
    for step in steps:
        click.echo(step)


@main.command("ros-commands")
def ros_commands_command() -> None:
    """Print categorized ROS 1 build, launch, topic, service, and bag commands."""
    print_section("Build")
    for command in ["cd ~/catkin_ws", "catkin_make", "source devel/setup.bash"]:
        print_command(command)

    print_section("Launch")
    for command in ["roscore", "roslaunch smart_warehouse_robot warehouse_demo.launch"]:
        print_command(command)

    print_section("Individual Nodes")
    for command in [
        "rosrun smart_warehouse_robot task_publisher_node.py",
        "rosrun smart_warehouse_robot task_queue_manager_node.py",
        "rosrun smart_warehouse_robot waypoint_goal_publisher_node.py",
        "rosrun smart_warehouse_robot path_progress_monitor_node.py",
        "rosrun smart_warehouse_robot obstacle_detector_node.py",
        "rosrun smart_warehouse_robot emergency_stop_node.py",
        "rosrun smart_warehouse_robot battery_publisher_node.py",
        "rosrun smart_warehouse_robot charging_controller_node.py",
        "rosrun smart_warehouse_robot package_handler_node.py",
        "rosrun smart_warehouse_robot status_publisher_node.py",
        "rosrun smart_warehouse_robot diagnostic_logger_node.py",
    ]:
        print_command(command)

    print_section("Topics")
    for command in [
        "rostopic list",
        "rostopic echo /warehouse/tasks/new",
        "rostopic echo /warehouse/tasks/status",
        "rostopic echo /warehouse/navigation/goal",
        "rostopic echo /warehouse/navigation/progress",
        "rostopic echo /warehouse/safety/obstacle",
        "rostopic echo /warehouse/safety/emergency_stop",
        "rostopic echo /warehouse/battery/state",
        "rostopic echo /warehouse/battery/return_to_charge",
        "rostopic echo /warehouse/package/status",
        "rostopic echo /warehouse/robot/status",
        "rostopic echo /warehouse/robot/diagnostics",
    ]:
        print_command(command)

    print_section("Services")
    for command in [
        "rosservice list",
        "rosservice call /warehouse/package/pickup",
        "rosservice call /warehouse/package/dropoff",
        "rosservice call /warehouse/package/reset",
    ]:
        print_command(command)

    print_section("Rosbag")
    for command in ["mkdir -p bags", FINAL_BAG_COMMAND, "rosbag info bags/final_demo.bag", "rosbag play bags/final_demo.bag"]:
        print_command(command)

    print_section("Tests")
    print_command("pytest")

    print_section("CLI Demos")
    for command in [
        "rosrun smart_warehouse_robot smart_warehouse_cli.py overview",
        "rosrun smart_warehouse_robot smart_warehouse_cli.py scenario happy-path",
        "rosrun smart_warehouse_robot smart_warehouse_cli.py diagnostics-demo",
    ]:
        print_command(command)


@main.group("scenario")
def scenario_group() -> None:
    """Generate end-to-end simulated warehouse scenarios without ROS."""


def _build_full_scenario() -> dict:
    """Build a complete simulated scenario covering the main project models."""
    task = WarehouseTask(
        task_type="pickup",
        source_zone="receiving",
        destination_zone="shipping",
        priority=4,
        notes="Scenario task",
    ).mark_in_progress()
    goal = NavigationGoal(
        task_id=task.task_id,
        source_zone=task.source_zone,
        destination_zone=task.destination_zone,
        priority=task.priority,
    ).mark_moving()
    navigation_progress = [
        NavigationProgress(
            goal_id=goal.goal_id,
            task_id=goal.task_id,
            current_zone="receiving",
            destination_zone="shipping",
            progress_percent=25,
            status="moving",
            message="Leaving receiving zone.",
        ).to_dict(),
        NavigationProgress(
            goal_id=goal.goal_id,
            task_id=goal.task_id,
            current_zone="packing",
            destination_zone="shipping",
            progress_percent=75,
            status="moving",
            message="Approaching shipping zone.",
        ).to_dict(),
        NavigationProgress(
            goal_id=goal.goal_id,
            task_id=goal.task_id,
            current_zone="shipping",
            destination_zone="shipping",
            progress_percent=100,
            status="arrived",
            message="Arrived at shipping zone.",
        ).to_dict(),
    ]
    obstacle = build_obstacle_reading("packing", 0.25, True, description="Pallet detected")
    emergency_command = build_emergency_stop_command(obstacle) if should_trigger_emergency_stop(obstacle) else None
    battery = build_battery_state(DEFAULT_ROBOT_NAME, 20, "packing")
    charge_command = build_charge_command(battery) if should_return_to_charge(battery.percentage) else None
    package = build_package_info(None, "receiving", "shipping", task_id=task.task_id)
    pickup_event = build_package_status_event(
        "package_picked_up",
        PackageInfo.from_json(package.to_json()).mark_carrying(DEFAULT_ROBOT_NAME),
        DEFAULT_ROBOT_NAME,
        "Package pickup completed.",
    )
    delivered_package = PackageInfo.from_json(package.to_json()).mark_carrying(DEFAULT_ROBOT_NAME).mark_delivered()
    dropoff_event = build_package_status_event(
        "package_delivered",
        delivered_package,
        DEFAULT_ROBOT_NAME,
        "Package dropoff completed.",
    )
    snapshot = build_robot_status_snapshot(
        robot_name=DEFAULT_ROBOT_NAME,
        current_zone="shipping",
        mode="unloading",
        battery_percentage=battery.percentage,
        active_task_id=task.task_id,
        active_navigation_goal_id=goal.goal_id,
        package_id=package.package_id,
        carrying_package=False,
        emergency_stop_active=bool(emergency_command.active) if emergency_command is not None else False,
        last_event=dropoff_event.message,
    )
    diagnostic = build_diagnostic_event(
        source="status",
        health_level=determine_health_level(
            emergency_stop_active=snapshot.emergency_stop_active,
            battery_percentage=snapshot.battery_percentage,
        ),
        message="Scenario diagnostic event.",
        related_id=snapshot.active_task_id,
        robot_name=snapshot.robot_name,
        topic=DIAGNOSTICS_TOPIC,
    )

    return {
        "task": task.to_dict(),
        "navigation_goal": goal.to_dict(),
        "navigation_progress": navigation_progress,
        "obstacle_reading": obstacle.to_dict(),
        "emergency_stop_command": emergency_command.to_dict() if emergency_command is not None else None,
        "battery_state": battery.to_dict(),
        "charge_command": charge_command.to_dict() if charge_command is not None else None,
        "package_info": package.to_dict(),
        "package_events": [pickup_event.to_dict(), dropoff_event.to_dict()],
        "robot_status": snapshot.to_dict(),
        "diagnostic_event": diagnostic.to_dict(),
    }


@scenario_group.command("full-json")
@click.option("--json-output", is_flag=True)
def scenario_full_json_command(json_output: bool) -> None:
    """Generate a full simulated warehouse scenario."""
    scenario = _build_full_scenario()
    if json_output:
        print_json(scenario)
        return

    print_section("Scenario Summary")
    click.echo(f"Task: {scenario['task']['task_id']}")
    click.echo(f"Goal: {scenario['navigation_goal']['goal_id']}")
    click.echo(f"Obstacle severity: {scenario['obstacle_reading']['severity']}")
    click.echo(f"Battery level: {scenario['battery_state']['level']}")
    click.echo(f"Package: {scenario['package_info']['package_id']}")
    print_section("Scenario JSON")
    print_json(scenario)


@scenario_group.command("happy-path")
def scenario_happy_path_command() -> None:
    """Print a normal warehouse flow scenario."""
    steps = [
        "Task created.",
        "Task queued.",
        "Navigation started.",
        "Robot arrived at pickup zone.",
        "Package picked up.",
        "Navigation continued to destination.",
        "Package dropped off.",
        "Robot status remains OK.",
    ]
    for step in steps:
        click.echo(step)


@scenario_group.command("emergency-stop")
def scenario_emergency_stop_command() -> None:
    """Print an emergency stop flow scenario."""
    steps = [
        "Task is running.",
        "Critical obstacle detected.",
        "Emergency stop command published.",
        "Navigation becomes blocked.",
        "Diagnostic event becomes CRITICAL.",
    ]
    for step in steps:
        click.echo(step)


@scenario_group.command("low-battery")
def scenario_low_battery_command() -> None:
    """Print a low-battery return-to-charge flow scenario."""
    steps = [
        "Battery percentage drops below threshold.",
        "Return-to-charge command is created.",
        "Navigation goal to charging_station is published.",
        "Robot arrives at charging station and starts charging.",
        "Diagnostic event shows WARNING, then returns to OK after charging.",
    ]
    for step in steps:
        click.echo(step)


@main.group("validate")
def validate_group() -> None:
    """Validation helpers for samples, structure, and ROS 1 compatibility."""


@validate_group.command("all-samples")
def validate_all_samples_command() -> None:
    """Create sample models and validate JSON round trips."""
    results: list[tuple[str, bool, str]] = []
    samples = [
        ("WarehouseTask", WarehouseTask(task_type="pickup", source_zone="receiving", destination_zone="storage_a", priority=3), WarehouseTask.from_json),
        ("NavigationGoal", NavigationGoal(source_zone="receiving", destination_zone="packing", priority=3), NavigationGoal.from_json),
        ("NavigationProgress", {"goal_id": "GOAL-001", "task_id": "TASK-001", "current_zone": "packing", "destination_zone": "shipping", "progress_percent": 50, "status": "moving", "message": "Halfway"}, None),
        ("ObstacleReading", build_obstacle_reading("storage_a", 0.8, True), ObstacleReading.from_json),
        ("EmergencyStopCommand", build_emergency_stop_command(build_obstacle_reading("storage_a", 0.25, True)), None),
        ("BatteryState", build_battery_state(DEFAULT_ROBOT_NAME, 20, "storage_a"), BatteryState.from_json),
        ("ChargeCommand", build_charge_command(build_battery_state(DEFAULT_ROBOT_NAME, 20, "storage_a")), None),
        ("PackageInfo", build_package_info(None, "storage_a", "shipping"), PackageInfo.from_json),
        ("PackageStatusEvent", build_package_status_event("package_ready", build_package_info(None, "storage_a", "shipping"), DEFAULT_ROBOT_NAME, "Ready"), None),
        ("RobotStatusSnapshot", build_robot_status_snapshot(DEFAULT_ROBOT_NAME, "receiving", "idle", battery_percentage=80), RobotStatusSnapshot.from_json),
        ("DiagnosticEvent", build_diagnostic_event("status", "ok", "Healthy"), DiagnosticEvent.from_json),
    ]
    for name, sample, parser in samples:
        try:
            if name == "NavigationProgress":
                payload = json.dumps(sample, indent=2, sort_keys=True)
                from smart_warehouse_robot.common.models import NavigationProgress

                NavigationProgress.from_json(payload)
            elif parser is None:
                parser = type(sample).from_json
                parser(sample.to_json())
            else:
                parser(sample.to_json())
            results.append((name, True, "round-trip ok"))
        except Exception as exc:  # pragma: no cover - surfaced in CLI output/tests
            results.append((name, False, str(exc)))

    failed = [item for item in results if not item[1]]
    for name, success, message in results:
        (print_success if success else print_error)(f"{name}: {message}")
    click.echo(f"Validated {len(results)} samples.")
    if failed:
        raise click.ClickException(f"{len(failed)} sample validations failed.")


@validate_group.command("project-structure")
def validate_project_structure_command() -> None:
    """Check that important project files exist."""
    required_paths = [
        "CMakeLists.txt",
        "package.xml",
        "setup.py",
        "launch/warehouse_demo.launch",
        "scripts/task_publisher_node.py",
        "scripts/task_queue_manager_node.py",
        "scripts/waypoint_goal_publisher_node.py",
        "scripts/path_progress_monitor_node.py",
        "scripts/obstacle_detector_node.py",
        "scripts/emergency_stop_node.py",
        "scripts/battery_publisher_node.py",
        "scripts/charging_controller_node.py",
        "scripts/package_handler_node.py",
        "scripts/status_publisher_node.py",
        "scripts/diagnostic_logger_node.py",
        "scripts/smart_warehouse_cli.py",
        "scripts/record_demo_bag.sh",
        "scripts/replay_demo_bag.sh",
        "scripts/check_demo_bag.sh",
        "scripts/run_demo_instructions.sh",
        "docs/architecture_overview.md",
        "docs/member_functionality_plan.md",
        "docs/rosbag_recording_guide.md",
        "docs/testing_guide.md",
        "bags/.gitkeep",
    ]
    missing = [path for path in required_paths if not (PROJECT_ROOT / path).exists()]
    if not missing:
        print_success("All required project files are present.")
        return
    for path in missing:
        print_error(f"Missing: {path}")
    raise click.ClickException(f"{len(missing)} required files are missing.")


@validate_group.command("no-ros" + "2")
def validate_no_ros2_command() -> None:
    """Scan runtime project files for forbidden ROS 2 compatibility markers."""
    forbidden_terms = ["rcl" + "py", "ros" + "2", "a" + "ment", ".launch" + ".py", "col" + "con"]
    scan_roots = [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "launch",
        PROJECT_ROOT / "config",
        PROJECT_ROOT / "package.xml",
        PROJECT_ROOT / "CMakeLists.txt",
        PROJECT_ROOT / "setup.py",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "docs",
    ]
    matches: list[str] = []
    for root in scan_roots:
        if not root.exists():
            continue
        paths = root.rglob("*") if root.is_dir() else [root]
        for path in paths:
            if path.is_dir():
                continue
            if any(part in {".git", "build", "devel", "install", "logs", "__pycache__", ".pytest_cache"} for part in path.parts):
                continue
            if path.name == "cli.py":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for line in text.splitlines():
                normalized_line = line.strip()
                if "validate no-ros2" in normalized_line or "validate_no_ros2" in normalized_line:
                    continue
                for term in forbidden_terms:
                    if term in normalized_line:
                        matches.append(f"{path.relative_to(PROJECT_ROOT)}: contains '{term}'")
    if not matches:
        print_success("No forbidden ROS 2 terms found in runtime project files.")
        return
    for match in matches:
        print_warning(match)
    raise click.ClickException("Forbidden ROS 2 compatibility markers were found.")


@main.group("bag")
def bag_group() -> None:
    """Print rosbag helper commands for the final demo."""


@bag_group.command("record-command")
def bag_record_command() -> None:
    """Print the final rosbag record command."""
    print_command(FINAL_BAG_COMMAND)


@bag_group.command("replay-command")
def bag_replay_command() -> None:
    """Print the rosbag replay command."""
    print_command("rosbag play bags/final_demo.bag")


@bag_group.command("info-command")
def bag_info_command() -> None:
    """Print the rosbag info command."""
    print_command("rosbag info bags/final_demo.bag")


@main.command("launch-command")
def launch_command() -> None:
    """Print the launch command and useful topic checks."""
    print_command("roscore")
    print_command("roslaunch smart_warehouse_robot warehouse_demo.launch")
    print_command("rostopic echo /warehouse/tasks/status")
    print_command("rostopic echo /warehouse/navigation/progress")
    print_command("rostopic echo /warehouse/robot/status")
    print_command("rostopic echo /warehouse/robot/diagnostics")


@main.command("member-summary")
def member_summary_command() -> None:
    """Print a table of member responsibilities and implementation status."""
    rows = [
        {"Member": "Member 1", "Area": "Task Management", "Function 1": "Task publisher", "Function 2": "Task queue/status manager", "Status": "Implemented"},
        {"Member": "Member 2", "Area": "Navigation", "Function 1": "Waypoint goal publisher", "Function 2": "Path progress monitor", "Status": "Implemented"},
        {"Member": "Member 3", "Area": "Obstacle Safety", "Function 1": "Obstacle detector", "Function 2": "Emergency stop node", "Status": "Implemented"},
        {"Member": "Member 4", "Area": "Battery System", "Function 1": "Battery state publisher", "Function 2": "Return-to-charge controller", "Status": "Implemented"},
        {"Member": "Member 5", "Area": "Package Handling", "Function 1": "Pickup service", "Function 2": "Dropoff service", "Status": "Implemented"},
        {"Member": "Member 6", "Area": "Status + Diagnostics", "Function 1": "Robot status publisher", "Function 2": "Diagnostic logger", "Status": "Implemented"},
        {"Member": "Member 7", "Area": "CLI + Operations", "Function 1": "Advanced CLI task/operation commands", "Function 2": "CLI simulation/rosbag/demo helpers", "Status": "Implemented"},
        {"Member": "Member 8", "Area": "Testing + Recording", "Function 1": "Pytest scenario validation", "Function 2": "ROS bag recording/launch validation", "Status": "Upcoming"},
    ]
    click.echo(format_table(rows, ["Member", "Area", "Function 1", "Function 2", "Status"]))


@main.command("ros1-commands")
def ros1_commands_command() -> None:
    """Print useful ROS 1 Noetic build, run, and bag commands."""
    commands = [
        "catkin_make",
        "source devel/setup.bash",
        "roslaunch smart_warehouse_robot warehouse_demo.launch",
        "rosrun smart_warehouse_robot task_publisher_node.py",
        "rosrun smart_warehouse_robot battery_publisher_node.py",
        "rosrun smart_warehouse_robot charging_controller_node.py",
        "rosrun smart_warehouse_robot status_publisher_node.py",
        "rosrun smart_warehouse_robot diagnostic_logger_node.py",
        "rosbag record -O bags/final_demo.bag /warehouse/tasks/new /warehouse/tasks/status /warehouse/navigation/goal /warehouse/navigation/progress /warehouse/safety/obstacle /warehouse/safety/emergency_stop /warehouse/battery/state /warehouse/battery/return_to_charge /warehouse/package/status /warehouse/robot/status /warehouse/robot/diagnostics",
        "rosbag play bags/final_demo.bag",
    ]
    for command in commands:
        click.echo(command)


@main.command("status-sample")
def status_sample_command() -> None:
    """Print a sample robot status payload as JSON."""
    click.echo(json.dumps(build_sample_status_payload(), indent=2, sort_keys=True))


@main.command("zones")
def zones_command() -> None:
    """List the available warehouse zones."""
    for zone in WAREHOUSE_ZONES:
        click.echo(zone)


@main.command("validate-zone")
@click.argument("zone_name")
def validate_zone_command(zone_name: str) -> None:
    """Validate a zone name and provide a clear message."""
    if validate_zone(zone_name):
        normalized = parse_warehouse_zone(zone_name)
        click.echo(f"Zone '{normalized.value}' is valid.")
        return

    valid_zones = ", ".join(zone.value for zone in WarehouseZone)
    raise click.ClickException(f"Zone '{zone_name}' is invalid. Available zones: {valid_zones}.")


if __name__ == "__main__":
    main()
