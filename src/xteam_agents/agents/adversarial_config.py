"""Adversarial agent team configuration with Agent-Critic pairs."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent roles in adversarial team."""

    # Orchestrator
    ORCHESTRATOR = "orchestrator"

    # Action Agents (propose solutions)
    TECH_LEAD = "tech_lead"
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATA = "data"
    DEVOPS = "devops"
    QA = "qa"
    AI_ARCHITECT = "ai_architect"
    SECURITY = "security"  # Blue team
    PERFORMANCE = "performance"

    # Critic Agents (challenge and improve)
    TECH_LEAD_CRITIC = "tech_lead_critic"
    ARCHITECT_CRITIC = "architect_critic"
    BACKEND_CRITIC = "backend_critic"
    FRONTEND_CRITIC = "frontend_critic"
    DATA_CRITIC = "data_critic"
    DEVOPS_CRITIC = "devops_critic"
    QA_CRITIC = "qa_critic"
    AI_ARCHITECT_CRITIC = "ai_architect_critic"
    SECURITY_CRITIC = "security_critic"  # Red team
    PERFORMANCE_CRITIC = "performance_critic"


class CriticStrategy(str, Enum):
    """Critic evaluation strategies."""

    CONSTRUCTIVE = "constructive"  # Collaborative improvement
    ADVERSARIAL = "adversarial"  # Actively tries to break
    PERFECTIONIST = "perfectionist"  # Extremely high standards


class AgentPairType(str, Enum):
    """Types of agent pairs."""

    TECH_LEAD = "tech_lead"
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATA = "data"
    DEVOPS = "devops"
    QA = "qa"
    AI_ARCHITECT = "ai_architect"
    SECURITY = "security"
    PERFORMANCE = "performance"


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    role: AgentRole
    name: str
    description: str
    model: str = "claude-sonnet-4-5"
    temperature: float = 0.5
    max_tokens: int = 4096
    is_critic: bool = False
    critic_strategy: Optional[CriticStrategy] = None
    can_escalate: bool = True

    class Config:
        frozen = True


class AgentPairConfig(BaseModel):
    """Configuration for an agent-critic pair."""

    pair_type: AgentPairType
    agent_role: AgentRole
    critic_role: AgentRole
    max_iterations: int = 3
    approval_threshold: float = 7.0  # Average score >= 7.0
    min_score_threshold: float = 5.0  # No dimension < 5.0

    class Config:
        frozen = True


