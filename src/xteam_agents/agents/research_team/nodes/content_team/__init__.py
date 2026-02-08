"""Content Team - Команда разработки образовательного контента"""

from xteam_agents.agents.research_team.nodes.content_team.content_architect import (
    ContentArchitect, ContentArchitectCritic
)
from xteam_agents.agents.research_team.nodes.content_team.subject_matter_experts import (
    SMEMath, SMEMathCritic, SMEScience, SMEScienceCritic
)
from xteam_agents.agents.research_team.nodes.content_team.dataset_engineer import (
    DatasetEngineer, DatasetEngineerCritic
)
from xteam_agents.agents.research_team.nodes.content_team.annotation_specialist import (
    AnnotationSpecialist, AnnotationSpecialistCritic
)

__all__ = [
    "ContentArchitect", "ContentArchitectCritic",
    "SMEMath", "SMEMathCritic",
    "SMEScience", "SMEScienceCritic",
    "DatasetEngineer", "DatasetEngineerCritic",
    "AnnotationSpecialist", "AnnotationSpecialistCritic",
]
