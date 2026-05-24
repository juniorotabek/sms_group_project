"""Pure navigation simulation logic for waypoint progress updates."""

from __future__ import annotations

from smart_warehouse_robot.common.constants import DEFAULT_NAVIGATION_STEP_PERCENT
from smart_warehouse_robot.common.helpers import clamp_progress
from smart_warehouse_robot.common.models import NavigationGoal, NavigationProgress, NavigationStatus


class NavigationSimulator:
    """Simulate progress toward a navigation goal without any ROS dependency."""

    def __init__(self, step_percent: float = DEFAULT_NAVIGATION_STEP_PERCENT) -> None:
        self.step_percent = float(step_percent)
        self._current_goal: NavigationGoal | None = None
        self._progress_percent = 0.0

    def set_goal(self, goal: NavigationGoal) -> NavigationGoal:
        """Store a new goal and reset progress to the start."""
        if not isinstance(goal, NavigationGoal):
            raise ValueError("NavigationSimulator requires a valid NavigationGoal.")

        self._current_goal = goal
        self._current_goal.mark_received()
        self._progress_percent = 0.0
        return self._current_goal

    def has_active_goal(self) -> bool:
        """Return True when a goal exists and is not terminal."""
        return self._current_goal is not None and not self._current_goal.is_terminal()

    def get_current_goal(self) -> NavigationGoal | None:
        """Return the currently tracked goal, if any."""
        return self._current_goal

    def step(self) -> NavigationProgress:
        """Advance the current goal and return a progress update."""
        if self._current_goal is None:
            return NavigationProgress(
                goal_id="GOAL-IDLE",
                task_id=None,
                current_zone="receiving",
                destination_zone="receiving",
                progress_percent=0.0,
                status=NavigationStatus.IDLE,
                message="No active navigation goal.",
            )

        if self._current_goal.status == NavigationStatus.BLOCKED:
            return self._build_progress("Navigation is blocked.")

        if self._current_goal.status == NavigationStatus.CANCELLED:
            return self._build_progress("Navigation goal has been cancelled.")

        if self._current_goal.status == NavigationStatus.FAILED:
            return self._build_progress("Navigation goal has failed.")

        if self._current_goal.status == NavigationStatus.ARRIVED:
            return self._build_progress("Robot already arrived at destination.")

        if self._current_goal.status == NavigationStatus.GOAL_RECEIVED:
            self._current_goal.mark_moving()

        self._progress_percent = clamp_progress(self._progress_percent + self.step_percent)
        if self._progress_percent >= 100.0:
            self._current_goal.mark_arrived()
            self._progress_percent = 100.0
            return self._build_progress("Robot arrived at destination.")

        return self._build_progress("Robot moving toward destination.")

    def cancel_current_goal(self) -> NavigationProgress:
        """Cancel the current goal if one exists."""
        if self._current_goal is None:
            return self.step()

        self._current_goal.mark_cancelled()
        return self._build_progress("Navigation goal cancelled.")

    def block_current_goal(self, reason: str = "Obstacle detected") -> NavigationProgress:
        """Block the current goal without making it terminal."""
        if self._current_goal is None:
            return self.step()

        self._current_goal.mark_blocked()
        return self._build_progress(reason)

    def reset_if_terminal(self) -> None:
        """Clear the current goal after a terminal state."""
        if self._current_goal is not None and self._current_goal.is_terminal():
            self._current_goal = None
            self._progress_percent = 0.0

    def _build_progress(self, message: str) -> NavigationProgress:
        current_zone = self._current_goal.source_zone
        if self._progress_percent >= 100.0:
            current_zone = self._current_goal.destination_zone

        return NavigationProgress(
            goal_id=self._current_goal.goal_id,
            task_id=self._current_goal.task_id,
            current_zone=current_zone,
            destination_zone=self._current_goal.destination_zone,
            progress_percent=self._progress_percent,
            status=self._current_goal.status,
            message=message,
        )
