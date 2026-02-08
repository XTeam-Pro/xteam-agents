"""
Research Team State Models

Определяет состояние и типы задач для исследовательской команды.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Annotated
from pydantic import BaseModel, Field
from datetime import datetime


class ResearchTaskType(str, Enum):
    """Типы исследовательских задач"""

    # Фундаментальные исследования
    FUNDAMENTAL_RESEARCH = "fundamental_research"
    LITERATURE_REVIEW = "literature_review"
    HYPOTHESIS_TESTING = "hypothesis_testing"

    # Разработка датасетов
    DATASET_DESIGN = "dataset_design"
    DATA_COLLECTION = "data_collection"
    DATA_ANNOTATION = "data_annotation"
    DATASET_VALIDATION = "dataset_validation"

    # Разработка моделей
    MODEL_ARCHITECTURE = "model_architecture"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_OPTIMIZATION = "model_optimization"

    # Методическая разработка
    CURRICULUM_DESIGN = "curriculum_design"
    ASSESSMENT_DESIGN = "assessment_design"
    PEDAGOGICAL_STRATEGY = "pedagogical_strategy"
    ADAPTIVE_ALGORITHM = "adaptive_algorithm"

    # Аналитика и исследования
    LEARNING_ANALYTICS = "learning_analytics"
    COGNITIVE_ANALYSIS = "cognitive_analysis"
    EFFECTIVENESS_STUDY = "effectiveness_study"
    A_B_TESTING = "ab_testing"


class ResearchComplexity(str, Enum):
    """Сложность исследовательской задачи"""

    EXPLORATORY = "exploratory"  # Предварительное исследование
    STANDARD = "standard"  # Стандартное исследование
    COMPLEX = "complex"  # Сложное исследование, требует междисциплинарного подхода
    CRITICAL = "critical"  # Критическая задача, требует полной команды и валидации


class ResearchPhase(str, Enum):
    """Фазы исследовательского процесса"""

    INITIALIZATION = "initialization"  # Формулировка задачи
    LITERATURE_REVIEW = "literature_review"  # Обзор литературы
    METHODOLOGY_DESIGN = "methodology_design"  # Разработка методологии
    DATA_PREPARATION = "data_preparation"  # Подготовка данных
    IMPLEMENTATION = "implementation"  # Реализация
    EXPERIMENTATION = "experimentation"  # Эксперименты
    ANALYSIS = "analysis"  # Анализ результатов
    VALIDATION = "validation"  # Валидация
    DOCUMENTATION = "documentation"  # Документирование
    DELIVERY = "delivery"  # Передача результатов


class ResearchArtifact(BaseModel):
    """Артефакт исследования"""

    artifact_type: str = Field(description="Тип артефакта (paper, dataset, model, methodology)")
    title: str = Field(description="Название артефакта")
    description: str = Field(description="Описание артефакта")
    content: Dict[str, Any] = Field(default_factory=dict, description="Содержимое артефакта")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    created_by: str = Field(description="Агент, создавший артефакт")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    validated: bool = Field(default=False, description="Прошел ли артефакт валидацию")
    validation_score: Optional[float] = Field(default=None, description="Оценка качества (0-1)")


class ResearchFinding(BaseModel):
    """Научное открытие или результат"""

    finding_id: str = Field(description="Уникальный идентификатор находки")
    title: str = Field(description="Название находки")
    description: str = Field(description="Подробное описание")
    evidence: List[str] = Field(default_factory=list, description="Доказательства")
    confidence: float = Field(ge=0.0, le=1.0, description="Уровень уверенности")
    implications: List[str] = Field(default_factory=list, description="Последствия для системы")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    discovered_by: str = Field(description="Агент, сделавший открытие")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentResult(BaseModel):
    """Результат эксперимента"""

    experiment_id: str = Field(description="ID эксперимента")
    hypothesis: str = Field(description="Проверяемая гипотеза")
    methodology: str = Field(description="Методология эксперимента")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="Сводка данных")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Метрики результатов")
    statistical_significance: Optional[float] = Field(default=None, description="Статистическая значимость")
    conclusion: str = Field(description="Вывод эксперимента")
    limitations: List[str] = Field(default_factory=list, description="Ограничения исследования")


def merge_research_artifacts(
    existing: List[ResearchArtifact],
    new: List[ResearchArtifact]
) -> List[ResearchArtifact]:
    """Редьюсер для объединения артефактов"""
    return existing + new


def merge_research_findings(
    existing: List[ResearchFinding],
    new: List[ResearchFinding]
) -> List[ResearchFinding]:
    """Редьюсер для объединения находок"""
    return existing + new


def merge_experiments(
    existing: List[ExperimentResult],
    new: List[ExperimentResult]
) -> List[ExperimentResult]:
    """Редьюсер для объединения экспериментов"""
    return existing + new


class ResearchState(BaseModel):
    """
    Состояние исследовательской команды.

    Отслеживает весь процесс научного исследования от формулировки задачи
    до передачи результатов команде разработки.
    """

    # Основная информация о задаче
    task_id: str = Field(description="Уникальный ID исследовательской задачи")
    task_type: ResearchTaskType = Field(description="Тип исследовательской задачи")
    complexity: ResearchComplexity = Field(description="Сложность задачи")

    # Описание задачи
    research_question: str = Field(description="Основной исследовательский вопрос")
    objectives: List[str] = Field(default_factory=list, description="Цели исследования")
    scope: str = Field(default="", description="Область исследования")
    constraints: List[str] = Field(default_factory=list, description="Ограничения и требования")

    # Процесс исследования
    current_phase: ResearchPhase = Field(default=ResearchPhase.INITIALIZATION)
    phases_completed: List[ResearchPhase] = Field(default_factory=list)

    # Научные результаты
    literature_review: str = Field(default="", description="Обзор литературы")
    methodology: str = Field(default="", description="Методология исследования")
    hypothesis: List[str] = Field(default_factory=list, description="Гипотезы")

    # Артефакты и результаты
    artifacts: Annotated[
        List[ResearchArtifact],
        merge_research_artifacts
    ] = Field(default_factory=list, description="Созданные артефакты")

    findings: Annotated[
        List[ResearchFinding],
        merge_research_findings
    ] = Field(default_factory=list, description="Научные открытия")

    experiments: Annotated[
        List[ExperimentResult],
        merge_experiments
    ] = Field(default_factory=list, description="Результаты экспериментов")

    # Взаимодействие команды
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="История сообщений между агентами"
    )

    assigned_agents: Dict[str, str] = Field(
        default_factory=dict,
        description="Назначенные агенты для каждой фазы"
    )

    # Валидация и качество
    peer_reviews: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Рецензии от других агентов"
    )

    quality_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Общая оценка качества исследования"
    )

    # Интеграция с разработкой
    implementation_tasks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Задачи для команды разработки"
    )

    delivery_package: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Пакет для передачи в разработку"
    )

    # Метаданные
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    status: str = Field(default="in_progress", description="Статус исследования")

    class Config:
        arbitrary_types_allowed = True