# Agent Configurations
AGENT_CONFIGS = {
    # Orchestrator
    AgentRole.ORCHESTRATOR: AgentConfig(
        role=AgentRole.ORCHESTRATOR,
        name="OrchestratorAgent",
        description="Master coordinator and final decision maker",
        model="claude-opus-4-5",
        temperature=0.3,
        can_escalate=False,  # Supreme authority
    ),
    # TechLead Pair
    AgentRole.TECH_LEAD: AgentConfig(
        role=AgentRole.TECH_LEAD,
        name="TechLeadAgent",
        description="Technical decisions and architecture framing",
        model="claude-opus-4-5",
        temperature=0.3,
    ),
    AgentRole.TECH_LEAD_CRITIC: AgentConfig(
        role=AgentRole.TECH_LEAD_CRITIC,
        name="TechLeadCritic",
        description="Challenges technical decisions and finds alternatives",
        model="claude-opus-4-5",
        temperature=0.7,
        is_critic=True,
        critic_strategy=CriticStrategy.CONSTRUCTIVE,
    ),
    # Architect Pair
    AgentRole.ARCHITECT: AgentConfig(
        role=AgentRole.ARCHITECT,
        name="ArchitectAgent",
        description="System architecture design and boundaries",
        model="claude-sonnet-4-5",
        temperature=0.5,
    ),
    AgentRole.ARCHITECT_CRITIC: AgentConfig(
        role=AgentRole.ARCHITECT_CRITIC,
        name="ArchitectCritic",
        description="Stress-tests architecture and finds failure modes",
        model="claude-sonnet-4-5",
        temperature=0.8,
        is_critic=True,
        critic_strategy=CriticStrategy.CONSTRUCTIVE,
    ),
    # Backend Pair
    AgentRole.BACKEND: AgentConfig(
        role=AgentRole.BACKEND,
        name="BackendAgent",
        description="Business logic and API implementation",
        model="claude-sonnet-4-5",
        temperature=0.2,
    ),
    AgentRole.BACKEND_CRITIC: AgentConfig(
        role=AgentRole.BACKEND_CRITIC,
        name="BackendCritic",
        description="Code review and logic validation",
        model="claude-sonnet-4-5",
        temperature=0.6,
        is_critic=True,
        critic_strategy=CriticStrategy.CONSTRUCTIVE,
    ),
    # Frontend Pair
    AgentRole.FRONTEND: AgentConfig(
        role=AgentRole.FRONTEND,
        name="FrontendAgent",
        description="User interface and client logic",
        model="claude-sonnet-4-5",
        temperature=0.4,
    ),
    AgentRole.FRONTEND_CRITIC: AgentConfig(
        role=AgentRole.FRONTEND_CRITIC,
        name="FrontendCritic",
        description="UX validation and accessibility audit",
        model="claude-sonnet-4-5",
        temperature=0.7,
        is_critic=True,
        critic_strategy=CriticStrategy.CONSTRUCTIVE,
    ),
    # Data Pair
    AgentRole.DATA: AgentConfig(
        role=AgentRole.DATA,
        name="DataAgent",
        description="Data architecture and optimization",
        model="claude-sonnet-4-5",
        temperature=0.2,
    ),
    AgentRole.DATA_CRITIC: AgentConfig(
        role=AgentRole.DATA_CRITIC,
        name="DataCritic",
        description="Data integrity and performance validation",
        model="claude-sonnet-4-5",
        temperature=0.6,
        is_critic=True,
        critic_strategy=CriticStrategy.CONSTRUCTIVE,
    ),
    # DevOps Pair
    AgentRole.DEVOPS: AgentConfig(
        role=AgentRole.DEVOPS,
        name="DevOpsAgent",
        description="Operations and infrastructure",
        model="claude-sonnet-4-5",
        temperature=0.3,
    ),
    AgentRole.DEVOPS_CRITIC: AgentConfig(
        role=AgentRole.DEVOPS_CRITIC,
        name="DevOpsCritic",
        description="Infrastructure resilience testing",
        model="claude-sonnet-4-5",
        temperature=0.7,
        is_critic=True,
        critic_strategy=CriticStrategy.CONSTRUCTIVE,
    ),
    # QA Pair
    AgentRole.QA: AgentConfig(
        role=AgentRole.QA,
        name="QAAgent",
        description="Quality assurance and testing",
        model="claude-sonnet-4-5",
        temperature=0.1,
    ),
    AgentRole.QA_CRITIC: AgentConfig(
        role=AgentRole.QA_CRITIC,
        name="QACritic",
        description="Test coverage and edge case hunter",
        model="claude-sonnet-4-5",
        temperature=0.8,
        is_critic=True,
        critic_strategy=CriticStrategy.PERFECTIONIST,
    ),
    # AI Architect Pair
    AgentRole.AI_ARCHITECT: AgentConfig(
        role=AgentRole.AI_ARCHITECT,
        name="AIAgentArchitect",
        description="AI systems architecture",
        model="claude-opus-4-5",
        temperature=0.5,
    ),
    AgentRole.AI_ARCHITECT_CRITIC: AgentConfig(
        role=AgentRole.AI_ARCHITECT_CRITIC,
        name="AIArchitectCritic",
        description="AI safety and ethics validation",
        model="claude-opus-4-5",
        temperature=0.7,
        is_critic=True,
        critic_strategy=CriticStrategy.CONSTRUCTIVE,
    ),
    # Security Pair (Blue Team / Red Team)
    AgentRole.SECURITY: AgentConfig(
        role=AgentRole.SECURITY,
        name="SecurityAgent",
        description="Defensive security (Blue Team)",
        model="claude-opus-4-5",
        temperature=0.1,
    ),
    AgentRole.SECURITY_CRITIC: AgentConfig(
        role=AgentRole.SECURITY_CRITIC,
        name="SecurityCritic",
        description="Offensive security (Red Team) - attacker mindset",
        model="claude-opus-4-5",
        temperature=0.9,  # Very creative for finding vulnerabilities
        is_critic=True,
        critic_strategy=CriticStrategy.ADVERSARIAL,
    ),
    # Performance Pair
    AgentRole.PERFORMANCE: AgentConfig(
        role=AgentRole.PERFORMANCE,
        name="PerformanceAgent",
        description="Performance optimization",
        model="claude-sonnet-4-5",
        temperature=0.3,
    ),
    AgentRole.PERFORMANCE_CRITIC: AgentConfig(
        role=AgentRole.PERFORMANCE_CRITIC,
        name="PerformanceCritic",
        description="Stress testing and bottleneck hunting",
        model="claude-sonnet-4-5",
        temperature=0.7,
        is_critic=True,
        critic_strategy=CriticStrategy.PERFECTIONIST,
    ),
}

