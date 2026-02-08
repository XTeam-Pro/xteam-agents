"""
Adaptive Learning Specialist - Специалист по адаптивному обучению

Разрабатывает алгоритмы персонализации, адаптивные стратегии,
student modeling, recommendation systems для обучения.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class AdaptiveLearningSpecialist(ResearchAgent):
    """
    Adaptive Learning Specialist - эксперт по адаптивному обучению.

    РОЛЬ:
    - Дизайн адаптивных алгоритмов
    - Student modeling
    - Personalization strategies
    - Recommendation systems
    - Learning path optimization

    КОМПЕТЕНЦИИ:
    1. Adaptive Learning Theory
       - Zone of Proximal Development
       - Optimal challenge point
       - Mastery learning
       - Personalized learning paths

    2. Student Modeling
       - Knowledge tracing (BKT, DKT)
       - Skill modeling
       - Learning style identification
       - Affect detection

    3. Recommendation Algorithms
       - Next best action
       - Content recommendation
       - Difficulty adjustment
       - Learning resource selection

    4. Intelligent Tutoring Systems (ITS)
       - Expert model
       - Student model
       - Tutoring model
       - Interface model

    5. Learning Analytics для Adaptation
       - Real-time performance monitoring
       - Intervention triggers
       - Progress prediction
       - Risk identification

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Адаптация для struggling students
    - Knowledge graph-based pathways
    - Mastery-based progression
    - Real-time difficulty adjustment
    - Personalized scaffolding
    - Confidence building через success

    МЕТОДЫ РАБОТЫ:
    1. Student model design
    2. Adaptation rules specification
    3. Recommendation algorithm design
    4. Intervention strategies
    5. A/B testing frameworks

    РЕЗУЛЬТАТЫ:
    - Adaptive Algorithm Specifications
    - Student Model Designs
    - Recommendation Rules
    - Intervention Protocols
    - Personalization Frameworks
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Adaptive Learning Specialist",
            role="Специалист по адаптивному обучению и персонализации",
            expertise=[
                "Adaptive Learning Systems",
                "Student Modeling",
                "Knowledge Tracing",
                "Recommendation Systems",
                "ITS Design",
                "Learning Path Optimization",
                "Personalization Algorithms",
                "Real-time Adaptation",
            ],
            research_methods=[
                "Student model design",
                "Algorithm specification",
                "Simulation studies",
                "A/B testing design",
                "Learning analytics",
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Разработка адаптивной системы обучения.

        АЛГОРИТМ:
        1. Student model design (что отслеживаем)
        2. Adaptation rules (когда и как адаптироваться)
        3. Recommendation logic (что предложить)
        4. Intervention strategies (когда вмешаться)
        5. Evaluation metrics (как измерить эффективность)
        """
        updates: Dict[str, Any] = {"messages": []}

        context = await self.query_knowledge_base(
            query=f"adaptive learning personalization ITS {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

РАЗРАБОТАЙТЕ АДАПТИВНУЮ СИСТЕМУ:

1. Student Model Design:
   - Что отслеживаем о студенте:
     * Mastery level по каждому концепту
     * Prior knowledge
     * Learning rate
     * Struggle patterns
     * Confidence level
     * Engagement metrics
   - Как обновляем модель (после каждого ответа?)
   - Как представляем неопределенность (Bayesian?)

2. Adaptation Rules:
   - Difficulty Adjustment:
     * Когда повышаем сложность
     * Когда понижаем
     * Magnitude of adjustment
   - Content Selection:
     * Next best question/topic
     * Knowledge graph traversal
     * Prerequisite handling
   - Scaffolding Level:
     * Когда добавляем hints
     * Когда убираем support
     * Fading strategy

3. Recommendation Algorithm:
   - Next Best Action:
     * Continue current topic
     * Remediate gaps
     * Review previous content
     * Advance to new material
   - Scoring Function:
     * Учет mastery level
     * Учет prerequisites
     * Учет cognitive load
     * Учет motivation/engagement
   - Exploration vs Exploitation balance

4. Intervention Strategies:
   - Early Warning Signs:
     * Multiple consecutive errors
     * Prolonged struggle
     * Disengagement indicators
   - Intervention Types:
     * Hint provision
     * Worked example
     * Concept review
     * Break suggestion
     * Teacher alert
   - Timing of interventions

5. Personalization Features:
   - Learning Path Customization
   - Pace adjustment
   - Presentation modality (visual/text)
   - Feedback style
   - Challenge level

6. Evaluation Plan:
   - Metrics for adaptation quality:
     * Time to mastery
     * Engagement maintained
     * Confidence growth
     * Error rate trends
   - A/B testing framework
   - Counterfactual analysis

КРИТИЧНЫЙ ФОКУС ДЛЯ STUDYNINJA:
- Struggling students начинают ниже mastery
- Адаптация должна предотвращать overwhelm
- Success experiences критичны для motivation
- Progress должен быть visible в 1-2 дня
- Knowledge graph структура для pathways

ФОРМАТ ОТВЕТА (JSON):
{{
  "student_model": {{
    "tracked_features": [],
    "update_mechanism": "",
    "uncertainty_handling": ""
  }},
  "adaptation_rules": {{
    "difficulty_adjustment": {{
      "increase_condition": "",
      "decrease_condition": "",
      "magnitude": ""
    }},
    "content_selection": {{
      "algorithm": "",
      "graph_traversal": "",
      "prerequisite_handling": ""
    }},
    "scaffolding": {{
      "add_condition": "",
      "remove_condition": "",
      "fading_strategy": ""
    }}
  }},
  "recommendation_algorithm": {{
    "next_action_logic": "",
    "scoring_function": "",
    "exploration_exploitation": ""
  }},
  "intervention_strategies": [
    {{"trigger": "", "action": "", "timing": ""}}
  ],
  "personalization_features": [],
  "evaluation_metrics": []
}}
"""

        response = await self.generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
            max_tokens=4000,
        )

        artifact = await self.create_artifact(
            state=state,
            artifact_type="adaptive_learning_design",
            title="Adaptive Learning System Design",
            description="Дизайн адаптивной системы от Adaptive Learning Specialist",
            content={"design": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Адаптивная система разработана",
        })

        return updates


class AdaptiveLearningSpecialistCritic(ResearchCritic):
    """Критик Adaptive Learning Specialist"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Adaptive Learning Specialist Critic",
            review_focus=[
                "Student model completeness",
                "Adaptation logic soundness",
                "Recommendation quality",
                "Intervention appropriateness",
            ],
            quality_criteria=[
                "Comprehensive student modeling",
                "Clear adaptation rules",
                "Evidence-based recommendations",
                "Effective interventions",
                "Evaluation plan quality",
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "Adaptive Learning Specialist"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(artifacts[-1].content),
            focus_areas=["Student model", "Adaptation rules", "Evaluation plan"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
