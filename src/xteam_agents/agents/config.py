"""Agent team configuration."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent roles in the team."""

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


class RACILevel(str, Enum):
    """RACI responsibility levels."""

    RESPONSIBLE = "R"  # Does the work
    ACCOUNTABLE = "A"  # Ultimately accountable
    CONSULTED = "C"  # Must be consulted
    INFORMED = "I"  # Must be informed


class TaskCategory(str, Enum):
    """Task categories for routing."""

    ARCHITECTURE = "architecture"
    BACKEND_LOGIC = "backend_logic"
    FRONTEND_UI = "frontend_ui"
    DATA_MODEL = "data_model"
    AI_SYSTEM = "ai_system"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    GENERAL = "general"


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    role: AgentRole
    name: str
    description: str
    model: str = "claude-sonnet-4-5"
    temperature: float = 0.5
    max_tokens: int = 4096
    can_escalate: bool = True
    can_approve: bool = False
    can_commit: bool = False

    class Config:
        frozen = True


# Agent configurations
AGENT_CONFIGS = {
    AgentRole.TECH_LEAD: AgentConfig(
        role=AgentRole.TECH_LEAD,
        name="TechLeadAgent",
        description="Technical leadership and decision authority",
        model="claude-opus-4-5",
        temperature=0.3,
        can_approve=True,
        can_commit=True,
    ),
    AgentRole.ARCHITECT: AgentConfig(
        role=AgentRole.ARCHITECT,
        name="ArchitectAgent",
        description="System architecture design and boundaries",
        model="claude-sonnet-4-5",
        temperature=0.5,
    ),
    AgentRole.BACKEND: AgentConfig(
        role=AgentRole.BACKEND,
        name="BackendAgent",
        description="Business logic and API implementation",
        model="claude-sonnet-4-5",
        temperature=0.2,
    ),
    AgentRole.FRONTEND: AgentConfig(
        role=AgentRole.FRONTEND,
        name="FrontendAgent",
        description="User interface and client logic",
        model="claude-sonnet-4-5",
        temperature=0.4,
    ),
    AgentRole.DATA: AgentConfig(
        role=AgentRole.DATA,
        name="DataAgent",
        description="Data architecture and optimization",
        model="claude-sonnet-4-5",
        temperature=0.2,
    ),
    AgentRole.DEVOPS: AgentConfig(
        role=AgentRole.DEVOPS,
        name="DevOpsAgent",
        description="Operations and infrastructure",
        model="claude-sonnet-4-5",
        temperature=0.3,
    ),
    AgentRole.QA: AgentConfig(
        role=AgentRole.QA,
        name="QAAgent",
        description="Quality assurance and testing",
        model="claude-sonnet-4-5",
        temperature=0.1,
    ),
    AgentRole.AI_ARCHITECT: AgentConfig(
        role=AgentRole.AI_ARCHITECT,
        name="AIAgentArchitect",
        description="AI systems architecture",
        model="claude-opus-4-5",
        temperature=0.5,
    ),
    AgentRole.SECURITY: AgentConfig(
        role=AgentRole.SECURITY,
        name="SecurityAgent",
        description="Security and compliance",
        model="claude-opus-4-5",
        temperature=0.1,
    ),
    AgentRole.PERFORMANCE: AgentConfig(
        role=AgentRole.PERFORMANCE,
        name="PerformanceAgent",
        description="Performance optimization",
        model="claude-sonnet-4-5",
        temperature=0.3,
    ),
}


class RoutingRule(BaseModel):
    """Routing rule for task classification."""

    category: TaskCategory
    keywords: list[str]
    required_agents: list[AgentRole]
    optional_agents: list[AgentRole] = Field(default_factory=list)
    needs_architecture_review: bool = False
    needs_security_review: bool = False
    needs_performance_review: bool = False


