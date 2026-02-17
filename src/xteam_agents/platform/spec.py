"""Declarative specifications for agents, pipelines, and teams.

These models define the data schema for the recursive multi-agent platform.
Agents, pipelines, and teams are defined as data (YAML/dict), not code.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryPermissions(str, Enum):
    """Memory access levels for agents."""

    EPISODIC_ONLY = "episodic_only"
    SHARED_READ = "shared_read"
    SHARED_WRITE = "shared_write"


class CriticStrategy(str, Enum):
    """Critic evaluation strategies."""

    CONSTRUCTIVE = "constructive"
    ADVERSARIAL = "adversarial"
    PERFECTIONIST = "perfectionist"


class CriticSpec(BaseModel):
    """Declarative critic specification (inline within AgentSpec)."""

    id: str
    name: str
    role: str
    persona: str
    model: str = "claude-sonnet-4-5"
    temperature: float = 0.7
    max_tokens: int = 4096
    strategy: CriticStrategy = CriticStrategy.CONSTRUCTIVE


class PairConfig(BaseModel):
    """Configuration for agent-critic pair interaction."""

    max_iterations: int = 3
    approval_threshold: float = 7.0
    min_score_threshold: float = 5.0


class AgentSpec(BaseModel):
    """Declarative agent specification.

    Defines everything needed to instantiate and run an agent:
    identity, behavior, capabilities, resource limits, and optional critic.
    """

    # Identity
    id: str
    name: str
    version: str = "1.0"
    role: str
    persona: str

    # Capabilities
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)

    # LLM Config
    model: str = "claude-sonnet-4-5"
    temperature: float = 0.5
    max_tokens: int = 4096

    # Memory
    memory_permissions: MemoryPermissions = MemoryPermissions.EPISODIC_ONLY

    # Recursion
    can_spawn: bool = False
    max_spawn_depth: int = 2

    # Critic (optional, inline)
    critic: CriticSpec | None = None
    pair_config: PairConfig | None = None

    # Metadata
    tags: list[str] = Field(default_factory=list)
    source: str = "builtin"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def has_critic(self) -> bool:
        return self.critic is not None

    def get_critic_spec(self) -> CriticSpec | None:
        return self.critic


class NodeSpec(BaseModel):
    """A node in a pipeline graph."""

    node_name: str
    agent_id: str
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class EdgeSpec(BaseModel):
    """A directed edge between pipeline nodes."""

    source: str
    target: str


class ConditionalEdgeSpec(BaseModel):
    """A conditional edge with routing logic."""

    source: str
    condition: str
    routes: dict[str, str]


class PipelineSpec(BaseModel):
    """Declarative pipeline specification.

    Defines a complete LangGraph topology that can be built at runtime.
    """

    id: str
    name: str
    version: str = "1.0"
    description: str = ""
    entry_point: str
    state_schema: str = "AgentState"

    nodes: list[NodeSpec] = Field(default_factory=list)
    edges: list[EdgeSpec] = Field(default_factory=list)
    conditional_edges: list[ConditionalEdgeSpec] = Field(default_factory=list)

    resource_budget: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PairSpec(BaseModel):
    """Reference to an agent-critic pair in a team."""

    agent: str
    critic: str


class TeamSpec(BaseModel):
    """Declarative team specification."""

    id: str
    name: str
    version: str = "1.0"
    description: str = ""

    pipeline: str
    orchestrator: str | None = None
    pairs: list[PairSpec] = Field(default_factory=list)
    agents: list[str] = Field(default_factory=list)

    max_iterations: int = 3
    approval_threshold: float = 7.0

    metadata: dict[str, Any] = Field(default_factory=dict)
