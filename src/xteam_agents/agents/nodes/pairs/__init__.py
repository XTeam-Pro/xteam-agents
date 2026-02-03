"""Agent-Critic pair implementations."""

from .ai_architect_pair import AIAgentArchitect, AIArchitectCritic
from .architect_pair import ArchitectAgent, ArchitectCritic
from .backend_pair import BackendAgent, BackendCritic
from .data_pair import DataAgent, DataCritic
from .devops_pair import DevOpsAgent, DevOpsCritic
from .frontend_pair import FrontendAgent, FrontendCritic
from .performance_pair import PerformanceAgent, PerformanceCritic
from .qa_pair import QAAgent, QACritic
from .security_pair import SecurityAgent, SecurityCritic
from .tech_lead_pair import TechLeadAgent, TechLeadCritic

__all__ = [
    "TechLeadAgent",
    "TechLeadCritic",
    "ArchitectAgent",
    "ArchitectCritic",
    "BackendAgent",
    "BackendCritic",
    "FrontendAgent",
    "FrontendCritic",
    "DataAgent",
    "DataCritic",
    "DevOpsAgent",
    "DevOpsCritic",
    "QAAgent",
    "QACritic",
    "AIAgentArchitect",
    "AIArchitectCritic",
    "SecurityAgent",
    "SecurityCritic",
    "PerformanceAgent",
    "PerformanceCritic",
]
