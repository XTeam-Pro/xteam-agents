"""Agent team package."""

# Import adversarial agent components
from .adversarial_config import (
    AGENT_CONFIGS,
    AGENT_PAIRS,
    AgentConfig,
    AgentPairConfig,
    AgentPairType,
    AgentRole,
    CriticEvaluation,
    CriticStrategy,
    PairStatus,
    get_agent_config,
    get_pair_config,
)
from .adversarial_state import (
    AdversarialAgentState,
    AgentOutput,
    Conflict,
    CriticReview,
    OrchestratorDecision,
    OrchestratorFinalDecision,
    PairResult,
    merge_artifacts,
    merge_conflicts,
    merge_messages,
    merge_pair_results,
)
from .base import BaseAgent, BaseCritic
from .orchestrator import OrchestratorAgent
from .pair_manager import PairRegistry

__all__ = [
    # Config
    "AgentRole",
    "AgentConfig",
    "AGENT_CONFIGS",
    "AgentPairType",
    "AgentPairConfig",
    "AGENT_PAIRS",
    "PairStatus",
    "CriticStrategy",
    "CriticEvaluation",
    "get_agent_config",
    "get_pair_config",
    # State
    "AdversarialAgentState",
    "OrchestratorDecision",
    "OrchestratorFinalDecision",
    "AgentOutput",
    "CriticReview",
    "PairResult",
    "Conflict",
    "merge_messages",
    "merge_artifacts",
    "merge_conflicts",
    "merge_pair_results",
    # Base classes
    "BaseAgent",
    "BaseCritic",
    "OrchestratorAgent",
    "PairRegistry",
]
