"""
Execute Research Node - выполнение через Research Team

Интеграция исследовательской команды в Cognitive OS workflow.
"""

from typing import Dict, Any
from xteam_agents.models.state import AgentState
from xteam_agents.integration.research_adapter import get_research_adapter
from xteam_agents.agents.research_team import ResearchTaskType, ResearchComplexity
import logging

logger = logging.getLogger(__name__)


async def execute_research_node(state: AgentState) -> Dict[str, Any]:
    """
    Выполнение исследования через Research Team.

    Конвертирует AgentState → ResearchState, запускает Research Team,
    конвертирует результаты обратно в AgentState.

    Args:
        state: Текущее состояние Cognitive OS

    Returns:
        Обновления состояния с результатами исследования
    """
    logger.info(f"Executing research for task: {state.task_context.get('description', '')}")

    # Получаем adapter
    adapter = get_research_adapter(
        llm_provider=state.task_context.get("llm_provider"),
        memory_manager=state.task_context.get("memory_manager"),
    )

    # Извлекаем параметры из state
    task_description = state.task_context.get("description", "")

    # Классификация типа задачи
    task_type = classify_research_task_type(task_description)

    # Оценка сложности
    complexity = estimate_research_complexity(state)

    # Извлечение целей
    objectives = extract_research_objectives(state)

    logger.info(
        f"Research classification: type={task_type.value}, "
        f"complexity={complexity.value}, "
        f"objectives_count={len(objectives)}"
    )

    try:
        # Запуск Research Team
        result = await adapter.invoke_research_team(
            research_question=task_description,
            task_type=task_type,
            complexity=complexity,
            objectives=objectives,
            scope=state.task_context.get("scope", ""),
            constraints=state.task_context.get("constraints", []),
        )

        logger.info(
            f"Research completed: status={result.get('status')}, "
            f"quality={result.get('quality_score', 0):.2f}, "
            f"artifacts={len(result.get('artifacts', []))}"
        )

        # Формируем обновления для AgentState
        updates = {
            "messages": [
                {
                    "role": "assistant",
                    "content": (
                        f"Исследование завершено.\n"
                        f"Качество: {result.get('quality_score', 0):.2f}\n"
                        f"Артефактов: {len(result.get('artifacts', []))}\n"
                        f"Находок: {len(result.get('findings', []))}"
                    ),
                }
            ],
            "artifacts": [
                f"research_artifact_{i}_{artifact.get('title', 'untitled')}"
                for i, artifact in enumerate(result.get("artifacts", []))
            ],
        }

        # Если есть delivery package с implementation tasks
        delivery_package = result.get("delivery_package")
        if delivery_package:
            implementation_tasks = delivery_package.get("implementation_tasks", [])
            if implementation_tasks:
                # Можно добавить в plan или subtasks
                updates["plan"] = {
                    "description": "Implementation tasks from Research Team",
                    "tasks": implementation_tasks,
                    "source": "research_team",
                }

        return updates

    except Exception as e:
        logger.error(f"Research execution failed: {e}", exc_info=True)
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Ошибка при выполнении исследования: {str(e)}",
                }
            ],
            "error": str(e),
        }


def classify_research_task_type(description: str) -> ResearchTaskType:
    """
    Классификация типа исследовательской задачи по описанию.

    Args:
        description: Описание задачи

    Returns:
        ResearchTaskType
    """
    description_lower = description.lower()

    # Датасеты
    if any(kw in description_lower for kw in ["dataset", "data collection", "датасет", "данные"]):
        return ResearchTaskType.DATASET_DESIGN

    # Модели
    if any(kw in description_lower for kw in ["model", "neural", "модель", "нейронн"]):
        return ResearchTaskType.MODEL_ARCHITECTURE

    # Curriculum
    if any(kw in description_lower for kw in ["curriculum", "учебн", "программ"]):
        return ResearchTaskType.CURRICULUM_DESIGN

    # Assessment
    if any(kw in description_lower for kw in ["assessment", "оценивание", "тест"]):
        return ResearchTaskType.ASSESSMENT_DESIGN

    # Analytics
    if any(kw in description_lower for kw in ["analytics", "analysis", "аналитика", "анализ"]):
        return ResearchTaskType.LEARNING_ANALYTICS

    # A/B testing
    if any(kw in description_lower for kw in ["a/b", "experiment", "эксперимент"]):
        return ResearchTaskType.A_B_TESTING

    # Default
    return ResearchTaskType.FUNDAMENTAL_RESEARCH


def estimate_research_complexity(state: AgentState) -> ResearchComplexity:
    """
    Оценка сложности исследовательской задачи.

    Args:
        state: Состояние агента

    Returns:
        ResearchComplexity
    """
    # Простая эвристика - можно улучшить
    description = state.task_context.get("description", "")
    requirements = state.task_context.get("requirements", [])

    # Критическая сложность
    if any(kw in description.lower() for kw in ["critical", "критичн", "security", "безопасн"]):
        return ResearchComplexity.CRITICAL

    # Сложная задача
    if len(requirements) > 5 or len(description) > 500:
        return ResearchComplexity.COMPLEX

    # Exploratory
    if any(kw in description.lower() for kw in ["explore", "investigate", "изучить", "исследова"]):
        return ResearchComplexity.EXPLORATORY

    # Standard по умолчанию
    return ResearchComplexity.STANDARD


def extract_research_objectives(state: AgentState) -> list[str]:
    """
    Извлечение целей исследования из состояния.

    Args:
        state: Состояние агента

    Returns:
        Список целей
    """
    # Пытаемся найти objectives в различных местах
    objectives = []

    # Из task_context
    if "objectives" in state.task_context:
        objectives.extend(state.task_context["objectives"])

    # Из requirements
    if "requirements" in state.task_context:
        objectives.extend(state.task_context["requirements"])

    # Из analysis если есть
    if hasattr(state, "analysis") and isinstance(state.analysis, dict):
        if "goals" in state.analysis:
            objectives.extend(state.analysis["goals"])

    # Если ничего не найдено, создаем базовую цель
    if not objectives:
        objectives = ["Провести исследование согласно запросу"]

    return objectives


def requires_research(state: AgentState) -> bool:
    """
    Определяет, требуется ли научное исследование для задачи.

    Args:
        state: Состояние агента

    Returns:
        True если требуется Research Team
    """
    description = state.task_context.get("description", "").lower()

    # Ключевые слова, указывающие на research задачу
    research_keywords = [
        "dataset", "датасет", "данные",
        "model", "модель", "neural", "нейронн",
        "curriculum", "учебн", "программ",
        "assessment", "оценивание",
        "analytics", "аналитика", "analysis", "анализ",
        "research", "исследова", "изучи",
        "study", "experiment", "эксперимент",
        "a/b test",
        "learning path", "траектори",
        "pedagogical", "педагогич",
        "cognitive", "когнитивн",
    ]

    return any(keyword in description for keyword in research_keywords)
