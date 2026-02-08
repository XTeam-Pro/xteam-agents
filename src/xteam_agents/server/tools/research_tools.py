"""
Research Team MCP Tools

Инструменты для работы с исследовательской командой через MCP сервер.
"""

from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from xteam_agents.integration.research_adapter import get_research_adapter
from xteam_agents.agents.research_team import (
    ResearchTaskType,
    ResearchComplexity,
)
from xteam_agents.llm.provider import get_llm_provider
from xteam_agents.memory.manager import MemoryManager
import uuid
import logging

logger = logging.getLogger(__name__)

# Хранилище активных исследований (в production использовать Redis/DB)
_active_research_tasks: Dict[str, Dict[str, Any]] = {}

mcp = FastMCP("xteam-agents-research")


@mcp.tool()
async def submit_research_task(
    research_question: str,
    task_type: str,
    complexity: str = "standard",
    objectives: Optional[List[str]] = None,
    scope: str = "",
    constraints: Optional[List[str]] = None,
) -> dict:
    """
    Отправить исследовательскую задачу в Research Team.

    Args:
        research_question: Исследовательский вопрос (четкая формулировка)
        task_type: Тип задачи. Доступные типы:
            - dataset_design: Дизайн датасета
            - data_collection: Сбор данных
            - model_architecture: Архитектура модели
            - model_training: Обучение модели
            - curriculum_design: Дизайн учебной программы
            - assessment_design: Дизайн оценивания
            - learning_analytics: Анализ данных обучения
            - ab_testing: A/B тестирование
            - fundamental_research: Фундаментальное исследование
        complexity: Уровень сложности (exploratory/standard/complex/critical)
        objectives: Список целей исследования
        scope: Область исследования
        constraints: Ограничения и требования

    Returns:
        Dict с task_id, статусом и начальной информацией

    Examples:
        submit_research_task(
            research_question="Разработать датасет вопросов по алгебре с градацией сложности",
            task_type="dataset_design",
            complexity="complex",
            objectives=[
                "Определить структуру датасета",
                "Разработать таксономию сложности",
                "Создать annotation guidelines"
            ]
        )
    """
    try:
        # Валидация входных данных
        try:
            task_type_enum = ResearchTaskType(task_type)
        except ValueError:
            return {
                "error": f"Invalid task_type: {task_type}. "
                         f"Available types: {[t.value for t in ResearchTaskType]}"
            }

        try:
            complexity_enum = ResearchComplexity(complexity)
        except ValueError:
            return {
                "error": f"Invalid complexity: {complexity}. "
                         f"Available: exploratory, standard, complex, critical"
            }

        # Генерируем task_id
        task_id = str(uuid.uuid4())

        logger.info(
            f"Submitting research task {task_id}: "
            f"type={task_type}, complexity={complexity}"
        )

        # Инициализируем adapter
        llm_provider = get_llm_provider()
        memory_manager = MemoryManager()  # TODO: proper initialization
        adapter = get_research_adapter(llm_provider, memory_manager)

        # Сохраняем в активные задачи
        _active_research_tasks[task_id] = {
            "task_id": task_id,
            "research_question": research_question,
            "task_type": task_type,
            "complexity": complexity,
            "status": "pending",
            "started_at": None,
            "completed_at": None,
        }

        # Асинхронно запускаем исследование
        # В реальной реализации должно быть background task
        result = await adapter.invoke_research_team(
            research_question=research_question,
            task_type=task_type_enum,
            complexity=complexity_enum,
            objectives=objectives or [],
            scope=scope,
            constraints=constraints or [],
        )

        # Обновляем статус
        _active_research_tasks[task_id].update({
            "status": result.get("status", "completed"),
            "quality_score": result.get("quality_score"),
            "artifacts_count": len(result.get("artifacts", [])),
            "findings_count": len(result.get("findings", [])),
            "result": result,
        })

        logger.info(f"Research task {task_id} completed with quality {result.get('quality_score', 0):.2f}")

        return {
            "task_id": task_id,
            "status": "completed",
            "quality_score": result.get("quality_score"),
            "message": "Research completed successfully",
            "artifacts_count": len(result.get("artifacts", [])),
            "findings_count": len(result.get("findings", [])),
        }

    except Exception as e:
        logger.error(f"Failed to submit research task: {e}", exc_info=True)
        return {
            "error": str(e),
            "task_id": task_id if 'task_id' in locals() else None,
        }


