"""Dynamic team composition based on task analysis.

Uses capability matching and optional LLM analysis to select the optimal team
of agents for a given task, replacing hardcoded complexity-based routing.
"""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

import structlog

from xteam_agents.platform.registry import AgentRegistry, PipelineRegistry, TeamRegistry
from xteam_agents.platform.spec import AgentSpec, PairSpec, TeamSpec

if TYPE_CHECKING:
    from xteam_agents.llm.provider import LLMProvider

logger = structlog.get_logger()

TEAM_COMPOSER_PROMPT = """You are a Team Composer for a multi-agent system.

Given a task description and available agents, select the optimal team composition.

Available agents:
{agents_description}

Task: {task_description}
Context: {task_context}

Select agents needed. Respond in JSON:
{{
    "selected_agents": ["agent.id1", "agent.id2"],
    "selected_pairs": [{{"agent": "agent.id", "critic": "critic.id"}}],
    "needs_orchestrator": true,
    "pipeline": "pipeline.id",
    "rationale": "explanation",
    "estimated_complexity": "simple|medium|complex|critical"
}}
"""

# Keyword -> capability domain mapping
_CAPABILITY_KEYWORDS: dict[str, list[str]] = {
    "security": ["security", "vulnerability", "auth", "encryption", "ssl", "xss", "injection"],
    "performance": ["performance", "optimize", "speed", "latency", "cache", "benchmark"],
    "data": ["database", "data", "query", "sql", "migration", "schema", "etl"],
    "frontend": ["ui", "frontend", "react", "css", "component", "ux", "responsive"],
    "backend": ["api", "backend", "endpoint", "service", "server", "rest", "graphql"],
    "devops": ["deploy", "docker", "ci", "cd", "infrastructure", "kubernetes", "monitoring"],
    "ai": ["ai", "ml", "model", "neural", "training", "llm", "agent", "embedding"],
    "qa": ["test", "quality", "qa", "coverage", "regression", "e2e"],
}


class TeamComposer:
    """Assembles agent teams dynamically based on task analysis."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        pipeline_registry: PipelineRegistry,
        team_registry: TeamRegistry,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.pipeline_registry = pipeline_registry
        self.team_registry = team_registry
        self.llm_provider = llm_provider

    async def compose_team(
        self,
        task_description: str,
        task_context: dict[str, Any] | None = None,
    ) -> TeamSpec:
        """Compose an optimal team for a task."""
        context = task_context or {}

        # Fast path: explicit team
        if "team_id" in context:
            team = self.team_registry.get_or_none(context["team_id"])
            if team:
                return team

        # Fast path: simple tasks
        complexity = context.get("complexity", "")
        if complexity in ("simple", "medium"):
            return self._compose_simple_team()

        # Capability matching
        matched = self._match_by_capabilities(task_description)

        # LLM refinement for complex tasks
        if self.llm_provider and (len(matched) > 3 or complexity in ("complex", "critical")):
            return await self._compose_with_llm(task_description, context, matched)

        return self._build_team_from_matches(matched, task_description)

    def _compose_simple_team(self) -> TeamSpec:
        return TeamSpec(
            id="team.dynamic_simple",
            name="Simple Task Team",
            pipeline="pipeline.cognitive_os",
            agents=[
                "cognitive.analyst", "cognitive.architect", "cognitive.worker",
                "cognitive.reviewer", "cognitive.committer", "cognitive.reflector",
            ],
        )

    def _match_by_capabilities(self, task_description: str) -> list[AgentSpec]:
        words = task_description.lower().split()
        matched: list[AgentSpec] = []

        for domain, keywords in _CAPABILITY_KEYWORDS.items():
            if any(kw in words for kw in keywords):
                agents = self.agent_registry.find_by_tags([domain])
                matched.extend(agents)

        # Deduplicate
        seen: set[str] = set()
        unique: list[AgentSpec] = []
        for agent in matched:
            if agent.id not in seen:
                seen.add(agent.id)
                unique.append(agent)
        return unique

    async def _compose_with_llm(
        self,
        task_description: str,
        context: dict[str, Any],
        pre_matched: list[AgentSpec],
    ) -> TeamSpec:
        all_agents = self.agent_registry.list_all()
        agents_desc = "\n".join(
            f"- {a.id}: {a.name} (caps: {', '.join(a.capabilities)}, tags: {', '.join(a.tags)})"
            for a in all_agents
            if not a.id.startswith("__system__")
        )

        prompt = TEAM_COMPOSER_PROMPT.format(
            agents_description=agents_desc,
            task_description=task_description,
            task_context=str(context),
        )

        try:
            model = self.llm_provider.get_model_for_agent("composer")
            response = await model.ainvoke([
                {"role": "system", "content": "You are a team composition expert."},
                {"role": "user", "content": prompt},
            ])

            content = response.content if hasattr(response, "content") else str(response)
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(content[start:end])
                return self._team_from_llm_response(data, task_description)
        except Exception as e:
            logger.warning("llm_team_composition_failed", error=str(e))

        return self._build_team_from_matches(pre_matched, task_description)

    def _team_from_llm_response(self, data: dict, task_description: str) -> TeamSpec:
        pairs = [
            PairSpec(agent=p["agent"], critic=p["critic"])
            for p in data.get("selected_pairs", [])
        ]

        pipeline_id = data.get("pipeline", "pipeline.cognitive_os")
        if not self.pipeline_registry.has(pipeline_id):
            pipeline_id = "pipeline.cognitive_os"

        return TeamSpec(
            id=f"team.dynamic_{abs(hash(task_description)) % 10000}",
            name=f"Dynamic Team: {task_description[:50]}",
            pipeline=pipeline_id,
            orchestrator="adversarial.orchestrator" if data.get("needs_orchestrator") else None,
            agents=data.get("selected_agents", []),
            pairs=pairs,
        )

    def _build_team_from_matches(self, matched: list[AgentSpec], task_description: str) -> TeamSpec:
        pairs = []
        agents = []
        for agent in matched:
            if agent.has_critic():
                pairs.append(PairSpec(agent=agent.id, critic=agent.critic.id))
            else:
                agents.append(agent.id)

        pipeline_id = "pipeline.adversarial_team" if pairs else "pipeline.cognitive_os"

        return TeamSpec(
            id=f"team.dynamic_{abs(hash(task_description)) % 10000}",
            name=f"Dynamic Team: {task_description[:50]}",
            pipeline=pipeline_id,
            orchestrator="adversarial.orchestrator" if len(pairs) > 2 else None,
            agents=agents,
            pairs=pairs,
        )
