"""
Pedagogical Researcher - Педагог-исследователь

Исследует педагогические методы, instructional design,
формирует образовательные стратегии, оценивает эффективность.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class PedagogicalResearcher(ResearchAgent):
    """
    Pedagogical Researcher - эксперт по педагогике и instructional design.

    РОЛЬ:
    - Исследование педагогических методов
    - Разработка instructional strategies
    - Оценка эффективности обучения
    - Адаптация методик для struggling students
    - Дизайн scaffolding и differentiation

    КОМПЕТЕНЦИИ:
    1. Педагогические теории: Constructivism, Socio-cultural theory,
       Zone of Proximal Development, Scaffolding, Direct instruction
    2. Instructional Design: ADDIE, Backwards design, UbD, Bloom's taxonomy
    3. Assessment: Formative/summative, Authentic assessment, Rubrics
    4. Differentiation: Tiered instruction, Flexible grouping, UDL
    5. Adaptive Teaching: Personalization, Mastery learning, Competency-based

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Pedagogy для struggling students (scaffolding, success-oriented)
    - Mastery-based progression
    - Formative assessment в каждой точке
    - "Small wins" instructional design
    - Adaptive scaffolding через AI

    РЕЗУЛЬТАТЫ:
    - Instructional Design Frameworks
    - Assessment Design Documents
    - Scaffolding Strategies
    - Effectiveness Evaluation Reports
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Pedagogical Researcher",
            role="Педагог-исследователь и Instructional Design эксперт",
            expertise=[
                "Instructional Design", "Pedagogy", "Assessment Design",
                "Scaffolding", "Differentiation", "Mastery Learning",
                "Formative Assessment", "Adaptive Teaching", "UDL"
            ],
            research_methods=[
                "Instructional design models", "Classroom observations",
                "Teacher interviews", "Student performance analysis",
                "Quasi-experimental studies"
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Разработка педагогических стратегий и оценка эффективности.

        АЛГОРИТМ:
        1. Анализ learning objectives
        2. Дизайн instructional sequence
        3. Scaffolding strategies
        4. Assessment design
        5. Differentiation approaches
        6. Evaluation metrics
        """
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"pedagogy instructional design teaching methods {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

РАЗРАБОТАЙТЕ ПЕДАГОГИЧЕСКИЙ ПОДХОД:

1. Learning Objectives (на основе Bloom's taxonomy):
   - Knowledge
   - Comprehension
   - Application
   - Analysis
   - Synthesis
   - Evaluation

2. Instructional Sequence:
   - Warm-up/Hook
   - Direct instruction phases
   - Guided practice
   - Independent practice
   - Assessment checkpoints

3. Scaffolding Strategies:
   - Initial support level
   - Fading plan
   - Prompts и hints
   - Worked examples

4. Differentiation:
   - For struggling students (additional scaffolding)
   - For advanced students (extension)
   - Multiple modalities (visual, auditory, kinesthetic)

5. Assessment Design:
   - Formative assessment points
   - Success criteria
   - Feedback mechanisms
   - Mastery thresholds

6. Effectiveness Metrics:
   - Learning gains
   - Time to mastery
   - Retention rates
   - Transfer measures

КРИТИЧНЫЙ ФОКУС:
- Struggling students нужны clear, structured pathways
- Mastery-based (не time-based)
- Immediate, specific feedback
- Visible progress indicators
- Low-stakes formative assessment

ФОРМАТ ОТВЕТА (JSON):
{{
  "learning_objectives": [{{"level": "Bloom level", "objective": ""}}],
  "instructional_sequence": [{{"phase": "", "activities": [], "duration": ""}}],
  "scaffolding_plan": {{"initial_support": "", "fading_strategy": "", "prompts": []}},
  "differentiation_strategies": {{"struggling": [], "advanced": []}},
  "assessment_design": {{"formative": [], "summative": [], "mastery_criteria": ""}},
  "effectiveness_metrics": ["metric1", "metric2"],
  "implementation_guidelines": ["guideline1", "guideline2"]
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
            artifact_type="pedagogical_design",
            title="Pedagogical Strategy Document",
            description="Педагогическая стратегия от Pedagogical Researcher",
            content={"design": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Разработана педагогическая стратегия",
            "summary": response[:200],
        })

        return updates


class PedagogicalResearcherCritic(ResearchCritic):
    """Критик Pedagogical Researcher - валидация педагогических методов"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Pedagogical Researcher Critic",
            review_focus=[
                "Педагогическая обоснованность",
                "Alignment with learning objectives",
                "Scaffolding adequacy",
                "Assessment validity"
            ],
            quality_criteria=[
                "Evidence-based practices",
                "Feasibility for implementation",
                "Differentiation quality",
                "Assessment alignment"
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        ped_artifacts = [a for a in state.artifacts if a.created_by == "Pedagogical Researcher"]
        if not ped_artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(ped_artifacts[-1].content),
            focus_areas=["Pedagogical soundness", "Scaffolding design", "Assessment quality"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
