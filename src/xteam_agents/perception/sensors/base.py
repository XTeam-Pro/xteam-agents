"""Base sensor interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from xteam_agents.models.observation import Observation


class Sensor(ABC):
    """
    Abstract base class for sensors.

    Sensors observe the environment and produce Observations
    that inform agent decision-making.
    """

    def __init__(self, name: str):
        self.name = name
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if sensor is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable the sensor."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the sensor."""
        self._enabled = False

    @abstractmethod
    async def observe(
        self,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[Observation]:
        """
        Observe the environment and return observations.

        Args:
            task_id: Optional task ID for task-specific observations
            context: Optional context for the observation

        Returns:
            List of observations (may be empty)
        """
        pass

    async def setup(self) -> None:
        """
        Setup the sensor (called once at startup).

        Override this for sensors that need initialization.
        """
        pass

    async def teardown(self) -> None:
        """
        Teardown the sensor (called at shutdown).

        Override this for sensors that need cleanup.
        """
        pass
