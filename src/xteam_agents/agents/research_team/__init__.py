"""
Research Team Module

Научно-исследовательская команда для разработки образовательных датасетов,
нейронных моделей и инновационных методик обучения.

Команда состоит из трех подразделений:
1. Scientists (Ученые) - фундаментальные исследования
2. Methodologists (Методисты) - разработка образовательных методик
3. Content Team (Команда контента) - создание датасетов и учебных материалов
"""

from xteam_agents.agents.research_team.research_graph import (
    create_research_team_graph,
    ResearchTeamOrchestrator,
)
from xteam_agents.agents.research_team.research_state import (
    ResearchState,
    ResearchTaskType,
    ResearchComplexity,
)

__all__ = [
    "create_research_team_graph",
    "ResearchTeamOrchestrator",
    "ResearchState",
    "ResearchTaskType",
    "ResearchComplexity",
]
