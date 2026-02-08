"""
Research Team Adapter

Интеграция исследовательской команды с основной системой xteam-agents.
Позволяет вызывать Research Team из Cognitive OS или напрямую.
"""

from typing import Dict, Any, List
from xteam_agents.agents.research_team import (
    create_research_team_graph,
    ResearchState,
    ResearchTaskType,
    ResearchComplexity,
)
from xteam_agents.models.state import AgentState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from datetime import datetime
import uuid


class ResearchTeamAdapter:
    """
    Адаптер для интеграции Research Team в Cognitive OS.

    ИСПОЛЬЗОВАНИЕ:
    1. Cognitive OS analyze node определяет, что нужно исследование
    2. ExecutionMode.RESEARCH маршрутизирует в Research Team
    3. Research Team выполняет исследование
    4. Результаты возвращаются в Cognitive OS state
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
        self.research_graph = create_research_team_graph(llm_provider, memory_manager)

    async def invoke_research_team(
        self,
        research_question: str,
        task_type: ResearchTaskType,
        complexity: ResearchComplexity,
        objectives: List[str],
        scope: str = "",
        constraints: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Вызов исследовательской команды.

        Args:
            research_question: Основной исследовательский вопрос
            task_type: Тип исследовательской задачи
            complexity: Сложность задачи
            objectives: Список целей
            scope: Область исследования
            constraints: Ограничения

        Returns:
            Результаты исследования (delivery_package)
        """
        # Создаем начальное состояние
        initial_state = ResearchState(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            complexity=complexity,
            research_question=research_question,
            objectives=objectives,
            scope=scope,
            constraints=constraints or [],
        )

        # Запускаем граф
        final_state = await self.research_graph.ainvoke(initial_state)

        return {
            "delivery_package": final_state.get("delivery_package"),
            "artifacts": final_state.get("artifacts", []),
            "findings": final_state.get("findings", []),
            "quality_score": final_state.get("quality_score"),
            "status": final_state.get("status"),
        }

    def convert_agent_state_to_research_state(self, agent_state: AgentState) -> ResearchState:
        """
        Конвертация AgentState в ResearchState для передачи в Research Team.

        Args:
            agent_state: Состояние из Cognitive OS

        Returns:
            ResearchState для исследовательской команды
        """
        # Извлекаем информацию из AgentState
        task_description = agent_state.task_context.get("description", "")
        task_id = agent_state.task_context.get("task_id", str(uuid.uuid4()))

        # Классифицируем тип задачи
        task_type = self._classify_research_task(task_description)
        complexity = self._estimate_complexity(agent_state)

        return ResearchState(
            task_id=task_id,
            task_type=task_type,
            complexity=complexity,
            research_question=task_description,
            objectives=self._extract_objectives(agent_state),
            scope=agent_state.task_context.get("scope", ""),
            constraints=agent_state.task_context.get("constraints", []),
        )

    def convert_research_state_to_agent_state(
        self,
        research_state: ResearchState,
        original_agent_state: AgentState,
    ) -> Dict[str, Any]:
        """
        Конвертация результатов Research Team обратно в AgentState.

        Args:
            research_state: Итоговое состояние исследования
            original_agent_state: Оригинальное состояние Cognitive OS

        Returns:
            Обновления для AgentState
        """
        updates = {
            "execution_results": {
                "research_completed": True,
                "delivery_package": research_state.delivery_package,
                "quality_score": research_state.quality_score,
            },
            "artifacts": [
                {
                    "type": "research_artifact",
                    "content": artifact.content,
                    "metadata": artifact.metadata,
                }
                for artifact in research_state.artifacts
            ],
        }

        # Если есть implementation tasks, добавляем их в план
        if research_state.implementation_tasks:
            updates["plan"] = {
                "tasks": research_state.implementation_tasks,
                "source": "research_team",
            }

        return updates

    def _classify_research_task(self, description: str) -> ResearchTaskType:
        """Классификация типа исследовательской задачи"""
        # TODO: Более сложная классификация через LLM
        description_lower = description.lower()

        if "dataset" in description_lower or "data collection" in description_lower:
            return ResearchTaskType.DATASET_DESIGN
        elif "model" in description_lower or "neural" in description_lower:
            return ResearchTaskType.MODEL_ARCHITECTURE
        elif "curriculum" in description_lower or "learning path" in description_lower:
            return ResearchTaskType.CURRICULUM_DESIGN
        elif "assessment" in description_lower:
            return ResearchTaskType.ASSESSMENT_DESIGN
        else:
            return ResearchTaskType.FUNDAMENTAL_RESEARCH

    def _estimate_complexity(self, agent_state: AgentState) -> ResearchComplexity:
        """Оценка сложности задачи"""
        # TODO: Более сложная оценка
        if agent_state.task_context.get("complexity") == "critical":
            return ResearchComplexity.CRITICAL
        elif len(agent_state.task_context.get("requirements", [])) > 5:
            return ResearchComplexity.COMPLEX
        else:
            return ResearchComplexity.STANDARD

    def _extract_objectives(self, agent_state: AgentState) -> List[str]:
        """Извлечение целей из AgentState"""
        # TODO: Парсинг целей из task_context
        return agent_state.task_context.get("objectives", ["Провести исследование"])


# Глобальный экземпляр (singleton pattern)
_research_adapter_instance = None


def get_research_adapter(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
) -> ResearchTeamAdapter:
    """
    Получение единственного экземпляра Research Team Adapter.

    Args:
        llm_provider: LLM provider
        memory_manager: Memory manager

    Returns:
        ResearchTeamAdapter instance
    """
    global _research_adapter_instance
    if _research_adapter_instance is None:
        _research_adapter_instance = ResearchTeamAdapter(llm_provider, memory_manager)
    return _research_adapter_instance
