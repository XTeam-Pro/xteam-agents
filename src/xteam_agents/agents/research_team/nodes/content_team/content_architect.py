"""
Content Architect - Архитектор образовательного контента

Разрабатывает стратегию контента, структуру, стандарты качества,
content taxonomy, metadata schemas.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class ContentArchitect(ResearchAgent):
    """
    Content Architect - архитектор образовательного контента.

    РОЛЬ:
    - Стратегия разработки контента
    - Content taxonomy design
    - Metadata schemas
    - Quality standards
    - Content organization

    КОМПЕТЕНЦИИ:
    1. Content Strategy
       - Content planning
       - Editorial calendar
       - Resource allocation
       - Priority setting

    2. Taxonomy & Ontology
       - Content classification
       - Tag systems
       - Hierarchies
       - Relationships

    3. Metadata Design
       - Dublin Core
       - Learning Object Metadata (LOM)
       - Custom schemas
       - Search optimization

    4. Quality Standards
       - Content guidelines
       - Review processes
       - Version control
       - Accessibility (WCAG)

    5. Content Management
       - CMS architecture
       - Workflow design
       - Content lifecycle
       - Reusability patterns

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Integration с Neo4j knowledge graph
    - Content aligned с mastery progression
    - Metadata для adaptive selection
    - Multi-modal content (text, video, interactive)
    - Accessibility для diverse learners

    РЕЗУЛЬТАТЫ:
    - Content Strategy Documents
    - Taxonomy Schemas
    - Metadata Standards
    - Quality Guidelines
    - Content Architecture Diagrams
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Content Architect",
            role="Архитектор образовательного контента",
            expertise=[
                "Content Strategy",
                "Taxonomy Design",
                "Metadata Schemas",
                "Quality Standards",
                "Content Management",
                "Information Architecture",
                "Accessibility (WCAG)",
            ],
            research_methods=[
                "Content audit",
                "Taxonomy development",
                "Metadata schema design",
                "Quality framework creation",
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """Разработка архитектуры контента"""
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"content architecture taxonomy metadata {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

РАЗРАБОТАЙТЕ АРХИТЕКТУРУ КОНТЕНТА:

1. Content Taxonomy:
   - Hierarchical structure (subject → topic → concept)
   - Tag system (difficulty, type, format)
   - Relationships (prerequisite, related, alternative)
   - Neo4j graph integration

2. Metadata Schema:
   - Core metadata (title, description, author, date)
   - Educational metadata (grade, subject, standards)
   - Technical metadata (format, duration, language)
   - Adaptive metadata (difficulty, mastery_level)

3. Content Types:
   - Instruction (text, video, animation)
   - Practice (questions, exercises, simulations)
   - Assessment (formative, summative)
   - Support (hints, explanations, worked examples)

4. Quality Standards:
   - Accuracy criteria
   - Pedagogical guidelines
   - Accessibility requirements (WCAG 2.1 AA)
   - Technical specifications

5. Content Workflow:
   - Creation process
   - Review stages
   - Approval gates
   - Version control
   - Update triggers

ФОРМАТ ОТВЕТА (JSON):
{{
  "content_taxonomy": {{
    "structure": {{}},
    "tag_system": [],
    "relationships": []
  }},
  "metadata_schema": {{
    "core": [],
    "educational": [],
    "technical": [],
    "adaptive": []
  }},
  "content_types": [
    {{"type": "", "purpose": "", "specifications": ""}}
  ],
  "quality_standards": {{
    "accuracy": [],
    "pedagogy": [],
    "accessibility": [],
    "technical": []
  }},
  "workflow": {{
    "stages": [],
    "roles": [],
    "tools": []
  }}
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
            artifact_type="content_architecture",
            title="Content Architecture Design",
            description="Архитектура контента от Content Architect",
            content={"architecture": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({"agent": self.agent_name, "message": "Архитектура контента разработана"})
        return updates


class ContentArchitectCritic(ResearchCritic):
    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider, memory_manager, "Content Architect Critic",
            ["Taxonomy completeness", "Metadata schema quality", "Workflow feasibility"],
            ["Clear taxonomy", "Comprehensive metadata", "Practical workflow"]
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "Content Architect"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}
        review = await self.generate_review(str(artifacts[-1].content), ["Taxonomy", "Metadata", "Standards"])
        return {**review, "quality_score": self.get_quality_score(review)}
