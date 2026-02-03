"""LangGraph for adversarial agent team orchestration."""

from typing import TYPE_CHECKING, Any, Literal, Optional

import structlog
from langgraph.graph import END, StateGraph

from ..config import Settings
from .adversarial_config import AGENT_PAIRS, AgentPairType, get_pair_config
from .adversarial_state import AdversarialAgentState, PairStatus

if TYPE_CHECKING:
    from ..memory.manager import MemoryManager
from .nodes.pairs import (
    AIAgentArchitect,
    AIArchitectCritic,
    ArchitectAgent,
    ArchitectCritic,
    BackendAgent,
    BackendCritic,
    DataAgent,
    DataCritic,
    DevOpsAgent,
    DevOpsCritic,
    FrontendAgent,
    FrontendCritic,
    PerformanceAgent,
    PerformanceCritic,
    QAAgent,
    QACritic,
    SecurityAgent,
    SecurityCritic,
    TechLeadAgent,
    TechLeadCritic,
)
from .orchestrator import OrchestratorAgent
from .pair_manager import PairRegistry

logger = structlog.get_logger()


class AdversarialGraphBuilder:
    """Builds the LangGraph for adversarial agent team."""

    def __init__(
        self,
        settings: Settings,
        memory_manager: Optional["MemoryManager"] = None,
        llm: Optional[Any] = None,
    ):
        self.settings = settings
        self.memory_manager = memory_manager
        self.llm = llm
        self.logger = logger.bind(component="AdversarialGraph")

        # Initialize orchestrator
        self.orchestrator = OrchestratorAgent(settings, memory_manager, llm)

        # Initialize pair registry
        self.pair_registry = PairRegistry(settings)

        # Register all agent pairs
        self._register_all_pairs()

    def _register_all_pairs(self):
        """Register all agent pairs."""
        # TechLead pair
        tech_lead_config = get_pair_config(AgentPairType.TECH_LEAD)
        self.pair_registry.register_pair(
            tech_lead_config,
            TechLeadAgent(self.settings, self.memory_manager, self.llm),
            TechLeadCritic(self.settings, self.memory_manager, self.llm),
        )

        # Architect pair
        architect_config = get_pair_config(AgentPairType.ARCHITECT)
        self.pair_registry.register_pair(
            architect_config,
            ArchitectAgent(self.settings, self.memory_manager, self.llm),
            ArchitectCritic(self.settings, self.memory_manager, self.llm),
        )

        # Backend pair
        backend_config = get_pair_config(AgentPairType.BACKEND)
        self.pair_registry.register_pair(
            backend_config,
            BackendAgent(self.settings, self.memory_manager, self.llm),
            BackendCritic(self.settings, self.memory_manager, self.llm),
        )

        # Frontend pair
        frontend_config = get_pair_config(AgentPairType.FRONTEND)
        self.pair_registry.register_pair(
            frontend_config,
            FrontendAgent(self.settings, self.memory_manager, self.llm),
            FrontendCritic(self.settings, self.memory_manager, self.llm),
        )

        # Data pair
        data_config = get_pair_config(AgentPairType.DATA)
        self.pair_registry.register_pair(
            data_config,
            DataAgent(self.settings, self.memory_manager, self.llm),
            DataCritic(self.settings, self.memory_manager, self.llm),
        )

        # DevOps pair
        devops_config = get_pair_config(AgentPairType.DEVOPS)
        self.pair_registry.register_pair(
            devops_config,
            DevOpsAgent(self.settings, self.memory_manager, self.llm),
            DevOpsCritic(self.settings, self.memory_manager, self.llm),
        )

        # QA pair
        qa_config = get_pair_config(AgentPairType.QA)
        self.pair_registry.register_pair(
            qa_config,
            QAAgent(self.settings, self.memory_manager, self.llm),
            QACritic(self.settings, self.memory_manager, self.llm),
        )

        # AI Architect pair
        ai_architect_config = get_pair_config(AgentPairType.AI_ARCHITECT)
        self.pair_registry.register_pair(
            ai_architect_config,
            AIAgentArchitect(self.settings, self.memory_manager, self.llm),
            AIArchitectCritic(self.settings, self.memory_manager, self.llm),
        )

        # Security pair (Blue Team vs Red Team)
        security_config = get_pair_config(AgentPairType.SECURITY)
        self.pair_registry.register_pair(
            security_config,
            SecurityAgent(self.settings, self.memory_manager, self.llm),
            SecurityCritic(self.settings, self.memory_manager, self.llm),
        )

        # Performance pair
        performance_config = get_pair_config(AgentPairType.PERFORMANCE)
        self.pair_registry.register_pair(
            performance_config,
            PerformanceAgent(self.settings, self.memory_manager, self.llm),
            PerformanceCritic(self.settings, self.memory_manager, self.llm),
        )

    def build(self) -> StateGraph:
        """Build the complete adversarial graph."""
        # Create state graph
        graph = StateGraph(AdversarialAgentState)

        # Add nodes
        graph.add_node("orchestrator_classify", self._orchestrator_classify_node)
        graph.add_node("execute_pairs", self._execute_pairs_node)
        graph.add_node("resolve_conflicts", self._resolve_conflicts_node)
        graph.add_node("orchestrator_finalize", self._orchestrator_finalize_node)
        graph.add_node("fail", self._fail_node)

        # Add edges
        graph.set_entry_point("orchestrator_classify")

        # After classification → execute pairs
        graph.add_edge("orchestrator_classify", "execute_pairs")

        # After pairs → check for conflicts
        graph.add_conditional_edges(
            "execute_pairs",
            self._route_after_pairs,
            {
                "conflicts": "resolve_conflicts",
                "finalize": "orchestrator_finalize",
                "fail": "fail",
            },
        )

        # After conflict resolution → back to pairs or finalize
        graph.add_conditional_edges(
            "resolve_conflicts",
            self._route_after_conflicts,
            {
                "retry_pairs": "execute_pairs",
                "finalize": "orchestrator_finalize",
            },
        )

        # After finalization → end
        graph.add_edge("orchestrator_finalize", END)
        graph.add_edge("fail", END)

        return graph.compile()

    async def _orchestrator_classify_node(
        self, state: AdversarialAgentState
    ) -> dict:
        """Orchestrator classifies task and selects pairs."""
        self.logger.info("Orchestrator classifying", task_id=state.task_id)

        decision = await self.orchestrator.classify_and_route(state)

        return {
            "orchestrator_decision": decision,
            "current_phase": "execution",
        }

    async def _execute_pairs_node(self, state: AdversarialAgentState) -> dict:
        """Execute all selected agent pairs."""
        self.logger.info("Executing pairs", task_id=state.task_id)

        if not state.orchestrator_decision:
            return {"status": "failed", "error": "No orchestrator decision"}

        # Execute pairs in order
        for pair_type in state.orchestrator_decision.execution_order:
            self.logger.info("Executing pair", pair=pair_type.value)

            try:
                pair_result = await self.pair_registry.execute_pair(
                    pair_type.value, state
                )

                # Update state
                state.pair_results[pair_type] = pair_result

                if pair_result.status == PairStatus.APPROVED:
                    state.mark_pair_completed(pair_type, PairStatus.APPROVED)
                elif pair_result.status == PairStatus.ESCALATED:
                    state.mark_pair_completed(pair_type, PairStatus.ESCALATED)
                else:
                    state.mark_pair_completed(pair_type, PairStatus.REJECTED)

            except Exception as e:
                self.logger.error("Pair execution failed", pair=pair_type.value, error=str(e))
                state.mark_pair_completed(pair_type, PairStatus.REJECTED)

        return {
            "pair_results": state.pair_results,
            "current_phase": "review",
        }

    async def _resolve_conflicts_node(self, state: AdversarialAgentState) -> dict:
        """Orchestrator resolves conflicts."""
        self.logger.info("Resolving conflicts", task_id=state.task_id)

        unresolved = state.get_unresolved_conflicts()

        for conflict in unresolved:
            resolution = await self.orchestrator.resolve_conflict(state, conflict)
            state.resolve_conflict(conflict.conflict_id, resolution, resolution)

        return {
            "conflicts": state.conflicts,
            "current_phase": "finalization",
        }

    async def _orchestrator_finalize_node(
        self, state: AdversarialAgentState
    ) -> dict:
        """Orchestrator makes final decision."""
        self.logger.info("Orchestrator finalizing", task_id=state.task_id)

        final_decision = await self.orchestrator.make_final_decision(state)

        return {
            "orchestrator_final_decision": final_decision,
            "status": "completed" if final_decision.approved else "rejected",
        }

    def _fail_node(self, state: AdversarialAgentState) -> dict:
        """Handle failure."""
        self.logger.error("Task failed", task_id=state.task_id)
        return {"status": "failed"}

    def _route_after_pairs(
        self, state: AdversarialAgentState
    ) -> Literal["conflicts", "finalize", "fail"]:
        """Route after pair execution."""
        # Check for failures
        if len(state.failed_pairs) > len(state.completed_pairs):
            return "fail"

        # Check for conflicts
        if state.get_unresolved_conflicts():
            return "conflicts"

        # All good → finalize
        return "finalize"

    def _route_after_conflicts(
        self, state: AdversarialAgentState
    ) -> Literal["retry_pairs", "finalize"]:
        """Route after conflict resolution."""
        # For now, always go to finalize after resolving conflicts
        # In a more sophisticated version, we might retry pairs
        return "finalize"


def create_adversarial_graph(
    settings: Settings,
    memory_manager: Optional["MemoryManager"] = None,
    llm: Optional[Any] = None,
) -> StateGraph:
    """Create and return the adversarial graph."""
    builder = AdversarialGraphBuilder(settings, memory_manager, llm)
    return builder.build()
