"""Topology optimizer that suggests and applies pipeline modifications.

Works with MetaAgent to improve the multi-agent system over time.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import structlog

from xteam_agents.platform.meta_agent import MetaAgent, OptimizationSuggestion
from xteam_agents.platform.spec import AgentSpec

if TYPE_CHECKING:
    from xteam_agents.platform.registry import AgentRegistry

logger = structlog.get_logger()


class TopologyOptimizer:
    """Applies optimization suggestions to the agent registry."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        meta_agent: MetaAgent,
    ) -> None:
        self.agent_registry = agent_registry
        self.meta_agent = meta_agent
        self._applied: list[dict[str, Any]] = []

    def get_suggestions(self) -> list[OptimizationSuggestion]:
        return self.meta_agent.analyze()

    def apply_suggestion(self, suggestion: OptimizationSuggestion) -> bool:
        """Apply an optimization suggestion. Returns True if applied."""
        try:
            if suggestion.suggestion_type == "adjust_agent":
                return self._adjust_agent(suggestion)
            elif suggestion.suggestion_type == "reduce_tokens":
                return self._reduce_agent_tokens(suggestion)
            else:
                logger.info("suggestion_not_auto_applicable", type=suggestion.suggestion_type)
                return False
        except Exception as e:
            logger.error("suggestion_apply_failed", error=str(e))
            return False

    def _adjust_agent(self, suggestion: OptimizationSuggestion) -> bool:
        agent = self.agent_registry.get_or_none(suggestion.target_id)
        if not agent:
            return False

        new_temp = min(agent.temperature + 0.1, 1.0)
        modified = AgentSpec(
            **{
                **agent.model_dump(),
                "temperature": new_temp,
                "metadata": {**agent.metadata, "optimized": True,
                             "optimization_reason": suggestion.description},
            }
        )
        self.agent_registry.register(modified)
        self._applied.append({
            "suggestion": suggestion.model_dump(),
            "change": f"temperature {agent.temperature} -> {new_temp}",
        })
        logger.info("agent_optimized", agent_id=agent.id, change=f"temp: {agent.temperature}->{new_temp}")
        return True

    def _reduce_agent_tokens(self, suggestion: OptimizationSuggestion) -> bool:
        agent = self.agent_registry.get_or_none(suggestion.target_id)
        if not agent:
            return False

        new_max = max(1024, int(agent.max_tokens * 0.75))
        modified = AgentSpec(
            **{
                **agent.model_dump(),
                "max_tokens": new_max,
                "metadata": {**agent.metadata, "optimized": True,
                             "optimization_reason": suggestion.description},
            }
        )
        self.agent_registry.register(modified)
        self._applied.append({
            "suggestion": suggestion.model_dump(),
            "change": f"max_tokens {agent.max_tokens} -> {new_max}",
        })
        logger.info("agent_tokens_reduced", agent_id=agent.id, change=f"tokens: {agent.max_tokens}->{new_max}")
        return True

    def get_applied_optimizations(self) -> list[dict[str, Any]]:
        return list(self._applied)
