"""
Subject Matter Experts (SME) - Эксперты по предметным областям

SME Math - математика
SME Science - естественные науки
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class SMEMath(ResearchAgent):
    """
    SME Math - эксперт по математике.

    РОЛЬ:
    - Математическая экспертиза
    - Common misconceptions
    - Problem design
    - Concept explanations
    - Curriculum guidance

    КОМПЕТЕНЦИИ:
    1. Deep Math Knowledge (K-12):
       - Arithmetic, Algebra, Geometry
       - Statistics, Probability
       - Pre-calculus, Calculus
       - Common Core Math Standards

    2. Mathematical Pedagogy:
       - Concrete → Representational → Abstract (CRA)
       - Multiple representations
       - Problem-solving strategies
       - Mathematical discourse

    3. Common Misconceptions:
       - Известные ошибки студентов
       - Источники misconceptions
       - Remediation strategies

    4. Problem Design:
       - Graduated difficulty
       - Multiple solution paths
       - Real-world applications
       - Varied problem types

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Struggling students' common errors
    - Prerequisite identification
    - Scaffolded problem sequences
    - Conceptual vs procedural balance
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider, memory_manager, "SME Math",
            "Эксперт по математике",
            ["K-12 Mathematics", "Math Pedagogy", "Problem Design", "Misconceptions", "Common Core Math"],
            ["Content analysis", "Problem creation", "Error analysis", "Concept mapping"]
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        updates: Dict[str, Any] = {"messages": []}
        context = await self.query_knowledge_base(
            f"mathematics pedagogy misconceptions {state.research_question}",
            {"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

КАК ЭКСПЕРТ ПО МАТЕМАТИКЕ:

1. Content Analysis:
   - Math concepts involved
   - Prerequisites needed
   - Common Core standards alignment
   - Conceptual vs procedural balance

2. Common Misconceptions:
   - Typical student errors для этих концептов
   - Sources of misconceptions
   - Diagnostic questions
   - Remediation strategies

3. Problem Design Guidance:
   - Problem types suitable
   - Difficulty progression
   - Multiple representations (visual, symbolic, verbal)
   - Real-world contexts

4. Scaffolding Recommendations:
   - CRA sequence
   - Worked examples
   - Guided practice structure
   - Independence milestones

5. Content Specifications:
   - Vocabulary terms
   - Formulas/procedures
   - Key visualizations
   - Practice problem templates

ФОРМАТ ОТВЕТА (JSON):
{{
  "concepts": ["concept1", "concept2"],
  "prerequisites": [],
  "standards": [],
  "misconceptions": [
    {{"error": "", "source": "", "remediation": ""}}
  ],
  "problem_templates": [],
  "scaffolding": {{
    "concrete": "",
    "representational": "",
    "abstract": ""
  }}
}}
"""

        response = await self.generate_with_llm(system_prompt, user_prompt, 0.5, 3500)
        artifact = await self.create_artifact(
            state, "math_expertise", "Mathematics Content Specifications",
            "Математическая экспертиза от SME Math",
            {"analysis": response, "context": context[:2]},
            {"phase": state.current_phase.value}
        )
        updates["artifacts"] = [artifact]
        updates["messages"].append({"agent": self.agent_name, "message": "Математическая экспертиза завершена"})
        return updates


class SMEMathCritic(ResearchCritic):
    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider, memory_manager, "SME Math Critic",
            ["Math accuracy", "Misconception coverage", "Problem quality"],
            ["Correct mathematics", "Comprehensive misconceptions", "Appropriate difficulty"]
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "SME Math"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}
        review = await self.generate_review(str(artifacts[-1].content), ["Accuracy", "Misconceptions", "Pedagogy"])
        return {**review, "quality_score": self.get_quality_score(review)}


class SMEScience(ResearchAgent):
    """
    SME Science - эксперт по естественным наукам.

    РОЛЬ:
    - Научная экспертиза (Physics, Chemistry, Biology, Earth Science)
    - Inquiry-based learning
    - Experiments и simulations
    - Scientific practices

    КОМПЕТЕНЦИИ:
    1. K-12 Science Content:
       - Physics, Chemistry, Biology
       - Earth/Space Science
       - NGSS Standards

    2. Scientific Practices:
       - Asking questions
       - Planning investigations
       - Analyzing data
       - Constructing explanations
       - Argumentation from evidence

    3. Inquiry-Based Learning:
       - 5E model (Engage, Explore, Explain, Elaborate, Evaluate)
       - Guided vs open inquiry
       - Lab design
       - Safety considerations

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Virtual labs и simulations
    - Scaffolded inquiry
    - Conceptual understanding focus
    - Common science misconceptions
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider, memory_manager, "SME Science",
            "Эксперт по естественным наукам",
            ["K-12 Science", "NGSS", "Inquiry-Based Learning", "Scientific Practices", "Lab Design"],
            ["Content analysis", "Inquiry design", "Misconception analysis", "Lab planning"]
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        updates: Dict[str, Any] = {"messages": []}
        context = await self.query_knowledge_base(
            f"science pedagogy inquiry NGSS {state.research_question}",
            {"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

КАК ЭКСПЕРТ ПО НАУКЕ:

1. Science Content:
   - Core concepts (Disciplinary Core Ideas)
   - Crosscutting Concepts
   - NGSS Standards alignment
   - Prerequisites

2. Scientific Practices:
   - Which practices применимы
   - How to scaffold each practice
   - Assessment of practices

3. Inquiry Design:
   - 5E model application
   - Investigation types (guided/open)
   - Data collection methods
   - Evidence-based reasoning

4. Experiments/Simulations:
   - Virtual lab opportunities
   - Phenomena to explore
   - Variables to manipulate
   - Safety considerations (if physical)

5. Common Misconceptions:
   - Alternative conceptions
   - Naive theories
   - Conceptual change strategies

ФОРМАТ ОТВЕТА (JSON):
{{
  "core_ideas": [],
  "crosscutting_concepts": [],
  "ngss_standards": [],
  "practices": [{{"practice": "", "scaffolding": ""}}],
  "inquiry_design": {{
    "engage": "",
    "explore": "",
    "explain": "",
    "elaborate": "",
    "evaluate": ""
  }},
  "experiments": [{{"type": "", "phenomena": "", "variables": ""}}],
  "misconceptions": [{{"misconception": "", "correction": ""}}]
}}
"""

        response = await self.generate_with_llm(system_prompt, user_prompt, 0.5, 3500)
        artifact = await self.create_artifact(
            state, "science_expertise", "Science Content Specifications",
            "Научная экспертиза от SME Science",
            {"analysis": response, "context": context[:2]},
            {"phase": state.current_phase.value}
        )
        updates["artifacts"] = [artifact]
        updates["messages"].append({"agent": self.agent_name, "message": "Научная экспертиза завершена"})
        return updates


class SMEScienceCritic(ResearchCritic):
    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider, memory_manager, "SME Science Critic",
            ["Science accuracy", "NGSS alignment", "Inquiry quality"],
            ["Correct science", "Standards coverage", "Appropriate practices"]
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "SME Science"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}
        review = await self.generate_review(str(artifacts[-1].content), ["Accuracy", "NGSS", "Inquiry"])
        return {**review, "quality_score": self.get_quality_score(review)}
