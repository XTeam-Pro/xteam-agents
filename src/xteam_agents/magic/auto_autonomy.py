"""Auto-autonomy adjustment loop.

Periodically evaluates evolution metrics via MAGIC SDK and
recommends/applies autonomy level changes. Can run as a background
task in the orchestrator.
"""

import asyncio
from datetime import datetime

import structlog

from xteam_agents.config import Settings
from xteam_agents.models.magic import AutonomyLevel

logger = structlog.get_logger()


class AutoAutonomyAdjuster:
    """Background service that auto-adjusts autonomy level based on metrics."""

    def __init__(
        self,
        settings: Settings,
        evolution_engine: object,
        initial_level: AutonomyLevel = AutonomyLevel.COLLABORATIVE,
    ) -> None:
        self._settings = settings
        self._evolution = evolution_engine
        self._current_level = initial_level
        self._running = False
        self._task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._adjustment_log: list[dict] = []

    @property
    def current_level(self) -> AutonomyLevel:
        return self._current_level

    @property
    def adjustment_log(self) -> list[dict]:
        return list(self._adjustment_log)

    def start(self, check_interval: int = 3600) -> None:
        """Start the background adjustment loop.

        Args:
            check_interval: Seconds between checks (default: 1 hour).
        """
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._loop(check_interval))
        logger.info("auto_autonomy_started", interval=check_interval)

    def stop(self) -> None:
        """Stop the background adjustment loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("auto_autonomy_stopped")

    async def check_and_adjust(self) -> dict:
        """Run a single check cycle. Returns adjustment result."""
        recommended = self._evolution.recommend_autonomy_adjustment(
            current_level=self._current_level,
            period_days=7,
        )

        result = {
            "previous_level": self._current_level.value,
            "recommended_level": recommended.value,
            "applied": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if recommended != self._current_level:
            old = self._current_level
            self._current_level = recommended
            result["applied"] = True

            self._adjustment_log.append(result)

            logger.info(
                "autonomy_adjusted",
                previous=old.value,
                new=recommended.value,
            )

        # Include metrics snapshot
        metrics = self._evolution.compute_metrics(period_days=7)
        result["metrics"] = [
            {"name": m.name, "value": m.value, "trend": m.trend}
            for m in metrics
        ]
        result["proposals"] = self._evolution.get_improvement_proposals()

        return result

    async def _loop(self, interval: int) -> None:
        """Background loop that periodically checks and adjusts."""
        while self._running:
            try:
                await self.check_and_adjust()
            except Exception as e:
                logger.warning("auto_autonomy_check_failed", error=str(e))

            await asyncio.sleep(interval)
