"""Runtime registries for agent, pipeline, and team specs.

Supports loading from YAML, programmatic registration,
and capability-based discovery.
"""

from __future__ import annotations

import structlog

from xteam_agents.platform.spec import AgentSpec, PipelineSpec, TeamSpec

logger = structlog.get_logger()


class AgentRegistry:
    """Central registry for agent specifications."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentSpec] = {}

    def register(self, spec: AgentSpec) -> None:
        if spec.id in self._agents:
            logger.warning("agent_spec_overwritten", agent_id=spec.id)
        self._agents[spec.id] = spec
        logger.debug("agent_spec_registered", agent_id=spec.id, name=spec.name)

    def get(self, agent_id: str) -> AgentSpec:
        if agent_id not in self._agents:
            raise KeyError(f"Agent spec not found: {agent_id}")
        return self._agents[agent_id]

    def get_or_none(self, agent_id: str) -> AgentSpec | None:
        return self._agents.get(agent_id)

    def find_by_capability(self, capability: str) -> list[AgentSpec]:
        return [s for s in self._agents.values() if capability in s.capabilities]

    def find_by_role(self, role: str) -> list[AgentSpec]:
        return [s for s in self._agents.values() if s.role == role]

    def find_by_tags(self, tags: list[str], match_all: bool = False) -> list[AgentSpec]:
        tag_set = set(tags)
        results = []
        for spec in self._agents.values():
            spec_tags = set(spec.tags)
            if match_all:
                if tag_set.issubset(spec_tags):
                    results.append(spec)
            else:
                if tag_set & spec_tags:
                    results.append(spec)
        return results

    def list_all(self) -> list[AgentSpec]:
        return list(self._agents.values())

    def count(self) -> int:
        return len(self._agents)

    def has(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def unregister(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def clear(self) -> None:
        self._agents.clear()


class PipelineRegistry:
    """Registry for pipeline specifications."""

    def __init__(self) -> None:
        self._pipelines: dict[str, PipelineSpec] = {}

    def register(self, spec: PipelineSpec) -> None:
        self._pipelines[spec.id] = spec
        logger.debug("pipeline_spec_registered", pipeline_id=spec.id)

    def get(self, pipeline_id: str) -> PipelineSpec:
        if pipeline_id not in self._pipelines:
            raise KeyError(f"Pipeline spec not found: {pipeline_id}")
        return self._pipelines[pipeline_id]

    def get_or_none(self, pipeline_id: str) -> PipelineSpec | None:
        return self._pipelines.get(pipeline_id)

    def list_all(self) -> list[PipelineSpec]:
        return list(self._pipelines.values())

    def count(self) -> int:
        return len(self._pipelines)

    def has(self, pipeline_id: str) -> bool:
        return pipeline_id in self._pipelines

    def clear(self) -> None:
        self._pipelines.clear()


class TeamRegistry:
    """Registry for team specifications."""

    def __init__(self) -> None:
        self._teams: dict[str, TeamSpec] = {}

    def register(self, spec: TeamSpec) -> None:
        self._teams[spec.id] = spec
        logger.debug("team_spec_registered", team_id=spec.id)

    def get(self, team_id: str) -> TeamSpec:
        if team_id not in self._teams:
            raise KeyError(f"Team spec not found: {team_id}")
        return self._teams[team_id]

    def get_or_none(self, team_id: str) -> TeamSpec | None:
        return self._teams.get(team_id)

    def list_all(self) -> list[TeamSpec]:
        return list(self._teams.values())

    def count(self) -> int:
        return len(self._teams)

    def clear(self) -> None:
        self._teams.clear()
