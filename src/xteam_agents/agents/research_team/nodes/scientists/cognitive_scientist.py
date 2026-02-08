"""
Cognitive Scientist - Когнитивный психолог

Исследует когнитивные процессы обучения, memory formation,
attention mechanisms, cognitive load, metacognition.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class CognitiveScientist(ResearchAgent):
    """
    Cognitive Scientist - специалист по когнитивным процессам обучения.

    РОЛЬ:
    - Исследование когнитивных процессов при обучении
    - Оптимизация cognitive load
    - Дизайн для memory retention
    - Изучение attention и motivation
    - Metacognitive strategies

    КОМПЕТЕНЦИИ:
    1. Теория обучения: Working memory, Long-term memory, Schema theory,
       Cognitive Load Theory, Dual coding theory
    2. Attention & Focus: Divided attention, Selective attention, Sustained attention
    3. Memory: Encoding strategies, Retrieval practice, Spacing effects, Interleaving
    4. Metacognition: Self-monitoring, Self-regulation, Growth mindset
    5. Motivation: Intrinsic/extrinsic, Self-efficacy, Goal theory

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Оптимизация для struggling students (overloaded cognitive system)
    - Снижение cognitive load в адаптивной системе
    - Дизайн "small wins" для confidence building
    - Spacing и interleaving в knowledge graph
    - Metacognitive prompts в AI tutor

    РЕЗУЛЬТАТЫ:
    - Cognitive Load Analysis Reports
    - Memory Retention Strategies
    - Attention Design Guidelines
    - Metacognitive Intervention Plans
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Cognitive Scientist",
            role="Когнитивный психолог и Learning Science эксперт",
            expertise=[
                "Cognitive Load Theory", "Memory Systems", "Attention Mechanisms",
                "Schema Theory", "Metacognition", "Self-Regulated Learning",
                "Working Memory", "Knowledge Representation", "Transfer of Learning"
            ],
            research_methods=[
                "Cognitive Task Analysis", "Think-aloud protocols",
                "Eye-tracking studies", "Cognitive modeling",
                "Learning trajectory analysis"
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Анализ когнитивных аспектов образовательной задачи.

        ФОКУСЫ АНАЛИЗА:
        1. Cognitive Load - измерение и оптимизация
        2. Memory Systems - стратегии для retention
        3. Attention Design - поддержание фокуса
        4. Metacognitive Support - развитие self-regulation
        5. Motivation Psychology - intrinsic motivation через mastery
        """
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"cognitive psychology learning science {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

АНАЛИЗИРУЙТЕ КОГНИТИВНЫЕ АСПЕКТЫ:
1. Cognitive Load:
   - Intrinsic load (сложность материала)
   - Extraneous load (дизайн интерфейса, отвлечения)
   - Germane load (построение схем)
   - Рекомендации по снижению нагрузки

2. Memory Optimization:
   - Encoding strategies (dual coding, elaboration)
   - Retrieval practice opportunities
   - Spacing intervals
   - Interleaving стратегии

3. Attention & Engagement:
   - Факторы sustained attention
   - Минимизация divided attention
   - Motivation triggers

4. Metacognitive Support:
   - Self-monitoring prompts
   - Feedback для calibration
   - Goal-setting mechanisms

ОСОБЫЙ ФОКУС ДЛЯ STRUGGLING STUDENTS:
- Они часто имеют overloaded working memory
- Низкая self-efficacy и motivation
- Недостаток metacognitive skills
- Нужны small, clear wins для confidence

ФОРМАТ ОТВЕТА (JSON):
{{
  "cognitive_load_analysis": {{"intrinsic": "", "extraneous": "", "recommendations": []}},
  "memory_strategies": ["strategy1", "strategy2"],
  "attention_design": ["guideline1", "guideline2"],
  "metacognitive_interventions": ["intervention1", "intervention2"],
  "motivation_factors": ["factor1", "factor2"],
  "evidence_base": ["research1", "research2"]
}}
"""

        response = await self.generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=3500,
        )

        artifact = await self.create_artifact(
            state=state,
            artifact_type="cognitive_analysis",
            title="Cognitive Analysis Report",
            description="Анализ когнитивных аспектов от Cognitive Scientist",
            content={"analysis": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Завершен когнитивный анализ",
            "summary": response[:200],
        })

        return updates


class CognitiveScientistCritic(ResearchCritic):
    """Критик Cognitive Scientist - валидация когнитивных принципов"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Cognitive Scientist Critic",
            review_focus=[
                "Соответствие cognitive science principles",
                "Evidence-based recommendations",
                "Учет individual differences"
            ],
            quality_criteria=[
                "Опора на исследования",
                "Практическая применимость",
                "Учет context struggling students"
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        cog_artifacts = [a for a in state.artifacts if a.created_by == "Cognitive Scientist"]
        if not cog_artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(cog_artifacts[-1].content),
            focus_areas=["Evidence base", "Cognitive theory alignment", "Practical applicability"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
