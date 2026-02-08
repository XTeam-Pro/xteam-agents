"""
Annotation Specialist - Специалист по аннотации данных

Управляет процессом аннотации, создает guidelines,
контролирует качество, обеспечивает consistency.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class AnnotationSpecialist(ResearchAgent):
    """
    Annotation Specialist - эксперт по аннотации данных.

    РОЛЬ:
    - Разработка annotation guidelines
    - Обучение аннотаторов
    - Quality control (IAA - Inter-Annotator Agreement)
    - Процессы аннотации
    - Annotation tools setup

    КОМПЕТЕНЦИИ:
    1. Annotation Methodology:
       - Guideline creation
       - Annotator training
       - Pilot studies
       - Iterative refinement

    2. Quality Assurance:
       - Inter-Annotator Agreement (Cohen's Kappa, Krippendorff's Alpha)
       - Gold standard creation
       - Adjudication процессы
       - Continuous monitoring

    3. Annotation Tools:
       - LabelStudio, Prodigy, Doccano
       - Custom tool configuration
       - Workflow optimization
       - UI/UX для аннотаторов

    4. Annotation Types:
       - Classification
       - Named Entity Recognition (NER)
       - Relation extraction
       - Sentiment/Affect
       - Difficulty rating

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Образовательный контент аннотация:
      * Difficulty level
      * Concept tagging
      * Prerequisite identification
      * Misconception labeling
      * Learning objective alignment
    - Knowledge graph node properties
    - Student response coding

    РЕЗУЛЬТАТЫ:
    - Annotation Guidelines (detailed manuals)
    - Annotator Training Materials
    - Quality Control Protocols
    - IAA Reports
    - Annotation Tool Configurations
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Annotation Specialist",
            role="Специалист по аннотации данных",
            expertise=[
                "Annotation Guidelines",
                "Inter-Annotator Agreement",
                "Quality Control",
                "Annotation Tools (LabelStudio, Prodigy)",
                "Crowdsourcing",
                "Educational Content Annotation",
            ],
            research_methods=[
                "Guideline development",
                "Pilot annotation studies",
                "IAA calculation",
                "Adjudication protocols",
                "Tool configuration",
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Разработка процесса аннотации.

        АЛГОРИТМ:
        1. Определение annotation schema
        2. Создание guidelines
        3. Pilot study
        4. Refinement guidelines
        5. Quality control setup
        6. Tool configuration
        """
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"annotation guidelines quality control {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

РАЗРАБОТАЙТЕ ПРОЦЕСС АННОТАЦИИ:

1. Annotation Schema:
   - Что аннотируем (labels, categories, dimensions)
   - Label definitions (четкие, недвусмысленные)
   - Examples для каждого label
   - Edge cases handling

2. Annotation Guidelines:
   - Step-by-step instructions
   - Decision trees для сложных случаев
   - Examples (positive и negative)
   - Common mistakes to avoid
   - When to skip/flag

3. Annotator Training:
   - Training materials (slides, videos)
   - Practice exercises с ответами
   - Qualification test
   - Feedback mechanism

4. Quality Control:
   - Gold standard set creation
   - Inter-Annotator Agreement target (e.g., Kappa > 0.8)
   - Sampling strategy для double annotation
   - Adjudication process (при disagreement)
   - Regular calibration sessions

5. Annotation Tool Setup:
   - Tool choice (LabelStudio/Prodigy/Custom)
   - UI configuration
   - Keyboard shortcuts
   - Progress tracking
   - Export format

6. Workflow:
   - Assignment strategy (random/balanced)
   - Review stages
   - Feedback loops
   - Version control (guidelines)

7. Monitoring & Improvement:
   - IAA tracking over time
   - Guideline ambiguities identification
   - Annotator performance monitoring
   - Continuous refinement

СПЕЦИФИЧНО ДЛЯ ОБРАЗОВАТЕЛЬНОГО КОНТЕНТА:
- Difficulty rating (subjective, need clear rubric)
- Concept tagging (knowledge graph alignment)
- Prerequisite identification (need domain expertise)
- Misconception labeling (examples critical)

ФОРМАТ ОТВЕТА (JSON):
{{
  "annotation_schema": {{
    "labels": [{{"label": "", "definition": "", "examples": []}}],
    "edge_cases": []
  }},
  "guidelines_outline": {{
    "sections": [],
    "decision_trees": [],
    "examples": []
  }},
  "training_plan": {{
    "materials": [],
    "exercises": [],
    "qualification": ""
  }},
  "quality_control": {{
    "iaa_target": "",
    "sampling": "",
    "adjudication": ""
  }},
  "tool_recommendation": {{
    "tool": "",
    "configuration": {{}}
  }},
  "workflow": {{
    "stages": [],
    "review": ""
  }},
  "monitoring": {{
    "metrics": [],
    "improvement_triggers": []
  }}
}}
"""

        response = await self.generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
            max_tokens=4000,
        )

        artifact = await self.create_artifact(
            state=state,
            artifact_type="annotation_process",
            title="Annotation Process Design",
            description="Процесс аннотации от Annotation Specialist",
            content={"process": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Процесс аннотации разработан",
        })

        return updates


class AnnotationSpecialistCritic(ResearchCritic):
    """Критик Annotation Specialist"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Annotation Specialist Critic",
            review_focus=[
                "Guideline clarity",
                "Quality control rigor",
                "Tool appropriateness",
                "Workflow feasibility",
            ],
            quality_criteria=[
                "Clear, unambiguous guidelines",
                "Comprehensive quality control",
                "Appropriate tool selection",
                "Practical workflow",
                "Adequate training plan",
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "Annotation Specialist"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(artifacts[-1].content),
            focus_areas=["Guidelines clarity", "Quality control", "Workflow"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