# Routing rules matrix
ROUTING_RULES = [
    RoutingRule(
        category=TaskCategory.ARCHITECTURE,
        keywords=[
            "architecture",
            "system design",
            "boundaries",
            "service design",
            "components",
            "integration",
        ],
        required_agents=[AgentRole.ARCHITECT],
        needs_architecture_review=True,
    ),
    RoutingRule(
        category=TaskCategory.BACKEND_LOGIC,
        keywords=["api", "backend", "business logic", "integration", "server"],
        required_agents=[AgentRole.BACKEND],
        optional_agents=[AgentRole.DATA],
    ),
    RoutingRule(
        category=TaskCategory.FRONTEND_UI,
        keywords=["ui", "ux", "frontend", "client", "interface", "react", "vue"],
        required_agents=[AgentRole.FRONTEND],
    ),
    RoutingRule(
        category=TaskCategory.DATA_MODEL,
        keywords=[
            "database",
            "schema",
            "migration",
            "query",
            "data model",
            "sql",
            "postgres",
            "neo4j",
        ],
        required_agents=[AgentRole.DATA],
        optional_agents=[AgentRole.BACKEND],
    ),
    RoutingRule(
        category=TaskCategory.AI_SYSTEM,
        keywords=[
            "llm",
            "agent",
            "ai",
            "orchestration",
            "memory",
            "tools",
            "prompt",
            "embedding",
        ],
        required_agents=[AgentRole.AI_ARCHITECT],
        optional_agents=[AgentRole.BACKEND],
    ),
    RoutingRule(
        category=TaskCategory.INFRASTRUCTURE,
        keywords=[
            "deploy",
            "ci/cd",
            "infrastructure",
            "monitoring",
            "docker",
            "kubernetes",
            "rollback",
        ],
        required_agents=[AgentRole.DEVOPS],
    ),
    RoutingRule(
        category=TaskCategory.SECURITY,
        keywords=[
            "security",
            "auth",
            "permission",
            "sensitive",
            "encryption",
            "vulnerability",
            "access control",
        ],
        required_agents=[AgentRole.SECURITY],
        needs_security_review=True,
    ),
    RoutingRule(
        category=TaskCategory.PERFORMANCE,
        keywords=[
            "performance",
            "optimization",
            "latency",
            "throughput",
            "scale",
            "load",
            "bottleneck",
        ],
        required_agents=[AgentRole.PERFORMANCE],
        needs_performance_review=True,
    ),
    RoutingRule(
        category=TaskCategory.TESTING,
        keywords=["test", "qa", "quality", "bug", "edge case", "validation"],
        required_agents=[AgentRole.QA],
    ),
]


# RACI Matrix
RACI_MATRIX = {
    "architecture": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.RESPONSIBLE,
        AgentRole.BACKEND: RACILevel.INFORMED,
        AgentRole.FRONTEND: RACILevel.INFORMED,
        AgentRole.DATA: RACILevel.CONSULTED,
        AgentRole.DEVOPS: RACILevel.CONSULTED,
        AgentRole.QA: RACILevel.INFORMED,
        AgentRole.AI_ARCHITECT: RACILevel.CONSULTED,
        AgentRole.SECURITY: RACILevel.CONSULTED,
        AgentRole.PERFORMANCE: RACILevel.CONSULTED,
    },
    "business_requirements": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.CONSULTED,
    },
    "tech_stack": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.RESPONSIBLE,
        AgentRole.BACKEND: RACILevel.CONSULTED,
        AgentRole.FRONTEND: RACILevel.CONSULTED,
        AgentRole.DATA: RACILevel.CONSULTED,
        AgentRole.DEVOPS: RACILevel.CONSULTED,
        AgentRole.AI_ARCHITECT: RACILevel.CONSULTED,
        AgentRole.SECURITY: RACILevel.CONSULTED,
        AgentRole.PERFORMANCE: RACILevel.CONSULTED,
    },
    "backend_logic": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.INFORMED,
        AgentRole.BACKEND: RACILevel.RESPONSIBLE,
        AgentRole.DATA: RACILevel.CONSULTED,
        AgentRole.QA: RACILevel.CONSULTED,
    },
    "frontend_ux": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.INFORMED,
        AgentRole.FRONTEND: RACILevel.RESPONSIBLE,
        AgentRole.QA: RACILevel.CONSULTED,
    },
    "data_model": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.CONSULTED,
        AgentRole.BACKEND: RACILevel.CONSULTED,
        AgentRole.DATA: RACILevel.RESPONSIBLE,
        AgentRole.SECURITY: RACILevel.CONSULTED,
        AgentRole.PERFORMANCE: RACILevel.CONSULTED,
        AgentRole.QA: RACILevel.CONSULTED,
    },
    "ai_architecture": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.CONSULTED,
        AgentRole.AI_ARCHITECT: RACILevel.RESPONSIBLE,
        AgentRole.SECURITY: RACILevel.CONSULTED,
        AgentRole.PERFORMANCE: RACILevel.CONSULTED,
    },
    "infrastructure": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.INFORMED,
        AgentRole.DEVOPS: RACILevel.RESPONSIBLE,
        AgentRole.SECURITY: RACILevel.CONSULTED,
        AgentRole.PERFORMANCE: RACILevel.CONSULTED,
    },
    "security": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.CONSULTED,
        AgentRole.DATA: RACILevel.CONSULTED,
        AgentRole.DEVOPS: RACILevel.CONSULTED,
        AgentRole.SECURITY: RACILevel.RESPONSIBLE,
    },
    "performance": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.ARCHITECT: RACILevel.CONSULTED,
        AgentRole.BACKEND: RACILevel.CONSULTED,
        AgentRole.FRONTEND: RACILevel.CONSULTED,
        AgentRole.DATA: RACILevel.CONSULTED,
        AgentRole.DEVOPS: RACILevel.CONSULTED,
        AgentRole.PERFORMANCE: RACILevel.RESPONSIBLE,
    },
    "testing": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
        AgentRole.BACKEND: RACILevel.CONSULTED,
        AgentRole.FRONTEND: RACILevel.CONSULTED,
        AgentRole.DATA: RACILevel.CONSULTED,
        AgentRole.DEVOPS: RACILevel.CONSULTED,
        AgentRole.QA: RACILevel.RESPONSIBLE,
    },
    "final_gate": {
        AgentRole.TECH_LEAD: RACILevel.ACCOUNTABLE,
    },
}


