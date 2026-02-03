"""State management for adversarial agent team."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from .adversarial_config import (
    AgentPairType,
    AgentRole,
    CriticEvaluation,
    PairStatus,
)


class OrchestratorDecision(BaseModel):
    """Initial decision from Orchestrator."""

    task_id: str
    task_summary: str
    selected_pairs: list[AgentPairType]
    execution_order: list[AgentPairType]  # Order of pair execution
    success_criteria: list[str]
    constraints: list[str]
    estimated_complexity: str  # low, medium, high, critical
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True


class AgentOutput(BaseModel):
    """Output from an action agent."""

    agent_role: AgentRole
    iteration: int
    content: dict[str, Any]
    rationale: str
    changes_from_previous: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CriticReview(BaseModel):
    """Review from a critic agent."""

    critic_role: AgentRole
    iteration: int
    evaluation: CriticEvaluation
    decision: str  # APPROVED, REJECTED, REQUEST_REVISION
    detailed_feedback: str
    must_address: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PairResult(BaseModel):
    """Result of agent-critic pair interaction."""

    pair_type: AgentPairType
    agent_role: AgentRole
    critic_role: AgentRole

    # Iteration history
    iterations: list[tuple[AgentOutput, CriticReview]] = Field(default_factory=list)

    # Final status
    status: PairStatus = PairStatus.PENDING
    final_output: Optional[AgentOutput] = None
    final_evaluation: Optional[CriticEvaluation] = None

    # Metrics
    iteration_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def add_iteration(self, agent_output: AgentOutput, critic_review: CriticReview):
        """Add an iteration to the pair result."""
        self.iterations.append((agent_output, critic_review))
        self.iteration_count += 1

    def get_latest_agent_output(self) -> Optional[AgentOutput]:
        """Get the most recent agent output."""
        if self.iterations:
            return self.iterations[-1][0]
        return None

    def get_latest_critic_review(self) -> Optional[CriticReview]:
        """Get the most recent critic review."""
        if self.iterations:
            return self.iterations[-1][1]
        return None

    def is_approved(self) -> bool:
        """Check if pair interaction was approved."""
        return self.status == PairStatus.APPROVED

    def is_escalated(self) -> bool:
        """Check if pair interaction was escalated."""
        return self.status == PairStatus.ESCALATED

    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


class Conflict(BaseModel):
    """Conflict between agent and critic requiring orchestrator resolution."""

    conflict_id: str
    pair_type: AgentPairType
    agent_position: str
    critic_position: str
    iterations_attempted: int
    context: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Resolution
    resolved: bool = False
    orchestrator_decision: Optional[str] = None
    resolution_rationale: Optional[str] = None
    resolved_at: Optional[datetime] = None


class OrchestratorFinalDecision(BaseModel):
    """Final decision from orchestrator after all pairs complete."""

    approved: bool
    rationale: str
    quality_score: float  # 0-10
    all_pairs_passed: bool
    conflicts_resolved: int
    conditions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    artifacts_to_commit: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AdversarialAgentState(BaseModel):
    """Complete state for adversarial agent team."""

    # Core task info
    task_id: str
    original_request: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Orchestrator decisions (IMMUTABLE after set)
    orchestrator_decision: Optional[OrchestratorDecision] = None
    orchestrator_final_decision: Optional[OrchestratorFinalDecision] = None

    # Pair results
    pair_results: dict[AgentPairType, PairResult] = Field(default_factory=dict)

    # Conflicts requiring orchestrator intervention
    conflicts: list[Conflict] = Field(default_factory=list)

    # Current execution state
    current_phase: str = "initialization"  # initialization, planning, security, implementation, qa, finalization
    current_pair: Optional[AgentPairType] = None
    current_iteration: int = 0
    completed_pairs: list[AgentPairType] = Field(default_factory=list)
    failed_pairs: list[AgentPairType] = Field(default_factory=list)

    # Artifacts and outputs
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)

    # Global status
    status: str = "pending"  # pending, in_progress, completed, failed
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def add_message(
        self, agent: AgentRole, content: str, message_type: str = "info"
    ):
        """Add a message to the state."""
        self.messages.append(
            {
                "agent": agent.value,
                "content": content,
                "type": message_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def init_pair_result(self, pair_type: AgentPairType, pair_config):
        """Initialize a pair result."""
        if pair_type not in self.pair_results:
            self.pair_results[pair_type] = PairResult(
                pair_type=pair_type,
                agent_role=pair_config.agent_role,
                critic_role=pair_config.critic_role,
                started_at=datetime.utcnow(),
            )

    def get_pair_result(self, pair_type: AgentPairType) -> Optional[PairResult]:
        """Get result for a specific pair."""
        return self.pair_results.get(pair_type)

    def mark_pair_completed(self, pair_type: AgentPairType, status: PairStatus):
        """Mark a pair as completed with status."""
        if pair_type in self.pair_results:
            self.pair_results[pair_type].status = status
            self.pair_results[pair_type].completed_at = datetime.utcnow()

        if status == PairStatus.APPROVED:
            if pair_type not in self.completed_pairs:
                self.completed_pairs.append(pair_type)
        elif status in [PairStatus.REJECTED, PairStatus.ESCALATED]:
            if pair_type not in self.failed_pairs:
                self.failed_pairs.append(pair_type)

    def add_conflict(
        self,
        pair_type: AgentPairType,
        agent_position: str,
        critic_position: str,
        iterations: int,
        context: dict[str, Any],
    ) -> str:
        """Add a conflict requiring orchestrator resolution."""
        conflict_id = f"conflict_{len(self.conflicts) + 1}"
        conflict = Conflict(
            conflict_id=conflict_id,
            pair_type=pair_type,
            agent_position=agent_position,
            critic_position=critic_position,
            iterations_attempted=iterations,
            context=context,
        )
        self.conflicts.append(conflict)
        return conflict_id

    def resolve_conflict(
        self, conflict_id: str, decision: str, rationale: str
    ):
        """Resolve a conflict with orchestrator's decision."""
        for conflict in self.conflicts:
            if conflict.conflict_id == conflict_id:
                conflict.resolved = True
                conflict.orchestrator_decision = decision
                conflict.resolution_rationale = rationale
                conflict.resolved_at = datetime.utcnow()
                break

    def get_unresolved_conflicts(self) -> list[Conflict]:
        """Get all unresolved conflicts."""
        return [c for c in self.conflicts if not c.resolved]

    def get_completed_pair_count(self) -> int:
        """Get count of completed pairs."""
        return len(self.completed_pairs)

    def get_total_pair_count(self) -> int:
        """Get total count of selected pairs."""
        if self.orchestrator_decision:
            return len(self.orchestrator_decision.selected_pairs)
        return 0

    def all_pairs_complete(self) -> bool:
        """Check if all pairs have completed."""
        if not self.orchestrator_decision:
            return False
        return self.get_completed_pair_count() >= self.get_total_pair_count()

    def get_overall_quality_score(self) -> float:
        """Calculate overall quality score across all pairs."""
        scores = []
        for pair_result in self.pair_results.values():
            if pair_result.final_evaluation:
                scores.append(pair_result.final_evaluation.average_score())

        return sum(scores) / len(scores) if scores else 0.0

    def get_approval_rate(self) -> float:
        """Calculate approval rate (first-try approvals)."""
        if not self.pair_results:
            return 0.0

        first_try_approvals = sum(
            1
            for pr in self.pair_results.values()
            if pr.iteration_count == 1 and pr.is_approved()
        )

        return first_try_approvals / len(self.pair_results)

    def get_average_iterations(self) -> float:
        """Calculate average iterations per pair."""
        if not self.pair_results:
            return 0.0

        total_iterations = sum(pr.iteration_count for pr in self.pair_results.values())
        return total_iterations / len(self.pair_results)

    def get_escalation_rate(self) -> float:
        """Calculate escalation rate."""
        if not self.pair_results:
            return 0.0

        escalations = sum(1 for pr in self.pair_results.values() if pr.is_escalated())
        return escalations / len(self.pair_results)

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_pairs": self.get_total_pair_count(),
            "completed_pairs": self.get_completed_pair_count(),
            "failed_pairs": len(self.failed_pairs),
            "conflicts": len(self.conflicts),
            "unresolved_conflicts": len(self.get_unresolved_conflicts()),
            "overall_quality_score": self.get_overall_quality_score(),
            "approval_rate": self.get_approval_rate(),
            "average_iterations": self.get_average_iterations(),
            "escalation_rate": self.get_escalation_rate(),
        }


# State reducer functions for LangGraph
def merge_messages(existing: list, new: list) -> list:
    """Merge message lists."""
    return existing + new


def merge_artifacts(existing: list, new: list) -> list:
    """Merge artifact lists."""
    return existing + new


def merge_conflicts(existing: list, new: list) -> list:
    """Merge conflict lists."""
    return existing + new


def merge_pair_results(
    existing: dict[AgentPairType, PairResult],
    new: dict[AgentPairType, PairResult],
) -> dict[AgentPairType, PairResult]:
    """Merge pair results dictionaries."""
    merged = existing.copy()
    merged.update(new)
    return merged
