"""
Research Team Usage Examples

Примеры использования исследовательской команды для различных задач.
"""

import asyncio
from xteam_agents.agents.research_team import (
    ResearchState,
    ResearchTaskType,
    ResearchComplexity,
    create_research_team_graph,
)
from xteam_agents.integration.research_adapter import ResearchTeamAdapter
from xteam_agents.llm.provider import get_llm_provider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.config import settings


async def example_dataset_design():
    """
    Пример: Разработка датасета для адаптивного обучения математике.

    Задача: Создать датасет вопросов по алгебре с градацией сложности,
    аннотированный по концептам knowledge graph, для обучения модели
    предсказания mastery level.
    """
    print("\n=== EXAMPLE 1: Dataset Design ===\n")

    # Инициализация
    llm_provider = get_llm_provider()
    memory_manager = MemoryManager()  # TODO: proper initialization

    adapter = ResearchTeamAdapter(llm_provider, memory_manager)

    # Запуск исследования
    result = await adapter.invoke_research_team(
        research_question=(
            "Разработать датасет вопросов по алгебре для 7-9 классов "
            "с градацией сложности и аннотацией по knowledge graph концептам, "
            "для обучения модели предсказания mastery level студентов."
        ),
        task_type=ResearchTaskType.DATASET_DESIGN,
        complexity=ResearchComplexity.COMPLEX,
        objectives=[
            "Определить структуру датасета (схема, features, targets)",
            "Разработать таксономию сложности вопросов",
            "Создать annotation guidelines для концептов",
            "Определить процедуры сбора и валидации",
            "Оценить размер датасета для статистической значимости",
        ],
        scope="Алгебра 7-9 класс: уравнения, неравенства, функции, системы",
        constraints=[
            "Датасет должен интегрироваться с Neo4j knowledge graph",
            "Минимум 5000 вопросов для обучения модели",
            "Баланс по сложности и концептам",
            "Аннотация по common misconceptions",
        ],
    )

    print(f"Status: {result['status']}")
    print(f"Quality Score: {result['quality_score']:.2f}")
    print(f"Artifacts: {len(result['artifacts'])}")
    print(f"\nDelivery Package:\n{result['delivery_package']}")


async def example_model_architecture():
    """
    Пример: Разработка нейронной архитектуры для knowledge tracing.

    Задача: Создать модель для предсказания mastery level студента
    по истории его взаимодействий с системой и структуре knowledge graph.
    """
    print("\n=== EXAMPLE 2: Model Architecture Design ===\n")

    llm_provider = get_llm_provider()
    memory_manager = MemoryManager()

    adapter = ResearchTeamAdapter(llm_provider, memory_manager)

    result = await adapter.invoke_research_team(
        research_question=(
            "Разработать нейронную архитектуру для knowledge tracing, "
            "которая предсказывает mastery level студента по каждому концепту "
            "на основе истории ответов и структуры knowledge graph."
        ),
        task_type=ResearchTaskType.MODEL_ARCHITECTURE,
        complexity=ResearchComplexity.COMPLEX,
        objectives=[
            "Спроектировать архитектуру модели (GNN + Transformer или альтернативы)",
            "Обосновать выбор архитектуры теоретически",
            "Определить input/output representations",
            "Оценить computational complexity",
            "Разработать training strategy",
            "Определить evaluation metrics",
        ],
        scope="Knowledge tracing для адаптивной системы обучения",
        constraints=[
            "Real-time inference (<200ms)",
            "Interpretability для учителей",
            "Fairness across demographic groups",
            "Работа с sparse data (новые студенты)",
        ],
    )

    print(f"Status: {result['status']}")
    print(f"Quality Score: {result['quality_score']:.2f}")
    print(f"\nKey Findings: {len(result['findings'])}")
    for finding in result["findings"][:3]:
        print(f"  - {finding.title} (confidence: {finding.confidence})")


