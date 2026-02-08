"""
Lead Methodologist - Руководитель методической работы

Координирует всю методическую работу команды, обеспечивает согласованность
подходов, интегрирует результаты методистов.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class LeadMethodologist(ResearchAgent):
    """
    Lead Methodologist - главный методист команды.

    РОЛЬ:
    - Координация методической работы
    - Обеспечение согласованности подходов
    - Интеграция результатов методистов
    - Standards alignment
    - Quality assurance методик

    КОМПЕТЕНЦИИ:
    1. Методическое руководство
       - Разработка методических стандартов
       - Координация работы методистов
       - Контроль качества методик
       - Обеспечение согласованности

    2. Educational Standards
       - Common Core State Standards
       - NGSS (Science)
       - State standards
       - International curricula (IB, Cambridge)

    3. Evidence-based Education
       - Research-to-practice translation
       - Evidence synthesis
       - Best practices identification
       - Effectiveness evaluation

    4. Quality Assurance
       - Методические чек-листы
       - Peer review процессы
       - Continuous improvement
       - Documentation standards

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Alignment с vision struggling students
    - Mastery-based методики
    - Adaptive learning coordination
    - Progress visibility standards
    - Motivation через small wins

    МЕТОДЫ РАБОТЫ:
    1. Координация методической команды
    2. Обеспечение alignment со standards
    3. Интеграция методических подходов
    4. Quality control

    РЕЗУЛЬТАТЫ:
    - Methodological Framework Documents
    - Standards Alignment Reports
    - Quality Assurance Checklists
    - Integrated Methodological Recommendations
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Lead Methodologist",
            role="Руководитель методической работы и координатор",
            expertise=[
                "Методическая координация",
                "Educational Standards (Common Core, NGSS)",
                "Evidence-based Education",
                "Quality Assurance",
                "Instructional leadership",
                "Curriculum alignment",
                "Best practices synthesis",
            ],
            research_methods=[
                "Standards alignment analysis",
                "Methodological integration",
                "Quality assurance protocols",
                "Evidence synthesis",
                "Peer review coordination",
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Координация методической работы.

        АЛГОРИТМ:
        1. Анализ требований к методике
        2. Координация работы методистов
        3. Обеспечение standards alignment
        4. Интеграция методических подходов
        5. Quality assurance
        6. Формирование рекомендаций
        """
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"educational standards best practices {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

КООРДИНИРУЙТЕ МЕТОДИЧЕСКУЮ РАБОТУ:

1. Standards Alignment:
   - Определите релевантные educational standards
   - Common Core State Standards mapping
   - State/National curriculum alignment
   - Competency frameworks

2. Methodological Framework:
   - Координация Curriculum Designer, Assessment Designer, Adaptive Learning Specialist
   - Обеспечение согласованности подходов
   - Integration points между методиками
   - Unified pedagogical philosophy

3. Evidence Base:
   - Research evidence для каждого подхода
   - Best practices identification
   - Success metrics from literature
   - Implementation guidelines

4. Quality Standards:
   - Criteria для оценки методик
   - Review protocols
   - Documentation requirements
   - Continuous improvement plan

5. StudyNinja Alignment:
   - Фокус на struggling students
   - Mastery-based progression
   - Progress visibility (1-2 days)
   - Small wins design
   - Motivation через success

ФОРМАТ ОТВЕТА (JSON):
{{
  "standards_alignment": {{
    "common_core": [],
    "state_standards": [],
    "competencies": []
  }},
  "methodological_framework": {{
    "philosophy": "",
    "core_principles": [],
    "integration_points": []
  }},
  "evidence_base": [
    {{"practice": "", "evidence": "", "effectiveness": ""}}
  ],
  "quality_standards": {{
    "criteria": [],
    "review_protocols": [],
    "documentation_requirements": []
  }},
  "recommendations": ["recommendation1", "recommendation2"]
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
            artifact_type="methodological_framework",
            title="Methodological Framework and Coordination",
            description="Методологический фреймворк от Lead Methodologist",
            content={"framework": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Координация методической работы завершена",
        })

        return updates


class LeadMethodologistCritic(ResearchCritic):
    """Критик Lead Methodologist"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Lead Methodologist Critic",
            review_focus=[
                "Standards alignment quality",
                "Methodological coherence",
                "Evidence base strength",
                "Integration completeness",
            ],
            quality_criteria=[
                "Comprehensive standards coverage",
                "Clear methodological framework",
                "Strong evidence base",
                "Practical implementability",
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "Lead Methodologist"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(artifacts[-1].content),
            focus_areas=["Standards alignment", "Methodological coherence", "Evidence quality"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
