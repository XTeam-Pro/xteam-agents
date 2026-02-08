"""
Curriculum Designer - Разработчик учебных программ

Проектирует целостные учебные программы, последовательности тем,
интеграцию с knowledge graph, learning pathways.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class CurriculumDesigner(ResearchAgent):
    """
    Curriculum Designer - архитектор учебных программ.

    РОЛЬ:
    - Дизайн curriculum scope and sequence
    - Интеграция с knowledge graph (Neo4j)
    - Определение learning pathways
    - Prerequisite mapping
    - Pacing и progression design

    КОМПЕТЕНЦИИ:
    1. Curriculum Theory: Scope and sequence, Alignment (standards),
       Backward design, Vertical/horizontal alignment
    2. Knowledge Structure: Concept networks, Prerequisites,
       Difficulty progression, Cognitive complexity
    3. Graph-based Curriculum: Knowledge graph design,
       Adaptive pathways, Personalized sequences
    4. Standards Alignment: Common Core, State standards, IB/AP

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Curriculum в форме knowledge graph (Neo4j)
    - Adaptive pathways для struggling students
    - Mastery-based progression (не linear)
    - Explicit prerequisite chains
    - Multiple entry points и remediation paths

    РЕЗУЛЬТАТЫ:
    - Curriculum Maps (graph structure)
    - Learning Pathway Designs
    - Prerequisite Dependency Graphs
    - Scope and Sequence Documents
    - Standards Alignment Matrices
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Curriculum Designer",
            role="Архитектор учебных программ и Knowledge Graph Designer",
            expertise=[
                "Curriculum Design", "Scope and Sequence", "Knowledge Graphs",
                "Prerequisite Mapping", "Learning Pathways", "Standards Alignment",
                "Backward Design", "Competency Frameworks"
            ],
            research_methods=[
                "Curriculum mapping", "Task analysis", "Expert interviews",
                "Standards analysis", "Concept network analysis"
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Разработка структуры curriculum.

        АЛГОРИТМ:
        1. Анализ standards и learning goals
        2. Concept extraction и organization
        3. Prerequisite identification
        4. Difficulty assignment
        5. Pathway design (linear + adaptive branches)
        6. Neo4j graph schema design
        """
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"curriculum design knowledge graph {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

РАЗРАБОТАЙТЕ CURRICULUM STRUCTURE:

1. Scope (что включено):
   - Major topics/units
   - Key concepts per topic
   - Skills и competencies
   - Estimated mastery hours

2. Sequence (порядок):
   - Prerequisite relationships
   - Difficulty progression
   - Logical flow
   - Spiral curriculum elements

3. Knowledge Graph Design (для Neo4j):
   - Node types (Concept, Topic, Skill, Standard)
   - Relationship types (PREREQUISITE, PART_OF, REQUIRES, SUPPORTS)
   - Properties (difficulty, estimated_time, mastery_threshold)
   - Graph structure rationale

4. Learning Pathways:
   - Main pathway (standard progression)
   - Remediation branches (для gaps)
   - Acceleration paths (для ready students)
   - Entry points assessment

5. Standards Alignment:
   - Mapping к educational standards
   - Coverage analysis
   - Gap identification

ФОРМАТ ОТВЕТА (JSON):
{{
  "curriculum_overview": "Общее описание",
  "scope": [{{"topic": "", "concepts": [], "skills": [], "hours": ""}}],
  "neo4j_schema": {{
    "node_types": [],
    "relationship_types": [],
    "properties": {{}},
    "example_cypher": ""
  }},
  "prerequisite_graph": [{{"concept": "", "prerequisites": [], "difficulty": ""}}],
  "pathways": {{
    "main": [],
    "remediation": [],
    "acceleration": []
  }},
  "standards_alignment": [{{"standard": "", "concepts": []}}]
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
            artifact_type="curriculum_design",
            title="Curriculum Structure Design",
            description="Структура учебной программы от Curriculum Designer",
            content={"design": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Разработана структура curriculum",
        })

        return updates


class CurriculumDesignerCritic(ResearchCritic):
    """Критик Curriculum Designer"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Curriculum Designer Critic",
            review_focus=[
                "Логичность последовательности",
                "Полнота prerequisite chains",
                "Standards alignment",
                "Graph structure validity"
            ],
            quality_criteria=[
                "Coherent scope", "Logical sequence",
                "Clear prerequisites", "Appropriate difficulty progression"
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "Curriculum Designer"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(artifacts[-1].content),
            focus_areas=["Sequence logic", "Prerequisite completeness", "Graph design"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