async def example_curriculum_design():
    """
    Пример: Дизайн curriculum для алгебры в форме knowledge graph.

    Задача: Создать структуру curriculum по алгебре в виде Neo4j графа
    с prerequisite relationships, difficulty levels, и adaptive pathways.
    """
    print("\n=== EXAMPLE 3: Curriculum Design ===\n")

    llm_provider = get_llm_provider()
    memory_manager = MemoryManager()

    adapter = ResearchTeamAdapter(llm_provider, memory_manager)

    result = await adapter.invoke_research_team(
        research_question=(
            "Спроектировать curriculum по алгебре 7-9 класс в форме "
            "knowledge graph (Neo4j) с явными prerequisite chains, "
            "difficulty progression, и adaptive learning pathways."
        ),
        task_type=ResearchTaskType.CURRICULUM_DESIGN,
        complexity=ResearchComplexity.COMPLEX,
        objectives=[
            "Определить scope and sequence (темы, концепты)",
            "Построить prerequisite dependency graph",
            "Назначить difficulty levels концептам",
            "Разработать main learning pathway",
            "Создать remediation branches для gaps",
            "Спроектировать Neo4j schema",
        ],
        scope="Алгебра 7-9 класс (Common Core aligned)",
        constraints=[
            "Интеграция с существующим Neo4j knowledge base",
            "Поддержка multiple entry points",
            "Explicit prerequisite chains",
            "Mastery-based progression (не linear)",
        ],
    )

    print(f"Status: {result['status']}")
    print(f"Quality Score: {result['quality_score']:.2f}")


async def example_learning_analytics():
    """
    Пример: Анализ эффективности адаптивного алгоритма.

    Задача: Провести learning analytics для оценки эффективности
    текущего адаптивного алгоритма и предложить улучшения.
    """
    print("\n=== EXAMPLE 4: Learning Analytics ===\n")

    llm_provider = get_llm_provider()
    memory_manager = MemoryManager()

    adapter = ResearchTeamAdapter(llm_provider, memory_manager)

    result = await adapter.invoke_research_team(
        research_question=(
            "Провести learning analytics анализ данных студентов за последние "
            "3 месяца для оценки эффективности адаптивного алгоритма подбора "
            "вопросов и предложить data-driven improvements."
        ),
        task_type=ResearchTaskType.LEARNING_ANALYTICS,
        complexity=ResearchComplexity.STANDARD,
        objectives=[
            "Анализировать learning trajectories студентов",
            "Выявить паттерны success и struggle",
            "Оценить эффективность адаптивного алгоритма",
            "Найти bottleneck concepts",
            "Предсказать risk of dropout",
            "Рекомендовать оптимизации",
        ],
        scope="Данные за Q1 2026: 1000 студентов, 50K interactions",
        constraints=[
            "Privacy compliance (GDPR)",
            "Statistical significance required",
            "Fairness analysis across demographics",
        ],
    )

    print(f"Status: {result['status']}")
    print(f"Quality Score: {result['quality_score']:.2f}")


async def example_ab_testing():
    """
    Пример: Дизайн A/B теста для нового scaffolding подхода.

    Задача: Разработать A/B тест для сравнения нового подхода к scaffolding
    (adaptive hints) vs текущего подхода (fixed hints).
    """
    print("\n=== EXAMPLE 5: A/B Testing Design ===\n")

    llm_provider = get_llm_provider()
    memory_manager = MemoryManager()

    adapter = ResearchTeamAdapter(llm_provider, memory_manager)

    result = await adapter.invoke_research_team(
        research_question=(
            "Разработать A/B тест для оценки эффективности adaptive hints "
            "(hints подбираются на основе student model) vs fixed hints "
            "(статичные hints для всех студентов)."
        ),
        task_type=ResearchTaskType.A_B_TESTING,
        complexity=ResearchComplexity.STANDARD,
        objectives=[
            "Формулировать статистические гипотезы",
            "Определить primary и secondary metrics",
            "Рассчитать размер выборки (power analysis)",
            "Разработать randomization strategy",
            "Создать plan анализа результатов",
            "Определить критерии успеха",
        ],
        scope="Math problems, grades 7-9, duration 4 weeks",
        constraints=[
            "Minimum detectable effect: 10% improvement in mastery gain",
            "Significance level α=0.05, power β=0.80",
            "Equal group sizes",
            "Control for confounders (prior ability)",
        ],
    )

    print(f"Status: {result['status']}")
    print(f"Quality Score: {result['quality_score']:.2f}")


async def main():
    """Запуск всех примеров"""
    print("\n" + "=" * 70)
    print("RESEARCH TEAM USAGE EXAMPLES")
    print("=" * 70)

    # Запускаем примеры последовательно
    await example_dataset_design()
    await example_model_architecture()
    await example_curriculum_design()
    await example_learning_analytics()
    await example_ab_testing()

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
