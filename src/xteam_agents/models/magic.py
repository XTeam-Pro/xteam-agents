"""MAGIC (Metacognitive Awareness, Adaptive Learning, Generative Collaboration,
Intelligent Escalation, Continuous Evolution) system models."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# --- Enums ---

class ConfidenceLevel(str, Enum):
    """Confidence level thresholds."""
    HIGH = "high"          # >= 0.8
    MEDIUM = "medium"      # >= 0.6
    LOW = "low"            # >= 0.4
    VERY_LOW = "very_low"  # < 0.4


class EscalationReason(str, Enum):
    """Reasons for escalating to a human."""
    LOW_CONFIDENCE = "low_confidence"
    EXPLICIT_CHECKPOINT = "explicit_checkpoint"
    VALIDATION_FAILURE = "validation_failure"
    HIGH_RISK_TASK = "high_risk_task"
    AMBIGUOUS_REQUIREMENTS = "ambiguous_requirements"
    KNOWLEDGE_GAP = "knowledge_gap"
    POLICY_REQUIRED = "policy_required"


class EscalationPriority(str, Enum):
    """Priority levels for escalation requests."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HumanResponseType(str, Enum):
    """Types of human responses to escalations."""
    APPROVAL = "approval"
    REJECTION = "rejection"
    MODIFICATION = "modification"
    GUIDANCE = "guidance"
    OVERRIDE = "override"
    DEFERRAL = "deferral"


class FeedbackType(str, Enum):
    """Types of human feedback."""
    CORRECTION = "correction"
    PREFERENCE = "preference"
    GUIDELINE = "guideline"
    RATING = "rating"
    COMMENT = "comment"


class SessionStatus(str, Enum):
    """Status of a collaborative session."""
    ACTIVE = "active"
    WAITING = "waiting"
    PAUSED = "paused"
    CLOSED = "closed"
    EXPIRED = "expired"


class CheckpointStage(str, Enum):
    """Pipeline stages where checkpoints can be placed."""
    AFTER_ANALYZE = "after_analyze"
    AFTER_PLAN = "after_plan"
    AFTER_EXECUTE = "after_execute"
    AFTER_VALIDATE = "after_validate"


class AutonomyLevel(str, Enum):
    """Levels of system autonomy."""
    SUPERVISED = "supervised"      # Human reviews every step
    GUIDED = "guided"              # Human reviews analysis + validation
    COLLABORATIVE = "collaborative"  # Human reviews on low confidence
    AUTONOMOUS = "autonomous"      # Human only on failures
    TRUSTED = "trusted"            # No human involvement


# --- Core Models ---

class ConfidenceScore(BaseModel):
    """Multi-dimensional confidence assessment."""

    overall: float = Field(ge=0.0, le=1.0)
    factual_accuracy: float = Field(default=0.5, ge=0.0, le=1.0)
    completeness: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    coherence: float = Field(default=0.5, ge=0.0, le=1.0)
    novelty_risk: float = Field(default=0.5, ge=0.0, le=1.0)

    uncertainty_factors: list[str] = Field(default_factory=list)
    knowledge_gaps: list[str] = Field(default_factory=list)

    node_name: str = ""
    assessed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def level(self) -> ConfidenceLevel:
        if self.overall >= 0.8:
            return ConfidenceLevel.HIGH
        elif self.overall >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif self.overall >= 0.4:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.VERY_LOW

    def should_escalate(self, threshold: float = 0.6) -> bool:
        """Check if confidence is below the escalation threshold."""
        return self.overall < threshold

    @classmethod
    def from_score(cls, score: float, node_name: str = "") -> "ConfidenceScore":
        """Create a ConfidenceScore from a single overall score."""
        return cls(
            overall=score,
            factual_accuracy=score,
            completeness=score,
            relevance=score,
            coherence=score,
            novelty_risk=1.0 - score,
            node_name=node_name,
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class EscalationRequest(BaseModel):
    """A request for human intervention."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    session_id: UUID | None = None

    reason: EscalationReason
    priority: EscalationPriority = EscalationPriority.MEDIUM
    stage: CheckpointStage

    question: str
    context: str = ""
    options: list[str] = Field(default_factory=list)
    default_action: str | None = None

    confidence_score: ConfidenceScore | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    is_resolved: bool = False
    timeout_seconds: int = 300


class HumanResponse(BaseModel):
    """A human's response to an escalation."""

    escalation_id: UUID
    response_type: HumanResponseType
    content: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    human_id: str = "default"
    responded_at: datetime = Field(default_factory=datetime.utcnow)


class HumanFeedback(BaseModel):
    """Human feedback on system output."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    feedback_type: FeedbackType
    content: str
    target_node: str | None = None
    rating: float | None = Field(default=None, ge=0.0, le=1.0)
    should_persist: bool = False
    applies_to: str | None = None  # domain/category
    human_id: str = "default"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollaborativeSession(BaseModel):
    """A collaborative session between human and AI."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    human_id: str = "default"
    status: SessionStatus = SessionStatus.ACTIVE

    messages: list[dict[str, str]] = Field(default_factory=list)
    pending_escalations: list[UUID] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=4)
    )

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.updated_at = datetime.utcnow()


class MAGICTaskConfig(BaseModel):
    """Per-task MAGIC configuration."""

    enabled: bool = True
    autonomy_level: AutonomyLevel = AutonomyLevel.COLLABORATIVE
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    checkpoints: list[CheckpointStage] = Field(default_factory=list)
    escalation_timeout: int = 300
    fallback_on_timeout: str = "continue"  # continue, pause, fail
    human_id: str = "default"


# --- Learning Models ---

class EvolutionMetric(BaseModel):
    """A metric tracking system evolution."""

    name: str
    value: float
    period_days: int = 7
    trend: str = "stable"  # improving, declining, stable
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class HumanPreferenceProfile(BaseModel):
    """Learned preferences for a human collaborator."""

    human_id: str
    preferred_autonomy: AutonomyLevel = AutonomyLevel.COLLABORATIVE
    approval_rate: float = 0.0
    total_interactions: int = 0
    feedback_count: int = 0
    domains: dict[str, float] = Field(default_factory=dict)  # domain -> approval_rate
    updated_at: datetime = Field(default_factory=datetime.utcnow)
