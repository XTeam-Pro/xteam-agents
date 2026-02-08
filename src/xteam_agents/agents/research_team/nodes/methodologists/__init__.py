"""Methodologists Team - Команда методистов"""

from xteam_agents.agents.research_team.nodes.methodologists.lead_methodologist import (
    LeadMethodologist, LeadMethodologistCritic
)
from xteam_agents.agents.research_team.nodes.methodologists.curriculum_designer import (
    CurriculumDesigner, CurriculumDesignerCritic
)
from xteam_agents.agents.research_team.nodes.methodologists.assessment_designer import (
    AssessmentDesigner, AssessmentDesignerCritic
)
from xteam_agents.agents.research_team.nodes.methodologists.adaptive_learning_specialist import (
    AdaptiveLearningSpecialist, AdaptiveLearningSpecialistCritic
)

__all__ = [
    "LeadMethodologist", "LeadMethodologistCritic",
    "CurriculumDesigner", "CurriculumDesignerCritic",
    "AssessmentDesigner", "AssessmentDesignerCritic",
    "AdaptiveLearningSpecialist", "AdaptiveLearningSpecialistCritic",
]
