"""XTeam Agents Platform — Recursive Multi-Agent System Runtime.

Provides declarative agent specifications, dynamic graph building,
recursive pipeline execution, and self-optimizing topology.
"""

from xteam_agents.platform.budget import ResourceBudget
from xteam_agents.platform.context import ExecutionContext, PipelineResult
from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry, TeamRegistry
from xteam_agents.platform.spec import (
    AgentSpec,
    ConditionalEdgeSpec,
    CriticSpec,
    CriticStrategy,
    EdgeSpec,
    MemoryPermissions,
    NodeSpec,
    PairConfig,
    PairSpec,
    PipelineSpec,
    TeamSpec,
)

__all__ = [
    "AgentRegistry",
    "AgentSpec",
    "ConditionalEdgeSpec",
    "CriticSpec",
    "CriticStrategy",
    "EdgeSpec",
    "ExecutionContext",
    "MemoryPermissions",
    "NodeSpec",
    "PairConfig",
    "PairSpec",
    "PipelineRegistry",
    "PipelineResult",
    "PipelineSpec",
    "ResourceBudget",
    "TeamRegistry",
    "TeamSpec",
]