# Agent Pair Configurations
AGENT_PAIRS = {
    AgentPairType.TECH_LEAD: AgentPairConfig(
        pair_type=AgentPairType.TECH_LEAD,
        agent_role=AgentRole.TECH_LEAD,
        critic_role=AgentRole.TECH_LEAD_CRITIC,
        max_iterations=3,
        approval_threshold=8.0,  # Higher bar for tech decisions
    ),
    AgentPairType.ARCHITECT: AgentPairConfig(
        pair_type=AgentPairType.ARCHITECT,
        agent_role=AgentRole.ARCHITECT,
        critic_role=AgentRole.ARCHITECT_CRITIC,
        max_iterations=3,
        approval_threshold=8.0,
    ),
    AgentPairType.BACKEND: AgentPairConfig(
        pair_type=AgentPairType.BACKEND,
        agent_role=AgentRole.BACKEND,
        critic_role=AgentRole.BACKEND_CRITIC,
        max_iterations=3,
        approval_threshold=7.0,
    ),
    AgentPairType.FRONTEND: AgentPairConfig(
        pair_type=AgentPairType.FRONTEND,
        agent_role=AgentRole.FRONTEND,
        critic_role=AgentRole.FRONTEND_CRITIC,
        max_iterations=3,
        approval_threshold=7.0,
    ),
    AgentPairType.DATA: AgentPairConfig(
        pair_type=AgentPairType.DATA,
        agent_role=AgentRole.DATA,
        critic_role=AgentRole.DATA_CRITIC,
        max_iterations=3,
        approval_threshold=7.5,  # Data quality is critical
    ),
    AgentPairType.DEVOPS: AgentPairConfig(
        pair_type=AgentPairType.DEVOPS,
        agent_role=AgentRole.DEVOPS,
        critic_role=AgentRole.DEVOPS_CRITIC,
        max_iterations=3,
        approval_threshold=7.5,
    ),
    AgentPairType.QA: AgentPairConfig(
        pair_type=AgentPairType.QA,
        agent_role=AgentRole.QA,
        critic_role=AgentRole.QA_CRITIC,
        max_iterations=3,
        approval_threshold=8.0,  # QA must be thorough
    ),
    AgentPairType.AI_ARCHITECT: AgentPairConfig(
        pair_type=AgentPairType.AI_ARCHITECT,
        agent_role=AgentRole.AI_ARCHITECT,
        critic_role=AgentRole.AI_ARCHITECT_CRITIC,
        max_iterations=3,
        approval_threshold=8.0,
    ),
    AgentPairType.SECURITY: AgentPairConfig(
        pair_type=AgentPairType.SECURITY,
        agent_role=AgentRole.SECURITY,
        critic_role=AgentRole.SECURITY_CRITIC,
        max_iterations=5,  # More iterations for security
        approval_threshold=9.0,  # Highest bar for security
        min_score_threshold=7.0,  # No dimension below 7
    ),
    AgentPairType.PERFORMANCE: AgentPairConfig(
        pair_type=AgentPairType.PERFORMANCE,
        agent_role=AgentRole.PERFORMANCE,
        critic_role=AgentRole.PERFORMANCE_CRITIC,
        max_iterations=3,
        approval_threshold=7.5,
    ),
}


