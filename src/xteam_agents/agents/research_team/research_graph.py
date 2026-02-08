"""
Research Team Graph - LangGraph для координации исследовательской команды

Координирует работу ученых, методистов и команды контента.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from xteam_agents.agents.research_team.research_state import (
    ResearchState,
    ResearchTaskType,
    ResearchComplexity,
    ResearchPhase,
)
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager

# Импорт всех агентов
from xteam_agents.agents.research_team.nodes.scientists.chief_scientist import (
    ChiefScientist,
    ChiefScientistCritic,
)
from xteam_agents.agents.research_team.nodes.scientists.data_scientist import (
    DataScientist,
    DataScientistCritic,
)
from xteam_agents.agents.research_team.nodes.scientists.ml_researcher import (
    MLResearcher,
    MLResearcherCritic,
)
from xteam_agents.agents.research_team.nodes.scientists.cognitive_scientist import (
    CognitiveScientist,
    CognitiveScientistCritic,
)
from xteam_agents.agents.research_team.nodes.scientists.pedagogical_researcher import (
    PedagogicalResearcher,
    PedagogicalResearcherCritic,
)
from xteam_agents.agents.research_team.nodes.methodologists.curriculum_designer import (
    CurriculumDesigner,
    CurriculumDesignerCritic,
)
from xteam_agents.agents.research_team.nodes.content_team.dataset_engineer import (
    DatasetEngineer,
    DatasetEngineerCritic,
)


class ResearchTeamOrchestrator:
    """
    Orchestrator для исследовательской команды.

    РОЛЬ:
    - Классификация исследовательских задач
    - Маршрутизация к нужным агентам
    - Координация multi-agent collaboration
    - Интеграция результатов
    - Quality assurance через critics

    WORKFLOW:
    1. Классификация задачи (task_type, complexity)
    2. Инициализация (Chief Scientist формирует стратегию)
    3. Параллельная работа специалистов
    4. Peer review от critics
    5. Интеграция результатов
    6. Финализация и передача в разработку
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager

        # Инициализация всех агентов
        self.chief_scientist = ChiefScientist(llm_provider, memory_manager)
        self.chief_scientist_critic = ChiefScientistCritic(llm_provider, memory_manager)

        self.data_scientist = DataScientist(llm_provider, memory_manager)
        self.data_scientist_critic = DataScientistCritic(llm_provider, memory_manager)

        self.ml_researcher = MLResearcher(llm_provider, memory_manager)
        self.ml_researcher_critic = MLResearcherCritic(llm_provider, memory_manager)

        self.cognitive_scientist = CognitiveScientist(llm_provider, memory_manager)
        self.cognitive_scientist_critic = CognitiveScientistCritic(llm_provider, memory_manager)

        self.pedagogical_researcher = PedagogicalResearcher(llm_provider, memory_manager)
        self.pedagogical_researcher_critic = PedagogicalResearcherCritic(llm_provider, memory_manager)

        self.curriculum_designer = CurriculumDesigner(llm_provider, memory_manager)
        self.curriculum_designer_critic = CurriculumDesignerCritic(llm_provider, memory_manager)

        self.dataset_engineer = DatasetEngineer(llm_provider, memory_manager)
        self.dataset_engineer_critic = DatasetEngineerCritic(llm_provider, memory_manager)

    async def classify_task(self, state: ResearchState) -> Dict[str, Any]:
        """
        Классификация исследовательской задачи.

        Определяет:
        - Тип задачи (ResearchTaskType)
        - Сложность (ResearchComplexity)
        - Необходимых агентов
        """
        system_prompt = """Вы - классификатор исследовательских задач для научной команды.

Проанализируйте запрос и определите:
1. Тип задачи (dataset_design, model_architecture, curriculum_design, etc.)
2. Сложность (exploratory, standard, complex, critical)
3. Какие агенты нужны для выполнения

АГЕНТЫ:
- Chief Scientist: координация, стратегия (всегда нужен)
- Data Scientist: датасеты, статистика, аналитика
- ML Researcher: нейронные модели, обучение, оптимизация
- Cognitive Scientist: когнитивные аспекты обучения
- Pedagogical Researcher: педагогические методы
- Curriculum Designer: структура curriculum
- Dataset Engineer: инженерия датасетов
"""

        user_prompt = f"""
ЗАПРОС: {state.research_question}

КОНТЕКСТ:
Область: {state.scope}
Ограничения: {', '.join(state.constraints)}

Определите тип, сложность и нужных агентов в JSON:
{{
  "task_type": "тип",
  "complexity": "сложность",
  "required_agents": ["agent1", "agent2"],
  "rationale": "обоснование"
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.llm_provider.generate(messages=messages, temperature=0.3, max_tokens=500)

        # TODO: Парсинг JSON
        return {
            "messages": [
                {
                    "agent": "Orchestrator",
                    "message": "Задача классифицирована",
                    "content": response.get("content", ""),
                }
            ],
        }

    async def integrate_results(self, state: ResearchState) -> Dict[str, Any]:
        """
        Интеграция результатов всех агентов.

        Собирает артефакты, проводит synthesis, формирует итоговый отчет.
        """
        system_prompt = """Вы - Research Integration Specialist.

Ваша задача - интегрировать результаты всех исследователей в целостный отчет
с конкретными рекомендациями для команды разработки.
"""

        # Собираем все артефакты
        artifacts_summary = "\n\n".join(
            [
                f"=== {a.created_by}: {a.title} ===\n{str(a.content)[:300]}..."
                for a in state.artifacts
            ]
        )

        findings_summary = "\n".join(
            [f"- {f.title} (confidence: {f.confidence})" for f in state.findings]
        )

        user_prompt = f"""