@mcp.tool()
async def get_research_status(task_id: str) -> dict:
    """
    Получить статус исследовательской задачи.

    Args:
        task_id: ID задачи (возвращается при submit_research_task)

    Returns:
        Dict со статусом и прогрессом

    Examples:
        get_research_status("123e4567-e89b-12d3-a456-426614174000")
    """
    if task_id not in _active_research_tasks:
        return {
            "error": f"Task {task_id} not found",
            "available_tasks": list(_active_research_tasks.keys()),
        }

    task_info = _active_research_tasks[task_id]

    return {
        "task_id": task_id,
        "status": task_info.get("status"),
        "research_question": task_info.get("research_question"),
        "task_type": task_info.get("task_type"),
        "complexity": task_info.get("complexity"),
        "quality_score": task_info.get("quality_score"),
        "artifacts_count": task_info.get("artifacts_count", 0),
        "findings_count": task_info.get("findings_count", 0),
    }


@mcp.tool()
async def get_research_results(task_id: str) -> dict:
    """
    Получить полные результаты исследования.

    Args:
        task_id: ID задачи

    Returns:
        Dict с полными результатами, артефактами и находками

    Examples:
        get_research_results("123e4567-e89b-12d3-a456-426614174000")
    """
    if task_id not in _active_research_tasks:
        return {
            "error": f"Task {task_id} not found"
        }

    task_info = _active_research_tasks[task_id]

    if task_info.get("status") != "completed":
        return {
            "error": f"Task {task_id} is not completed yet. Status: {task_info.get('status')}",
            "status": task_info.get("status"),
        }

    result = task_info.get("result", {})

    # Форматируем результаты для удобства
    return {
        "task_id": task_id,
        "research_question": task_info.get("research_question"),
        "status": "completed",
        "quality_score": result.get("quality_score"),
        "delivery_package": result.get("delivery_package"),
        "artifacts": [
            {
                "title": artifact.get("title"),
                "type": artifact.get("artifact_type"),
                "created_by": artifact.get("created_by"),
                "validated": artifact.get("validated"),
            }
            for artifact in result.get("artifacts", [])
        ],
        "findings": [
            {
                "title": finding.get("title"),
                "confidence": finding.get("confidence"),
                "discovered_by": finding.get("discovered_by"),
            }
            for finding in result.get("findings", [])
        ],
        "implementation_tasks": result.get("delivery_package", {}).get("implementation_tasks", []),
    }


@mcp.tool()
async def list_research_tasks(status_filter: Optional[str] = None) -> dict:
    """
    Получить список всех исследовательских задач.

    Args:
        status_filter: Фильтр по статусу (pending/in_progress/completed/failed)

    Returns:
        Dict со списком задач

    Examples:
        list_research_tasks()
        list_research_tasks(status_filter="completed")
    """
    tasks = []

    for task_id, task_info in _active_research_tasks.items():
        if status_filter and task_info.get("status") != status_filter:
            continue

        tasks.append({
            "task_id": task_id,
            "research_question": task_info.get("research_question"),
            "task_type": task_info.get("task_type"),
            "complexity": task_info.get("complexity"),
            "status": task_info.get("status"),
            "quality_score": task_info.get("quality_score"),
        })

    return {
        "total_tasks": len(tasks),
        "filter_applied": status_filter,
        "tasks": tasks,
    }


@mcp.tool()
async def list_research_task_types() -> dict:
    """
    Получить список всех доступных типов исследовательских задач.

    Returns:
        Dict с типами задач и их описаниями
    """
    task_types = {
        "dataset_design": "Дизайн структуры датасета, features, schemas",
        "data_collection": "Разработка процедур сбора данных",
        "data_annotation": "Дизайн процесса аннотации данных",
        "model_architecture": "Разработка архитектуры нейронной модели",
        "model_training": "Стратегия обучения модели",
        "model_evaluation": "Оценка и валидация модели",
        "curriculum_design": "Дизайн учебной программы и knowledge graph",
        "assessment_design": "Разработка системы оценивания",
        "pedagogical_strategy": "Педагогические методы и подходы",
        "adaptive_algorithm": "Алгоритмы адаптивного обучения",
        "learning_analytics": "Анализ данных обучения",
        "cognitive_analysis": "Анализ когнитивных аспектов",
        "ab_testing": "Дизайн A/B теста",
        "fundamental_research": "Фундаментальное исследование",
    }

    complexity_levels = {
        "exploratory": "Предварительное исследование",
        "standard": "Стандартное исследование",
        "complex": "Сложное, междисциплинарное исследование",
        "critical": "Критическая задача, требует полной команды",
    }

    return {
        "task_types": task_types,
        "complexity_levels": complexity_levels,
        "research_team": {
            "scientists": 5,
            "methodologists": 4,
            "content_team": 5,
            "critics": 14,
            "total_agents": 28,
        },
    }