class CriticEvaluation(BaseModel):
    """Critic's evaluation of agent's output."""

    correctness: float = Field(ge=0, le=10, description="Technical correctness")
    completeness: float = Field(ge=0, le=10, description="Addresses all requirements")
    quality: float = Field(ge=0, le=10, description="Code/design quality")
    performance: float = Field(ge=0, le=10, description="Performance considerations")
    security: float = Field(ge=0, le=10, description="Security considerations")

    feedback: str = Field(description="Detailed feedback")
    concerns: list[str] = Field(default_factory=list, description="Specific concerns")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")

    approved: bool = Field(description="Overall approval")

    def average_score(self) -> float:
        """Calculate average score across dimensions."""
        return (
            self.correctness
            + self.completeness
            + self.quality
            + self.performance
            + self.security
        ) / 5.0

    def min_score(self) -> float:
        """Get minimum score across dimensions."""
        return min(
            self.correctness,
            self.completeness,
            self.quality,
            self.performance,
            self.security,
        )


class PairStatus(str, Enum):
    """Status of agent-critic pair interaction."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


def get_agent_config(role: AgentRole) -> AgentConfig:
    """Get configuration for an agent role."""
    return AGENT_CONFIGS[role]


def get_pair_config(pair_type: AgentPairType) -> AgentPairConfig:
    """Get configuration for an agent pair."""
    return AGENT_PAIRS[pair_type]


def get_critic_for_agent(agent_role: AgentRole) -> Optional[AgentRole]:
    """Get the critic role for a given agent role."""
    critic_map = {
        AgentRole.TECH_LEAD: AgentRole.TECH_LEAD_CRITIC,
        AgentRole.ARCHITECT: AgentRole.ARCHITECT_CRITIC,
        AgentRole.BACKEND: AgentRole.BACKEND_CRITIC,
        AgentRole.FRONTEND: AgentRole.FRONTEND_CRITIC,
        AgentRole.DATA: AgentRole.DATA_CRITIC,
        AgentRole.DEVOPS: AgentRole.DEVOPS_CRITIC,
        AgentRole.QA: AgentRole.QA_CRITIC,
        AgentRole.AI_ARCHITECT: AgentRole.AI_ARCHITECT_CRITIC,
        AgentRole.SECURITY: AgentRole.SECURITY_CRITIC,
        AgentRole.PERFORMANCE: AgentRole.PERFORMANCE_CRITIC,
    }
    return critic_map.get(agent_role)


def get_agent_for_critic(critic_role: AgentRole) -> Optional[AgentRole]:
    """Get the agent role for a given critic role."""
    agent_map = {
        AgentRole.TECH_LEAD_CRITIC: AgentRole.TECH_LEAD,
        AgentRole.ARCHITECT_CRITIC: AgentRole.ARCHITECT,
        AgentRole.BACKEND_CRITIC: AgentRole.BACKEND,
        AgentRole.FRONTEND_CRITIC: AgentRole.FRONTEND,
        AgentRole.DATA_CRITIC: AgentRole.DATA,
        AgentRole.DEVOPS_CRITIC: AgentRole.DEVOPS,
        AgentRole.QA_CRITIC: AgentRole.QA,
        AgentRole.AI_ARCHITECT_CRITIC: AgentRole.AI_ARCHITECT,
        AgentRole.SECURITY_CRITIC: AgentRole.SECURITY,
        AgentRole.PERFORMANCE_CRITIC: AgentRole.PERFORMANCE,
    }
    return agent_map.get(critic_role)


def is_approval_met(
    evaluation: CriticEvaluation, pair_config: AgentPairConfig
) -> bool:
    """Check if critic's evaluation meets approval thresholds."""
    avg_score = evaluation.average_score()
    min_score = evaluation.min_score()

    return (
        avg_score >= pair_config.approval_threshold
        and min_score >= pair_config.min_score_threshold
    )


# Metrics tracking
class PairMetrics(BaseModel):
    """Metrics for agent-critic pair performance."""

    pair_type: AgentPairType
    total_tasks: int = 0
    approved_first_try: int = 0
    total_iterations: int = 0
    escalations: int = 0
    average_score: float = 0.0

    def approval_rate(self) -> float:
        """Calculate first-try approval rate."""
        if self.total_tasks == 0:
            return 0.0
        return self.approved_first_try / self.total_tasks

    def avg_iterations(self) -> float:
        """Calculate average iterations per task."""
        if self.total_tasks == 0:
            return 0.0
        return self.total_iterations / self.total_tasks

    def escalation_rate(self) -> float:
        """Calculate escalation rate."""
        if self.total_tasks == 0:
            return 0.0
        return self.escalations / self.total_tasks
