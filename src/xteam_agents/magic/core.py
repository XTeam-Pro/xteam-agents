"""MAGICCore - Central coordinator for the MAGIC system."""

from typing import Any
from uuid import UUID

import structlog

from xteam_agents.llm.provider import LLMProvider
from xteam_agents.magic.escalation import EscalationRouter
from xteam_agents.magic.evolution import EvolutionEngine
from xteam_agents.magic.feedback import FeedbackCollector
from xteam_agents.magic.metacognition import MetacognitionEngine
from xteam_agents.magic.session import SessionManager
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.models.magic import (
    CheckpointStage,
    ConfidenceScore,
    EscalationRequest,
    EvolutionMetric,
    HumanFeedback,
    HumanResponse,
    HumanResponseType,
)
from xteam_agents.models.memory import MemoryArtifact
from xteam_agents.models.state import AgentState

logger = structlog.get_logger()


class MAGICCore:
    """Central coordinator for the MAGIC human-AI collaboration system.

    Holds instances of all MAGIC subsystems and provides a unified interface.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        memory_manager: MemoryManager,
    ):
        self.metacognition = MetacognitionEngine(llm_provider, memory_manager)
        self.escalation_router = EscalationRouter()
        self.feedback_collector = FeedbackCollector(memory_manager)
        self.session_manager = SessionManager()
        self.evolution_engine = EvolutionEngine()

        self._llm_provider = llm_provider
        self._memory_manager = memory_manager

    # --- Confidence Assessment ---

    async def assess_confidence(
        self,
        task_id: str,
        node_name: str,
        node_output: str,
        task_description: str,
        context: str = "",
    ) -> ConfidenceScore:
        """Assess confidence in a pipeline output. Delegates to metacognition."""
        return await self.metacognition.assess_confidence(
            task_id, node_name, node_output, task_description, context
        )

    # --- Escalation ---

    def create_escalation(
        self,
        state: AgentState,
        confidence: ConfidenceScore | None,
        stage: CheckpointStage,
    ) -> EscalationRequest | None:
        """Create an escalation if needed. Returns None if no escalation needed."""
        request = self.escalation_router.should_escalate(state, confidence, stage)
        if request:
            # Record escalation in evolution tracking
            self.evolution_engine.record_escalation()

            # Ensure a session exists
            session = self.session_manager.create_session(
                state.task_id,
                state.magic_config.human_id if state.magic_config else "default",
            )

            # Add escalation to session
            session.pending_escalations.append(request.id)
            self.session_manager.add_message(
                session.id,
                "system",
                f"Escalation created: {request.question}",
            )

        return request

    # --- Response Handling ---

    async def wait_for_response(
        self, escalation_id: UUID, timeout: int = 300
    ) -> HumanResponse | None:
        """Wait for a human response to an escalation."""
        return await self.session_manager.wait_for_response(
            escalation_id, timeout
        )

    async def submit_response(
        self, escalation_id: UUID, response: HumanResponse, task_id: UUID
    ) -> None:
        """Submit a human response and process feedback."""
        # Submit to session (signals waiting coroutine)
        self.session_manager.submit_response(escalation_id, response)

        # Resolve the escalation
        self.escalation_router.resolve_escalation(escalation_id)
        self.evolution_engine.record_escalation(resolved=True)

        # Convert to feedback for learning
        feedback = self.feedback_collector.convert_response_to_feedback(
            response, task_id
        )
        await self.feedback_collector.record_feedback(feedback)

    def process_human_response(
        self, state: AgentState, response: HumanResponse
    ) -> dict[str, Any]:
        """Process a human response and produce state updates.

        Maps response types to state changes:
        - APPROVAL -> continue
        - REJECTION -> replan
        - MODIFICATION -> update description/analysis/plan
        - GUIDANCE -> add to context
        - OVERRIDE -> force state change
        - DEFERRAL -> continue with defaults
        """
        updates: dict[str, Any] = {
            "is_human_paused": False,
            "pending_escalation": None,
        }

        rt = response.response_type

        if rt == HumanResponseType.APPROVAL:
            # Track first-pass approval
            self.evolution_engine.record_validation(first_pass_approved=True)

        elif rt == HumanResponseType.REJECTION:
            updates["should_replan"] = True
            updates["validation_feedback"] = (
                response.content or "Rejected by human reviewer"
            )
            self.evolution_engine.record_validation(first_pass_approved=False)

        elif rt == HumanResponseType.MODIFICATION:
            # Apply modifications from response data
            if response.data.get("analysis"):
                updates["analysis"] = response.data["analysis"]
            if response.data.get("plan"):
                updates["plan"] = response.data["plan"]
            if response.data.get("description"):
                updates["description"] = response.data["description"]

        elif rt == HumanResponseType.GUIDANCE:
            # Add guidance to context
            current_context = dict(state.context)
            guidance_list = current_context.get("human_guidance", [])
            guidance_list.append(response.content)
            current_context["human_guidance"] = guidance_list
            updates["context"] = current_context

        elif rt == HumanResponseType.OVERRIDE:
            # Apply override from response data
            updates["human_override"] = response.content
            if response.data.get("execution_result"):
                updates["execution_result"] = response.data["execution_result"]
            if response.data.get("is_validated") is not None:
                updates["is_validated"] = response.data["is_validated"]

        elif rt == HumanResponseType.DEFERRAL:
            # Continue with defaults, no changes needed
            pass

        return updates

    # --- Guidelines ---

    def get_pending_guidelines(self) -> list[MemoryArtifact]:
        """Get pending guidelines for commit_node to write."""
        return self.feedback_collector.get_pending_guidelines()

    # --- Evolution ---

    def compute_metrics(self, period_days: int = 7) -> list[EvolutionMetric]:
        """Compute evolution metrics."""
        return self.evolution_engine.compute_metrics(period_days)

    def get_improvement_proposals(self) -> list[dict]:
        """Get improvement proposals."""
        return self.evolution_engine.generate_improvement_proposals()