ИССЛЕДОВАТЕЛЬСКИЙ ВОПРОС: {state.research_question}

РЕЗУЛЬТАТЫ ОТ АГЕНТОВ:
{artifacts_summary}

КЛЮЧЕВЫЕ НАХОДКИ:
{findings_summary}

СОЗДАЙТЕ ИНТЕГРИРОВАННЫЙ ОТЧЕТ:

1. Executive Summary
   - Главные выводы
   - Рекомендации высокого уровня

2. Detailed Findings
   - По каждому аспекту (data, models, pedagogy, etc.)
   - Synthesis между агентами

3. Implementation Recommendations
   - Конкретные задачи для dev team
   - Приоритизация
   - Dependencies

4. Deliverables Package
   - Датасеты (specifications)
   - Модели (architectures)
   - Документация
   - Code artifacts

5. Next Steps
   - Follow-up research
   - Evaluation plan
   - Iteration strategy

ФОРМАТ: JSON
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.llm_provider.generate(messages=messages, temperature=0.5, max_tokens=4000)

        return {
            "delivery_package": {
                "integrated_report": response.get("content", ""),
                "artifacts_count": len(state.artifacts),
                "findings_count": len(state.findings),
            },
            "current_phase": ResearchPhase.DELIVERY,
            "status": "completed",
        }


def create_research_team_graph(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
) -> StateGraph:
    """
    Создание LangGraph для исследовательской команды.

    АРХИТЕКТУРА ГРАФА:

    START
      ↓
    classify_task (Orchestrator классифицирует)
      ↓
    chief_scientist_node (Формирование стратегии)
      ↓
    route_to_specialists
      ├→ data_scientist_node ────┐
      ├→ ml_researcher_node ─────┤
      ├→ cognitive_scientist_node ┤
      ├→ pedagogical_researcher_node ┤
      └→ curriculum_designer_node ┤
                                  ↓
                            gather_results
                                  ↓
                            peer_review (Critics)
                                  ↓
                            integrate_results
                                  ↓
                               END

    Returns:
        Compiled StateGraph
    """
    orchestrator = ResearchTeamOrchestrator(llm_provider, memory_manager)

    # Создаем граф
    workflow = StateGraph(ResearchState)

    # Добавляем ноды

    # 1. Классификация задачи
    async def classify_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.classify_task(state)

    workflow.add_node("classify", classify_node)

    # 2. Chief Scientist формирует стратегию
    async def chief_scientist_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.chief_scientist.conduct_research(state)

    workflow.add_node("chief_scientist", chief_scientist_node)

    # 3. Специалисты работают параллельно (в реальности выполняются последовательно)
    async def data_scientist_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.data_scientist.conduct_research(state)

    async def ml_researcher_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.ml_researcher.conduct_research(state)

    async def cognitive_scientist_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.cognitive_scientist.conduct_research(state)

    async def pedagogical_researcher_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.pedagogical_researcher.conduct_research(state)

    async def curriculum_designer_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.curriculum_designer.conduct_research(state)

    async def dataset_engineer_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.dataset_engineer.conduct_research(state)

    workflow.add_node("data_scientist", data_scientist_node)
    workflow.add_node("ml_researcher", ml_researcher_node)
    workflow.add_node("cognitive_scientist", cognitive_scientist_node)
    workflow.add_node("pedagogical_researcher", pedagogical_researcher_node)
    workflow.add_node("curriculum_designer", curriculum_designer_node)
    workflow.add_node("dataset_engineer", dataset_engineer_node)

    # 4. Peer Review
    async def peer_review_node(state: ResearchState) -> Dict[str, Any]:
        """Критики проводят рецензию"""
        reviews = []

        # Chief Scientist Critic
        review = await orchestrator.chief_scientist_critic.review_research(state)
        reviews.append(review)

        # Data Scientist Critic
        review = await orchestrator.data_scientist_critic.review_research(state)
        reviews.append(review)

        # ML Researcher Critic
        review = await orchestrator.ml_researcher_critic.review_research(state)
        reviews.append(review)

        # Другие критики...

        return {"peer_reviews": reviews, "quality_score": sum(r.get("quality_score", 0.5) for r in reviews) / len(reviews)}

    workflow.add_node("peer_review", peer_review_node)

    # 5. Интеграция результатов
    async def integrate_node(state: ResearchState) -> Dict[str, Any]:
        return await orchestrator.integrate_results(state)

    workflow.add_node("integrate", integrate_node)

    # Определяем edges

    # START → classify
    workflow.set_entry_point("classify")

    # classify → chief_scientist
    workflow.add_edge("classify", "chief_scientist")

    # chief_scientist → specialists (последовательно для простоты)
    workflow.add_edge("chief_scientist", "data_scientist")
    workflow.add_edge("data_scientist", "ml_researcher")
    workflow.add_edge("ml_researcher", "cognitive_scientist")
    workflow.add_edge("cognitive_scientist", "pedagogical_researcher")
    workflow.add_edge("pedagogical_researcher", "curriculum_designer")
    workflow.add_edge("curriculum_designer", "dataset_engineer")

    # dataset_engineer → peer_review
    workflow.add_edge("dataset_engineer", "peer_review")

    # peer_review → integrate
    workflow.add_edge("peer_review", "integrate")

    # integrate → END
    workflow.add_edge("integrate", END)

    return workflow.compile()
