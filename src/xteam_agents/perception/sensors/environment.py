"""Environment sensors for external event monitoring."""

from typing import Any
from uuid import UUID

import httpx
import structlog

from xteam_agents.models.observation import (
    Observation,
    ObservationSeverity,
    ObservationType,
)
from xteam_agents.perception.sensors.base import Sensor

logger = structlog.get_logger()


class APISensor(Sensor):
    """
    Monitors external API responses.

    Produces observations when:
    - API calls fail
    - Rate limits are hit
    - Response times are slow
    """

    def __init__(self, slow_threshold_ms: int = 5000):
        super().__init__("api_sensor")
        self.slow_threshold_ms = slow_threshold_ms
        self._recent_calls: list[dict[str, Any]] = []

    def record_call(
        self,
        url: str,
        status_code: int,
        duration_ms: int,
        error: str | None = None,
    ) -> None:
        """Record an API call for observation."""
        self._recent_calls.append({
            "url": url,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "error": error,
        })
        # Keep only last 100 calls
        self._recent_calls = self._recent_calls[-100:]

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []

        for call in self._recent_calls:
            # Check for errors
            if call.get("error") or call.get("status_code", 200) >= 400:
                observations.append(
                    Observation(
                        task_id=task_id,
                        observation_type=ObservationType.API_RESPONSE,
                        severity=ObservationSeverity.ERROR,
                        source=self.name,
                        title=f"API Error: {call.get('status_code', 'unknown')}",
                        description=call.get("error") or f"HTTP {call.get('status_code')}",
                        data=call,
                    )
                )

            # Check for rate limiting (429)
            elif call.get("status_code") == 429:
                observations.append(
                    Observation(
                        task_id=task_id,
                        observation_type=ObservationType.API_RESPONSE,
                        severity=ObservationSeverity.WARNING,
                        source=self.name,
                        title="Rate Limit Hit",
                        description=f"Rate limited by {call.get('url')}",
                        data=call,
                        requires_immediate_action=True,
                    )
                )

            # Check for slow responses
            elif call.get("duration_ms", 0) > self.slow_threshold_ms:
                observations.append(
                    Observation(
                        task_id=task_id,
                        observation_type=ObservationType.API_RESPONSE,
                        severity=ObservationSeverity.WARNING,
                        source=self.name,
                        title="Slow API Response",
                        description=f"API call took {call.get('duration_ms')}ms",
                        data=call,
                    )
                )

        # Clear processed calls
        self._recent_calls.clear()

        return observations


class CISensor(Sensor):
    """
    Monitors CI/CD pipeline status.

    Produces observations when:
    - Build fails
    - Tests fail
    - Deployment status changes
    """

    def __init__(self, n8n_url: str | None = None, n8n_api_key: str | None = None):
        super().__init__("ci_sensor")
        self.n8n_url = n8n_url
        self.n8n_api_key = n8n_api_key
        self._pending_events: list[dict[str, Any]] = []

    def record_event(self, event: dict[str, Any]) -> None:
        """Record a CI event for observation."""
        self._pending_events.append(event)

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []

        for event in self._pending_events:
            event_type = event.get("type", "unknown")
            status = event.get("status", "unknown")

            severity = ObservationSeverity.INFO
            if status in ["failed", "error"]:
                severity = ObservationSeverity.ERROR
            elif status == "warning":
                severity = ObservationSeverity.WARNING

            observations.append(
                Observation(
                    task_id=task_id,
                    observation_type=ObservationType.CI_STATUS,
                    severity=severity,
                    source=self.name,
                    title=f"CI Event: {event_type}",
                    description=event.get("message", f"CI {event_type} {status}"),
                    data=event,
                    requires_immediate_action=status == "failed",
                )
            )

        self._pending_events.clear()

        return observations

    async def poll_n8n(self) -> list[dict[str, Any]]:
        """Poll n8n for workflow status (if configured)."""
        if not self.n8n_url:
            return []

        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.n8n_api_key:
                    headers["X-N8N-API-KEY"] = self.n8n_api_key

                response = await client.get(
                    f"{self.n8n_url}/api/v1/executions",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return response.json().get("data", [])
        except Exception as e:
            logger.warning("n8n_poll_failed", error=str(e))

        return []


class GitSensor(Sensor):
    """
    Monitors Git repository events.

    Produces observations when:
    - New commits are pushed
    - Pull requests are created/merged
    - Conflicts are detected
    """

    def __init__(self):
        super().__init__("git_sensor")
        self._pending_events: list[dict[str, Any]] = []

    def record_event(self, event: dict[str, Any]) -> None:
        """Record a Git event for observation."""
        self._pending_events.append(event)

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []

        for event in self._pending_events:
            event_type = event.get("type", "unknown")

            severity = ObservationSeverity.INFO
            if event_type == "conflict":
                severity = ObservationSeverity.WARNING
            elif event_type == "force_push":
                severity = ObservationSeverity.WARNING

            observations.append(
                Observation(
                    task_id=task_id,
                    observation_type=ObservationType.GIT_EVENT,
                    severity=severity,
                    source=self.name,
                    title=f"Git Event: {event_type}",
                    description=event.get("message", f"Git {event_type}"),
                    data=event,
                )
            )

        self._pending_events.clear()

        return observations


class FeedbackSensor(Sensor):
    """
    Monitors user feedback.

    Produces observations when:
    - User provides feedback on task results
    - User requests changes
    - User cancels task
    """

    def __init__(self):
        super().__init__("feedback_sensor")
        self._pending_feedback: list[dict[str, Any]] = []

    def record_feedback(
        self,
        task_id: UUID,
        feedback_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Record user feedback for observation."""
        self._pending_feedback.append({
            "task_id": str(task_id),
            "type": feedback_type,
            "message": message,
            "data": data or {},
        })

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        observations: list[Observation] = []

        for feedback in self._pending_feedback:
            # Filter by task_id if provided
            if task_id and feedback.get("task_id") != str(task_id):
                continue

            feedback_type = feedback.get("type", "general")

            severity = ObservationSeverity.INFO
            requires_action = False

            if feedback_type == "rejection":
                severity = ObservationSeverity.WARNING
                requires_action = True
            elif feedback_type == "cancel":
                severity = ObservationSeverity.WARNING
                requires_action = True

            observations.append(
                Observation(
                    task_id=UUID(feedback["task_id"]) if feedback.get("task_id") else None,
                    observation_type=ObservationType.USER_FEEDBACK,
                    severity=severity,
                    source=self.name,
                    title=f"User Feedback: {feedback_type}",
                    description=feedback.get("message", ""),
                    data=feedback.get("data", {}),
                    requires_immediate_action=requires_action,
                )
            )

        # Clear processed feedback
        self._pending_feedback = [
            f for f in self._pending_feedback
            if task_id is None or f.get("task_id") != str(task_id)
        ]

        return observations
