"""Perception engine that aggregates sensor observations."""

from typing import Any
from uuid import UUID

import structlog

from xteam_agents.config import Settings
from xteam_agents.models.observation import Observation, ObservationSeverity
from xteam_agents.perception.sensors.base import Sensor
from xteam_agents.perception.sensors.environment import (
    APISensor,
    CISensor,
    FeedbackSensor,
    GitSensor,
)
from xteam_agents.perception.sensors.system import (
    BudgetSensor,
    ErrorSensor,
    TaskStateSensor,
)
from xteam_agents.perception.sensors.temporal import (
    CronSensor,
    DeadlineSensor,
    TimeoutSensor,
)

logger = structlog.get_logger()


class PerceptionEngine:
    """
    Aggregates observations from all sensors.

    The perception engine collects observations from various sensors
    and provides a unified view of the environment to agents.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._sensors: dict[str, Sensor] = {}
        self._setup_default_sensors()

    def _setup_default_sensors(self) -> None:
        """Setup default sensors."""
        # System sensors
        self.register_sensor(TaskStateSensor())
        self.register_sensor(ErrorSensor())
        self.register_sensor(BudgetSensor())

        # Environment sensors
        self.register_sensor(APISensor())
        self.register_sensor(
            CISensor(
                n8n_url=self.settings.n8n_url,
                n8n_api_key=(
                    self.settings.n8n_api_key.get_secret_value()
                    if self.settings.n8n_api_key
                    else None
                ),
            )
        )
        self.register_sensor(GitSensor())
        self.register_sensor(FeedbackSensor())

        # Temporal sensors
        self.register_sensor(DeadlineSensor())
        self.register_sensor(TimeoutSensor())
        self.register_sensor(CronSensor())

    def register_sensor(self, sensor: Sensor) -> None:
        """Register a sensor with the engine."""
        self._sensors[sensor.name] = sensor
        logger.debug("sensor_registered", sensor=sensor.name)

    def get_sensor(self, name: str) -> Sensor | None:
        """Get a sensor by name."""
        return self._sensors.get(name)

    def list_sensors(self) -> list[str]:
        """List all registered sensor names."""
        return list(self._sensors.keys())

    async def setup(self) -> None:
        """Setup all sensors."""
        for sensor in self._sensors.values():
            await sensor.setup()
        logger.info("perception_engine_setup", sensor_count=len(self._sensors))

    async def teardown(self) -> None:
        """Teardown all sensors."""
        for sensor in self._sensors.values():
            await sensor.teardown()
        logger.info("perception_engine_teardown")

    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        """
        Collect observations from all enabled sensors.

        Args:
            task_id: Optional task ID for task-specific observations
            context: Optional context for sensors

        Returns:
            List of all observations sorted by severity
        """
        all_observations: list[Observation] = []

        for sensor in self._sensors.values():
            if not sensor.enabled:
                continue

            try:
                observations = await sensor.observe(task_id, context)
                all_observations.extend(observations)
            except Exception as e:
                logger.error(
                    "sensor_observe_error",
                    sensor=sensor.name,
                    error=str(e),
                )

        # Sort by severity (critical first)
        severity_order = {
            ObservationSeverity.CRITICAL: 0,
            ObservationSeverity.ERROR: 1,
            ObservationSeverity.WARNING: 2,
            ObservationSeverity.INFO: 3,
        }
        all_observations.sort(key=lambda o: severity_order.get(o.severity, 4))

        return all_observations

    async def observe_blocking(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        """
        Get only blocking observations.

        Blocking observations require immediate attention and may
        halt task execution.
        """
        observations = await self.observe(task_id, context)
        return [o for o in observations if o.is_blocking]

    async def observe_actionable(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        """
        Get observations that require immediate action.

        These are observations that need attention but don't necessarily
        block execution.
        """
        observations = await self.observe(task_id, context)
        return [o for o in observations if o.requires_immediate_action]

    def get_observations_summary(self, observations: list[Observation]) -> str:
        """
        Generate a summary of observations for agent context.

        Args:
            observations: List of observations to summarize

        Returns:
            Human-readable summary string
        """
        if not observations:
            return "No observations."

        lines = []
        for obs in observations:
            lines.append(obs.to_message())

        return "\n\n".join(lines)
