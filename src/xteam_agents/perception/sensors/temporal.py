"""Temporal sensors for time-based monitoring."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from xteam_agents.models.observation import (
    Observation,
    ObservationSeverity,
    ObservationType,
)
from xteam_agents.perception.sensors.base import Sensor


class DeadlineSensor(Sensor):
    """
    Monitors task deadlines.

    Produces observations when:
    - Deadline is approaching
    - Deadline has passed
    """

    def __init__(self, warning_threshold_minutes: int = 30):
        super().__init__("deadline_sensor")
        self.warning_threshold = timedelta(minutes=warning_threshold_minutes)
        self._deadlines: dict[UUID, datetime] = {}

    def set_deadline(self, task_id: UUID, deadline: datetime) -> None:
        """Set a deadline for a task."""
        self._deadlines[task_id] = deadline

    def clear_deadline(self, task_id: UUID) -> None:
        """Clear a task's deadline."""
        self._deadlines.pop(task_id, None)

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []
        now = datetime.utcnow()

        # Check specific task or all tasks
        tasks_to_check = (
            [(task_id, self._deadlines.get(task_id))]
            if task_id and task_id in self._deadlines
            else list(self._deadlines.items())
        )

        for tid, deadline in tasks_to_check:
            if deadline is None:
                continue

            time_remaining = deadline - now

            if time_remaining < timedelta(0):
                # Deadline passed
                observations.append(
                    Observation(
                        task_id=tid,
                        observation_type=ObservationType.DEADLINE,
                        severity=ObservationSeverity.CRITICAL,
                        source=self.name,
                        title="Deadline Passed",
                        description=f"Task deadline passed {abs(time_remaining).total_seconds() / 60:.0f} minutes ago",
                        data={
                            "deadline": deadline.isoformat(),
                            "overdue_minutes": abs(time_remaining).total_seconds() / 60,
                        },
                        requires_immediate_action=True,
                        is_blocking=True,
                    )
                )
            elif time_remaining < self.warning_threshold:
                # Deadline approaching
                observations.append(
                    Observation(
                        task_id=tid,
                        observation_type=ObservationType.DEADLINE,
                        severity=ObservationSeverity.WARNING,
                        source=self.name,
                        title="Deadline Approaching",
                        description=f"Task deadline in {time_remaining.total_seconds() / 60:.0f} minutes",
                        data={
                            "deadline": deadline.isoformat(),
                            "remaining_minutes": time_remaining.total_seconds() / 60,
                        },
                        requires_immediate_action=True,
                    )
                )

        return observations


class TimeoutSensor(Sensor):
    """
    Monitors task execution timeouts.

    Produces observations when:
    - Task is approaching timeout
    - Task has timed out
    """

    def __init__(self, warning_threshold_percent: float = 0.8):
        super().__init__("timeout_sensor")
        self.warning_threshold = warning_threshold_percent
        self._timeouts: dict[UUID, tuple[datetime, int]] = {}  # (start_time, timeout_seconds)

    def start_timeout(self, task_id: UUID, timeout_seconds: int) -> None:
        """Start a timeout for a task."""
        self._timeouts[task_id] = (datetime.utcnow(), timeout_seconds)

    def clear_timeout(self, task_id: UUID) -> None:
        """Clear a task's timeout."""
        self._timeouts.pop(task_id, None)

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []
        now = datetime.utcnow()

        # Check specific task or all tasks
        tasks_to_check = (
            [(task_id, self._timeouts.get(task_id))]
            if task_id and task_id in self._timeouts
            else list(self._timeouts.items())
        )

        for tid, timeout_info in tasks_to_check:
            if timeout_info is None:
                continue

            start_time, timeout_seconds = timeout_info
            elapsed = (now - start_time).total_seconds()
            remaining = timeout_seconds - elapsed
            progress = elapsed / timeout_seconds

            if remaining <= 0:
                # Timed out
                observations.append(
                    Observation(
                        task_id=tid,
                        observation_type=ObservationType.TIMEOUT,
                        severity=ObservationSeverity.CRITICAL,
                        source=self.name,
                        title="Task Timed Out",
                        description=f"Task exceeded timeout of {timeout_seconds} seconds",
                        data={
                            "elapsed_seconds": elapsed,
                            "timeout_seconds": timeout_seconds,
                        },
                        requires_immediate_action=True,
                        is_blocking=True,
                    )
                )
            elif progress >= self.warning_threshold:
                # Approaching timeout
                observations.append(
                    Observation(
                        task_id=tid,
                        observation_type=ObservationType.TIMEOUT,
                        severity=ObservationSeverity.WARNING,
                        source=self.name,
                        title="Timeout Approaching",
                        description=f"Task has {remaining:.0f} seconds remaining",
                        data={
                            "elapsed_seconds": elapsed,
                            "remaining_seconds": remaining,
                            "timeout_seconds": timeout_seconds,
                            "progress_percent": progress * 100,
                        },
                        requires_immediate_action=True,
                    )
                )

        return observations


class CronSensor(Sensor):
    """
    Monitors scheduled events (cron-like).

    Produces observations when:
    - Scheduled time arrives
    - Periodic check is due
    """

    def __init__(self):
        super().__init__("cron_sensor")
        self._schedules: dict[str, dict[str, Any]] = {}
        self._last_triggered: dict[str, datetime] = {}

    def add_schedule(
        self,
        name: str,
        interval_seconds: int,
        task_id: UUID | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Add a scheduled event."""
        self._schedules[name] = {
            "interval_seconds": interval_seconds,
            "task_id": task_id,
            "data": data or {},
        }
        self._last_triggered[name] = datetime.utcnow()

    def remove_schedule(self, name: str) -> None:
        """Remove a scheduled event."""
        self._schedules.pop(name, None)
        self._last_triggered.pop(name, None)

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []
        now = datetime.utcnow()

        for name, schedule in self._schedules.items():
            # Filter by task_id if provided
            schedule_task_id = schedule.get("task_id")
            if task_id and schedule_task_id and schedule_task_id != task_id:
                continue

            last_triggered = self._last_triggered.get(name)
            if last_triggered is None:
                last_triggered = now
                self._last_triggered[name] = now

            elapsed = (now - last_triggered).total_seconds()
            interval = schedule["interval_seconds"]

            if elapsed >= interval:
                observations.append(
                    Observation(
                        task_id=schedule_task_id,
                        observation_type=ObservationType.CRON,
                        severity=ObservationSeverity.INFO,
                        source=self.name,
                        title=f"Scheduled Event: {name}",
                        description=f"Scheduled event '{name}' triggered",
                        data={
                            "schedule_name": name,
                            "interval_seconds": interval,
                            **schedule.get("data", {}),
                        },
                    )
                )
                self._last_triggered[name] = now

        return observations
