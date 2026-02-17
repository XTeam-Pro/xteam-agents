"""Semantic capability matching for agent selection.

Matches task requirements to agent capabilities using keyword
and score-based approaches.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from xteam_agents.platform.registry import AgentRegistry
from xteam_agents.platform.spec import AgentSpec

logger = structlog.get_logger()


@dataclass
class MatchResult:
    """Result of capability matching."""

    agent: AgentSpec
    score: float
    matched_capabilities: list[str] = field(default_factory=list)
    matched_tags: list[str] = field(default_factory=list)


class CapabilityMatcher:
    """Matches task requirements to agent capabilities."""

    def __init__(self, agent_registry: AgentRegistry) -> None:
        self.agent_registry = agent_registry

    def match(
        self,
        required_capabilities: list[str] | None = None,
        required_tags: list[str] | None = None,
        keywords: list[str] | None = None,
        min_score: float = 0.1,
    ) -> list[MatchResult]:
        """Find agents matching the given requirements.

        Returns sorted list (highest score first).
        """
        required_caps = set(required_capabilities or [])
        required_tag_set = set(required_tags or [])
        kw_set = {kw.lower() for kw in (keywords or [])}

        results: list[MatchResult] = []

        for agent in self.agent_registry.list_all():
            score = 0.0
            matched_caps: list[str] = []
            matched_tags: list[str] = []

            # Capability matching (weight: 0.5)
            if required_caps:
                agent_caps = set(agent.capabilities)
                intersection = required_caps & agent_caps
                if intersection:
                    score += len(intersection) / len(required_caps) * 0.5
                    matched_caps = list(intersection)

            # Tag matching (weight: 0.3)
            if required_tag_set:
                agent_tags = set(agent.tags)
                tag_intersection = required_tag_set & agent_tags
                if tag_intersection:
                    score += len(tag_intersection) / len(required_tag_set) * 0.3
                    matched_tags = list(tag_intersection)

            # Keyword matching (weight: 0.2)
            if kw_set:
                searchable = (
                    f"{agent.name} {agent.role} "
                    f"{' '.join(agent.capabilities)} "
                    f"{' '.join(agent.tags)}"
                ).lower()
                kw_matches = sum(1 for kw in kw_set if kw in searchable)
                if kw_matches:
                    score += kw_matches / len(kw_set) * 0.2

            if score >= min_score:
                results.append(MatchResult(
                    agent=agent,
                    score=score,
                    matched_capabilities=matched_caps,
                    matched_tags=matched_tags,
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results
