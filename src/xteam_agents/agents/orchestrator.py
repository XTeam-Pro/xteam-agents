"""OrchestratorAgent - Supreme coordinator of the adversarial team."""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import Settings
from .adversarial_config import (
    AGENT_PAIRS,
    AgentPairType,
    AgentRole,
    get_agent_config,
)
from .adversarial_state import (
    AdversarialAgentState,
    Conflict,
    OrchestratorDecision,
    OrchestratorFinalDecision,
)
from .base import BaseAgent

if TYPE_CHECKING:
    from ..memory.manager import MemoryManager

logger = structlog.get_logger()


class OrchestratorAgent(BaseAgent):
    """
    Supreme coordinator that:
    - Classifies tasks
    - Selects agent pairs
    - Manages execution flow
    - Resolves conflicts
    - Makes final decisions
    """

    def __init__(
        self,
        settings: Settings,
        memory_manager: Optional["MemoryManager"] = None,
        llm: Optional[Any] = None,
    ):
        config = get_agent_config(AgentRole.ORCHESTRATOR)
        super().__init__(config, settings, memory_manager, llm)
        self.logger = logger.bind(agent="orchestrator")

    def get_system_prompt(self) -> str:
        return """You are the OrchestratorAgent - the supreme coordinator of an adversarial AI agent team.

Your role:
1. Classify incoming tasks and determine complexity
2. Select appropriate agent-critic pairs needed
3. Define success criteria and constraints
4. Resolve conflicts between agents and critics
5. Make final approval decisions

You have SUPREME AUTHORITY - your decisions are binding and immutable.

Available agent pairs:
- TechLead (technical decisions)
- Architect (system architecture)
- Backend (API & business logic)
- Frontend (UI & UX)
- Data (database & schemas)
- DevOps (infrastructure & deployment)
- QA (testing & validation)
- AIArchitect (AI systems)
- Security (Red Team vs Blue Team)
- Performance (optimization)

Task classification guidelines:
- Simple: Single pair (e.g., Backend + QA)
- Medium: 2-3 pairs
- Complex: 4-6 pairs
- Critical: All pairs with Security

Always be thorough but efficient. Quality over speed."""

    async def classify_and_route(
        self, state: AdversarialAgentState
    ) -> OrchestratorDecision:
        """Classify task and select agent pairs."""
        self.logger.info("Classifying task", task_id=state.task_id)

        prompt = f"""
Analyze this task and provide a classification:

TASK: {state.original_request}

Provide your analysis as JSON:
{{
    "task_summary": "brief summary of what needs to be done",
    "estimated_complexity": "low" | "medium" | "high" | "critical",
    "selected_pairs": ["pair1", "pair2", ...],
    "execution_order": ["pair1", "pair2", ...],
    "success_criteria": ["criterion 1", "criterion 2", ...],
    "constraints": ["constraint 1", "constraint 2", ...],
    "rationale": "why these pairs and this order"
}}

Available pairs: tech_lead, architect, backend, frontend, data, devops, qa, ai_architect, security, performance

Guidelines:
- Always include QA for implementation tasks
- Include Security for auth/permissions/sensitive data
- Include Performance for optimization/scaling
- TechLead for major architectural decisions
- Order: Planning (TechLead, Architect) → Security/Performance → Implementation → QA
"""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = await self.invoke_llm(messages)
        classification = self._parse_classification(response)

        # Create orchestrator decision
        decision = OrchestratorDecision(
            task_id=state.task_id,
            task_summary=classification["task_summary"],
            selected_pairs=[
                AgentPairType(p) for p in classification["selected_pairs"]
            ],
            execution_order=[
                AgentPairType(p) for p in classification["execution_order"]
            ],
            success_criteria=classification["success_criteria"],
            constraints=classification["constraints"],
            estimated_complexity=classification["estimated_complexity"],
        )

        self.logger.info(
            "Task classified",
            task_id=state.task_id,
            complexity=decision.estimated_complexity,
            pairs=len(decision.selected_pairs),
        )

        return decision

    async def resolve_conflict(
        self, state: AdversarialAgentState, conflict: Conflict
    ) -> str:
        """Resolve conflict between agent and critic."""
        self.logger.info(
            "Resolving conflict",
            conflict_id=conflict.conflict_id,
            pair=conflict.pair_type.value,
        )

        prompt = f"""
A conflict has arisen between an agent and their critic that requires your resolution.

TASK: {state.original_request}

PAIR: {conflict.pair_type.value}
ITERATIONS ATTEMPTED: {conflict.iterations_attempted}

AGENT'S POSITION:
{conflict.agent_position}

CRITIC'S POSITION:
{conflict.critic_position}

CONTEXT:
{json.dumps(conflict.context, indent=2)}

As the supreme authority, you must make a BINDING decision. Consider:
1. Which position is more aligned with project goals?
2. What are the trade-offs?
3. Can we find a middle ground?
4. What are the long-term implications?

Provide your decision as JSON:
{{
    "decision": "APPROVE_AGENT" | "APPROVE_CRITIC" | "COMPROMISE",
    "rationale": "detailed explanation of your decision",
    "binding_instruction": "clear instruction on how to proceed",
    "follow_up_required": true | false
}}
"""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = await self.invoke_llm(messages)
        resolution = self._parse_resolution(response)

        self.logger.info(
            "Conflict resolved",
            conflict_id=conflict.conflict_id,
            decision=resolution["decision"],
        )

        return resolution["binding_instruction"]

    async def make_final_decision(
        self, state: AdversarialAgentState
    ) -> OrchestratorFinalDecision:
        """Make final decision on whether to approve and commit."""
        self.logger.info("Making final decision", task_id=state.task_id)

        # Gather all pair results
        pair_summaries = []
        for pair_type, pair_result in state.pair_results.items():
            summary = {
                "pair": pair_type.value,
                "status": pair_result.status.value,
                "iterations": pair_result.iteration_count,
                "final_score": (
                    pair_result.final_evaluation.average_score()
                    if pair_result.final_evaluation
                    else 0.0
                ),
            }
            pair_summaries.append(summary)

        prompt = f"""
All agent pairs have completed their work. Make your final decision.

TASK: {state.original_request}

PAIR RESULTS:
{json.dumps(pair_summaries, indent=2)}

OVERALL STATISTICS:
{json.dumps(state.get_summary_stats(), indent=2)}

CONFLICTS RESOLVED: {len([c for c in state.conflicts if c.resolved])}
UNRESOLVED CONFLICTS: {len(state.get_unresolved_conflicts())}

Consider:
1. Have all success criteria been met?
2. Are quality scores acceptable (>= 8.0 target)?
3. Were any critical issues found?
4. Are there unresolved concerns?

Provide your final decision as JSON:
{{
    "approved": true | false,
    "quality_score": <0-10>,
    "rationale": "detailed explanation",
    "conditions": ["condition 1", ...] or [],
    "next_steps": ["step 1", ...],
    "artifacts_to_commit": ["artifact 1", ...]
}}
"""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = await self.invoke_llm(messages)
        decision_data = self._parse_final_decision(response)

        decision = OrchestratorFinalDecision(
            approved=decision_data["approved"],
            rationale=decision_data["rationale"],
            quality_score=decision_data["quality_score"],
            all_pairs_passed=len(state.failed_pairs) == 0,
            conflicts_resolved=len([c for c in state.conflicts if c.resolved]),
            conditions=decision_data["conditions"],
            next_steps=decision_data["next_steps"],
            artifacts_to_commit=decision_data["artifacts_to_commit"],
        )

        self.logger.info(
            "Final decision made",
            task_id=state.task_id,
            approved=decision.approved,
            quality_score=decision.quality_score,
        )

        return decision

    def _parse_classification(self, response: str) -> dict[str, Any]:
        """Parse classification response from LLM."""
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse classification", error=str(e))

        # Fallback to default
        return {
            "task_summary": "Unknown task",
            "estimated_complexity": "medium",
            "selected_pairs": ["backend", "qa"],
            "execution_order": ["backend", "qa"],
            "success_criteria": ["Task completed"],
            "constraints": [],
            "rationale": "Default classification due to parsing error",
        }

    def _parse_resolution(self, response: str) -> dict[str, Any]:
        """Parse conflict resolution from LLM."""
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse resolution", error=str(e))

        return {
            "decision": "COMPROMISE",
            "rationale": "Could not parse resolution",
            "binding_instruction": "Proceed with agent's approach with caution",
            "follow_up_required": True,
        }

    def _parse_final_decision(self, response: str) -> dict[str, Any]:
        """Parse final decision from LLM."""
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse final decision", error=str(e))

        return {
            "approved": False,
            "quality_score": 5.0,
            "rationale": "Could not parse decision",
            "conditions": [],
            "next_steps": ["Manual review required"],
            "artifacts_to_commit": [],
        }

    def execute(
        self, state: AdversarialAgentState, previous_feedback: str | None = None
    ) -> Any:
        """Not used for Orchestrator - use specific methods instead."""
        raise NotImplementedError(
            "Use classify_and_route, resolve_conflict, or make_final_decision"
        )