class EscalationReason(str, Enum):
    """Reasons for escalating to TechLead."""

    AMBIGUOUS_REQUIREMENTS = "ambiguous_requirements"
    ARCHITECTURE_VIOLATION = "architecture_violation"
    SECURITY_RISK = "security_risk"
    SCALING_RISK = "scaling_risk"
    IRREVERSIBLE_DECISION = "irreversible_decision"
    CROSS_SYSTEM_IMPACT = "cross_system_impact"
    TECH_DEBT_CONCERN = "tech_debt_concern"
    RESOURCE_CONSTRAINT = "resource_constraint"


class Escalation(BaseModel):
    """Escalation request from agent to TechLead."""

    from_agent: AgentRole
    to_agent: AgentRole = AgentRole.TECH_LEAD
    reason: EscalationReason
    context: dict
    proposed_solution: Optional[str] = None
    urgency: str = "normal"  # low, normal, high, critical


def get_agent_config(role: AgentRole) -> AgentConfig:
    """Get configuration for an agent role."""
    return AGENT_CONFIGS[role]


def classify_task(task_description: str) -> list[TaskCategory]:
    """Classify task into categories based on keywords."""
    categories = []
    task_lower = task_description.lower()

    for rule in ROUTING_RULES:
        if any(keyword in task_lower for keyword in rule.keywords):
            categories.append(rule.category)

    return categories if categories else [TaskCategory.GENERAL]


def get_required_agents(categories: list[TaskCategory]) -> set[AgentRole]:
    """Get required agents for given task categories."""
    agents = {AgentRole.TECH_LEAD}  # Always include TechLead

    for rule in ROUTING_RULES:
        if rule.category in categories:
            agents.update(rule.required_agents)

    # Add QA for execution tasks
    if any(
        cat
        in [
            TaskCategory.BACKEND_LOGIC,
            TaskCategory.FRONTEND_UI,
            TaskCategory.DATA_MODEL,
        ]
        for cat in categories
    ):
        agents.add(AgentRole.QA)

    return agents


def needs_review(categories: list[TaskCategory]) -> dict[str, bool]:
    """Determine if task needs special reviews."""
    reviews = {
        "architecture": False,
        "security": False,
        "performance": False,
    }

    for rule in ROUTING_RULES:
        if rule.category in categories:
            if rule.needs_architecture_review:
                reviews["architecture"] = True
            if rule.needs_security_review:
                reviews["security"] = True
            if rule.needs_performance_review:
                reviews["performance"] = True

    return reviews


def get_raci_level(domain: str, agent: AgentRole) -> Optional[RACILevel]:
    """Get RACI level for agent in given domain."""
    return RACI_MATRIX.get(domain, {}).get(agent)


def can_agent_execute(domain: str, agent: AgentRole) -> bool:
    """Check if agent can execute in given domain."""
    level = get_raci_level(domain, agent)
    return level in [RACILevel.RESPONSIBLE, RACILevel.ACCOUNTABLE]


def must_consult_agent(domain: str, agent: AgentRole) -> bool:
    """Check if agent must be consulted for domain."""
    level = get_raci_level(domain, agent)
    return level == RACILevel.CONSULTED
