"""System sensors for internal state monitoring."""

from datetime import datetime
from typing import Any
from uuid import UUID

from xteam_agents.models.observation import (
    Observation,
    ObservationSeverity,
    ObservationType,
)
from xteam_agents.models.state import AgentState
from xteam_agents.perception.sensors.base import Sensor


class TaskStateSensor(Sensor):
    """
    Monitors task state for important transitions.

    Produces observations when:
    - Task enters a new node
    - Iteration count increases
    - Validation state changes
    """

    def __init__(self):
        super().__init__("task_state_sensor")
        self._previous_states: dict[UUID, dict[str, Any]] = {}

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []

        if context is None or "state" not in context:
            return observations

        state: AgentState = context["state"]

        # Get previous state for comparison
        prev = self._previous_states.get(state.task_id, {})

        # Check for node transition
        if prev.get("current_node") != state.current_node:
            observations.append(
                Observation(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    observation_type=ObservationType.TASK_STATE,
                    source=self.name,
                    title=f"Node Transition: {state.current_node}",
                    description=f"Task transitioned from {prev.get('current_node', 'start')} to {state.current_node}",
                    data={
                        "previous_node": prev.get("current_node"),
                        "current_node": state.current_node,
                        "iteration": state.iteration_count,
                    },
                )
            )

        # Check for validation state change
        if prev.get("is_validated") != state.is_validated and state.is_validated:
            observations.append(
                Observation(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    observation_type=ObservationType.TASK_STATE,
                    source=self.name,
                    title="Task Validated",
                    description="Task execution has been validated by reviewer",
                    data={"validation_attempts": state.validation_attempts},
                )
            )

        # Check for max iterations approaching
        if state.iteration_count >= state.max_iterations - 2:
            observations.append(
                Observation(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    observation_type=ObservationType.TASK_STATE,
                    severity=ObservationSeverity.WARNING,
                    source=self.name,
                    title="Max Iterations Approaching",
                    description=f"Task has used {state.iteration_count} of {state.max_iterations} iterations",
                    data={
                        "current": state.iteration_count,
                        "max": state.max_iterations,
                    },
                    requires_immediate_action=True,
                )
            )

        # Store current state for next comparison
        self._previous_states[state.task_id] = {
            "current_node": state.current_node,
            "is_validated": state.is_validated,
            "iteration_count": state.iteration_count,
        }

        return observations


class ErrorSensor(Sensor):
    """
    Monitors for errors in task execution.

    Produces observations when:
    - Task has an error set
    - Task is marked as failed
    """

    def __init__(self):
        super().__init__("error_sensor")

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []

        if context is None or "state" not in context:
            return observations

        state: AgentState = context["state"]

        if state.error:
            severity = (
                ObservationSeverity.CRITICAL
                if state.is_failed
                else ObservationSeverity.ERROR
            )
            observations.append(
                Observation(
                    task_id=state.task_id,
                    session_id=state.session_id,
                    observation_type=ObservationType.ERROR,
                    severity=severity,
                    source=self.name,
                    title="Task Error",
                    description=state.error,
                    data={
                        "is_failed": state.is_failed,
                        "current_node": state.current_node,
                    },
                    requires_immediate_action=not state.is_failed,
                    is_blocking=state.is_failed,
                )
            )

        return observations


class BudgetSensor(Sensor):
    """
    Monitors resource budget consumption.

    Produces observations when:
    - Token usage exceeds thresholds
    - Time budget is running low
    """

    def __init__(self, token_warning_threshold: int = 50000):
        super().__init__("budget_sensor")
        self.token_warning_threshold = token_warning_threshold

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []

        if context is None:
            return observations

        # Check token usage
        token_usage = context.get("token_usage", {})
        total_tokens = token_usage.get("total_tokens", 0)

        if total_tokens > self.token_warning_threshold:
            observations.append(
                Observation(
                    task_id=task_id,
                    observation_type=ObservationType.BUDGET,
                    severity=ObservationSeverity.WARNING,
                    source=self.name,
                    title="Token Budget Warning",
                    description=f"Task has used {total_tokens} tokens",
                    data={
                        "total_tokens": total_tokens,
                        "threshold": self.token_warning_threshold,
                    },
                )
            )

        # Check time budget
        start_time = context.get("start_time")
        timeout = context.get("timeout_seconds")

        if start_time and timeout:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            remaining = timeout - elapsed

            if remaining < timeout * 0.2:  # Less than 20% time remaining
                observations.append(
                    Observation(
                        task_id=task_id,
                        observation_type=ObservationType.BUDGET,
                        severity=ObservationSeverity.WARNING,
                        source=self.name,
                        title="Time Budget Warning",
                        description=f"Only {remaining:.0f} seconds remaining",
                        data={
                            "elapsed_seconds": elapsed,
                            "remaining_seconds": remaining,
                            "timeout_seconds": timeout,
                        },
                        requires_immediate_action=True,
                    )
                )

        return observations
