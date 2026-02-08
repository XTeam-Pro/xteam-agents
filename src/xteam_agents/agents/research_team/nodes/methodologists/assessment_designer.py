"""
Assessment Designer - Разработчик систем оценивания

Проектирует формативное и суммативное оценивание, rubrics,
adaptive assessment, feedback mechanisms.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class AssessmentDesigner(ResearchAgent):
    """
    Assessment Designer - эксперт по оцениванию.

    РОЛЬ:
    - Дизайн систем оценивания
    - Formative/summative assessment
    - Rubrics и критерии
    - Adaptive assessment
    - Feedback mechanisms

    КОМПЕТЕНЦИИ:
    1. Assessment Theory
       - Formative vs Summative
       - Diagnostic assessment
       - Authentic assessment
       - Portfolio assessment

    2. Psychometrics
       - Validity (content, construct, criterion)
       - Reliability (test-retest, inter-rater)
       - Item analysis (difficulty, discrimination)
       - Classical Test Theory basics

    3. Rubric Design
       - Analytic rubrics
       - Holistic rubrics
       - Single-point rubrics
       - Mastery-based rubrics

    4. Adaptive Assessment
       - Computer Adaptive Testing (CAT)
       - Item Response Theory basics
       - Difficulty calibration
       - Stopping rules

    5. Feedback Design
       - Immediate feedback
       - Elaborated feedback
       - Metacognitive prompts
       - Error-specific hints

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Formative assessment в каждой точке
    - Mastery thresholds для progression
    - Low-stakes assessment (снижение anxiety)
    - Immediate, specific feedback
    - Progress-oriented rubrics
    - Adaptive difficulty adjustment

    МЕТОДЫ РАБОТЫ:
    1. Assessment Blueprint creation
    2. Item/question design
    3. Rubric development
    4. Pilot testing protocol
    5. Item analysis и refinement

    РЕЗУЛЬТАТЫ:
    - Assessment Blueprints
    - Item Banks (specifications)
    - Rubrics (analytic/holistic)
    - Feedback Protocols
    - Validity/Reliability Reports
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Assessment Designer",
            role="Разработчик систем оценивания",
            expertise=[
                "Assessment Theory",
                "Formative Assessment",
                "Summative Assessment",
                "Rubric Design",
                "Psychometrics",
                "Adaptive Assessment",
                "Feedback Design",
                "Item banking",
            ],
            research_methods=[
                "Assessment blueprint design",
                "Item development",
                "Pilot testing",
                "Item analysis",
                "Validity studies",
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Разработка системы оценивания.

        АЛГОРИТМ:
        1. Определение целей assessment
        2. Assessment blueprint (что измеряем, как, когда)
        3. Item/question specifications
        4. Rubric design
        5. Feedback mechanisms
        6. Validity/reliability plan
        """
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"assessment design rubrics feedback {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

РАЗРАБОТАЙТЕ СИСТЕМУ ОЦЕНИВАНИЯ:

1. Assessment Purpose & Goals:
   - Formative (during learning) или Summative (end of unit)?
   - Что измеряем (knowledge, skills, understanding)?
   - Alignment с learning objectives
   - Frequency (continuous, periodic, milestone)

2. Assessment Blueprint:
   - Content areas покрытые
   - Cognitive levels (Bloom's)
   - Item types (MCQ, open-ended, performance)
   - Weighting по важности

3. Item Specifications:
   - Item formats для каждого objective
   - Difficulty range (для adaptive)
   - Примеры items для каждого типа
   - Distractor design (для MCQ)

4. Rubric Design:
   - Type (analytic/holistic/mastery-based)
   - Performance levels (не менее 3-4)
   - Descriptors для каждого level
   - Mastery threshold определение

5. Feedback Mechanisms:
   - Immediate feedback после каждого item?
   - Elaborated feedback (не просто right/wrong)
   - Error-specific hints
   - Metacognitive prompts
   - Next steps recommendations

6. Adaptive Features (для StudyNinja):
   - Difficulty adjustment rules
   - Stopping rules (когда заканчивать)
   - Confidence estimation
   - Mastery level determination

7. Psychometric Considerations:
   - Validity evidence plan
   - Reliability estimation method
   - Bias и fairness checks
   - Pilot testing protocol

ФОРМАТ ОТВЕТА (JSON):
{{
  "assessment_purpose": "",
  "blueprint": {{
    "content_areas": [],
    "cognitive_levels": [],
    "item_types": [],
    "weighting": {{}}
  }},
  "item_specifications": [
    {{"objective": "", "format": "", "difficulty": "", "example": ""}}
  ],
  "rubric": {{
    "type": "",
    "levels": [
      {{"level": "", "score": "", "descriptors": ""}}
    ],
    "mastery_threshold": ""
  }},
  "feedback_protocol": {{
    "timing": "",
    "type": "",
    "elaboration_strategy": "",
    "hints": []
  }},
  "adaptive_features": {{
    "difficulty_adjustment": "",
    "stopping_rules": "",
    "mastery_determination": ""
  }},
  "validity_plan": ["evidence1", "evidence2"],
  "pilot_protocol": ""
}}
"""

        response = await self.generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=4000,
        )

        artifact = await self.create_artifact(
            state=state,
            artifact_type="assessment_design",
            title="Assessment System Design",
            description="Система оценивания от Assessment Designer",
            content={"design": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Система оценивания разработана",
        })

        return updates


class AssessmentDesignerCritic(ResearchCritic):
    """Критик Assessment Designer"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Assessment Designer Critic",
            review_focus=[
                "Assessment validity",
                "Rubric clarity",
                "Feedback quality",
                "Adaptive features",
            ],
            quality_criteria=[
                "Clear assessment goals",
                "Comprehensive blueprint",
                "Well-designed rubrics",
                "Effective feedback",
                "Psychometric soundness",
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "Assessment Designer"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(artifacts[-1].content),
            focus_areas=["Validity", "Rubric quality", "Feedback design"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
