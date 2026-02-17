"""Meta-reasoning agent that observes and optimizes the multi-agent system.

Analyzes execution traces, identifies patterns, and suggests
topology optimizations for improved performance.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from xteam_agents.memory.manager import MemoryManager
    from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry

logger = structlog.get_logger()


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for a single agent."""

    agent_id: str
    total_invocations: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_tokens_used: float = 0.0
    avg_execution_time: float = 0.0
    avg_quality_score: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_invocations == 0:
            return 0.0
        return self.success_count / self.total_invocations


class PipelinePerformanceMetrics(BaseModel):
    """Performance metrics for a pipeline."""

    pipeline_id: str
    total_executions: int = 0
    success_count: int = 0
    avg_execution_time: float = 0.0
    avg_tokens_used: float = 0.0
    avg_depth_reached: float = 0.0
    agent_metrics: dict[str, AgentPerformanceMetrics] = Field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.success_count / self.total_executions


class OptimizationSuggestion(BaseModel):
    """A suggestion for topology optimization."""

    suggestion_type: str
    target_id: str
    description: str
    expected_impact: str
    confidence: float = Field(ge=0.0, le=1.0)
    data: dict[str, Any] = Field(default_factory=dict)


class MetaAgent:
    """Meta-reasoning agent that optimizes the multi-agent system.

    Capabilities:
    - Analyze execution traces from audit log
    - Identify performance bottlenecks
    - Suggest topology optimizations
    - Track agent performance metrics
    - Recommend team compositions based on historical data
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        pipeline_registry: PipelineRegistry,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.pipeline_registry = pipeline_registry
        self.memory_manager = memory_manager

        self._pipeline_metrics: dict[str, PipelinePerformanceMetrics] = {}
        self._agent_metrics: dict[str, AgentPerformanceMetrics] = {}
        self._suggestions: list[OptimizationSuggestion] = []

    def record_pipeline_execution(
        self,
        pipeline_id: str,
        success: bool,
        execution_time: float,
        tokens_used: int,
        depth_reached: int,
        agent_stats: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Record metrics from a pipeline execution."""
        if pipeline_id not in self._pipeline_metrics:
            self._pipeline_metrics[pipeline_id] = PipelinePerformanceMetrics(
                pipeline_id=pipeline_id,
            )

        m = self._pipeline_metrics[pipeline_id]
        m.total_executions += 1
        if success:
            m.success_count += 1

        n = m.total_executions
        m.avg_execution_time = (m.avg_execution_time * (n - 1) + execution_time) / n
        m.avg_tokens_used = (m.avg_tokens_used * (n - 1) + tokens_used) / n
        m.avg_depth_reached = (m.avg_depth_reached * (n - 1) + depth_reached) / n

        if agent_stats:
            for agent_id, stats in agent_stats.items():
                self._record_agent_metrics(agent_id, stats)

    def _record_agent_metrics(self, agent_id: str, stats: dict[str, Any]) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentPerformanceMetrics(agent_id=agent_id)

        m = self._agent_metrics[agent_id]
        m.total_invocations += 1
        if stats.get("success", True):
            m.success_count += 1
        else:
            m.failure_count += 1

        n = m.total_invocations
        if "tokens_used" in stats:
            m.avg_tokens_used = (m.avg_tokens_used * (n - 1) + stats["tokens_used"]) / n
        if "execution_time" in stats:
            m.avg_execution_time = (m.avg_execution_time * (n - 1) + stats["execution_time"]) / n

    def analyze(self) -> list[OptimizationSuggestion]:
        """Analyze metrics and generate optimization suggestions."""
        suggestions: list[OptimizationSuggestion] = []

        for agent_id, m in self._agent_metrics.items():
            if m.total_invocations >= 5 and m.success_rate < 0.5:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="adjust_agent",
                    target_id=agent_id,
                    description=(
                        f"Agent {agent_id} has low success rate ({m.success_rate:.1%}). "
                        f"Consider adjusting temperature or model."
                    ),
                    expected_impact="Improved success rate",
                    confidence=0.7,
                    data={"success_rate": m.success_rate, "invocations": m.total_invocations},
                ))

        for pipeline_id, m in self._pipeline_metrics.items():
            if m.total_executions >= 3 and m.avg_execution_time > 120:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="optimize_pipeline",
                    target_id=pipeline_id,
                    description=(
                        f"Pipeline {pipeline_id} is slow (avg {m.avg_execution_time:.0f}s). "
                        f"Consider reducing team size or parallelizing."
                    ),
                    expected_impact="Reduced execution time",
                    confidence=0.6,
                    data={"avg_time": m.avg_execution_time},
                ))

        for agent_id, m in self._agent_metrics.items():
            if m.total_invocations >= 3 and m.avg_tokens_used > 10000:
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="reduce_tokens",
                    target_id=agent_id,
                    description=(
                        f"Agent {agent_id} uses many tokens (avg {m.avg_tokens_used:.0f}). "
                        f"Consider a smaller model or refined prompt."
                    ),
                    expected_impact="Reduced token cost",
                    confidence=0.5,
                    data={"avg_tokens": m.avg_tokens_used},
                ))

        self._suggestions = suggestions
        return suggestions

    def get_pipeline_metrics(self) -> dict[str, PipelinePerformanceMetrics]:
        return dict(self._pipeline_metrics)

    def get_agent_metrics(self) -> dict[str, AgentPerformanceMetrics]:
        return dict(self._agent_metrics)

    def get_suggestions(self) -> list[OptimizationSuggestion]:
        return list(self._suggestions)

    def recommend_pipeline_for_task(self, task_description: str) -> str | None:
        """Recommend best pipeline based on historical success rate."""
        best_pipeline = None
        best_rate = 0.0
        for pipeline_id, m in self._pipeline_metrics.items():
            if m.total_executions >= 3 and m.success_rate > best_rate:
                best_rate = m.success_rate
                best_pipeline = pipeline_id
        return best_pipeline
