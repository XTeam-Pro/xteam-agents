"""
Dataset Engineer - Инженер датасетов

Реализует создание датасетов: сбор, аннотация, валидация, версионирование.
"""

from typing import Dict, Any
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class DatasetEngineer(ResearchAgent):
    """
    Dataset Engineer - инженер создания датасетов.

    РОЛЬ:
    - Реализация сбора данных
    - Построение data pipelines
    - Quality assurance процессы
    - Версионирование датасетов
    - Automated data validation

    КОМПЕТЕНЦИИ:
    1. Data Engineering: ETL pipelines, Data validation, Data versioning (DVC),
       Schema enforcement, Data quality metrics
    2. Annotation Tools: LabelStudio, Prodigy, Custom tools
    3. Synthetic Data: Generation strategies, Augmentation techniques
    4. Database Design: PostgreSQL, Neo4j, Document stores
    5. CI/CD для данных: Automated testing, Data drift detection

    СПЕЦИАЛИЗАЦИЯ ДЛЯ STUDYNINJA:
    - Educational question datasets
    - Student interaction data
    - Knowledge graph data (Neo4j)
    - Mastery progression data
    - Error pattern datasets

    РЕЗУЛЬТАТЫ:
    - Data Collection Scripts
    - Annotation Guidelines
    - Data Validation Pipelines
    - Dataset Documentation (Datasheets)
    - Versioned Dataset Releases
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Dataset Engineer",
            role="Инженер создания и управления датасетами",
            expertise=[
                "Data Engineering", "ETL Pipelines", "Data Quality",
                "Annotation Systems", "Data Versioning", "Schema Design",
                "Automated Testing", "Documentation"
            ],
            research_methods=[
                "Data profiling", "Quality metrics", "Validation rules",
                "Schema evolution", "Data lineage tracking"
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Разработка инженерного решения для датасета.

        АЛГОРИТМ:
        1. Анализ требований от Data Scientist
        2. Дизайн data pipeline
        3. Выбор/разработка annotation tools
        4. Создание validation rules
        5. Настройка версионирования
        6. Документация
        """
        updates: Dict[str, Any] = {"messages": []}

        # Получаем спецификацию от Data Scientist
        data_artifacts = [a for a in state.artifacts if a.created_by == "Data Scientist"]

        context = await self.query_knowledge_base(
            query=f"data engineering pipelines dataset {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()
        user_prompt = f"""
ЗАДАЧА: {state.research_question}

СПЕЦИФИКАЦИЯ ОТ DATA SCIENTIST:
{str(data_artifacts[-1].content)[:500] if data_artifacts else "Нет спецификации"}

РАЗРАБОТАЙТЕ ИНЖЕНЕРНОЕ РЕШЕНИЕ:

1. Data Collection Pipeline:
   - Sources (APIs, databases, user-generated)
   - Extraction scripts
   - Scheduling (cron/airflow)
   - Error handling

2. Data Processing:
   - Cleaning rules
   - Normalization
   - Feature extraction
   - Schema validation

3. Annotation System:
   - Tool choice (LabelStudio/Prodigy/Custom)
   - Annotation guidelines document
   - Quality control (inter-annotator agreement)
   - Annotation workflow

4. Validation Pipeline:
   - Schema checks (Great Expectations/Pandera)
   - Statistical tests
   - Outlier detection
   - Consistency checks

5. Versioning & Storage:
   - DVC/Git LFS setup
   - Storage backend (S3/MinIO)
   - Versioning strategy
   - Metadata tracking

6. Documentation:
   - Datasheet for the dataset
   - API documentation
   - Usage examples

ФОРМАТ ОТВЕТА (JSON + Code):
{{
  "pipeline_overview": "Описание",
  "collection_script": "# Python code",
  "processing_script": "# Python code",
  "annotation_guidelines": "Markdown document",
  "validation_rules": [{{"rule": "", "check": ""}}],
  "versioning_setup": "DVC configuration",
  "documentation_template": "Datasheet template"
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
            artifact_type="dataset_engineering",
            title="Dataset Engineering Implementation",
            description="Инженерное решение для датасета от Dataset Engineer",
            content={"implementation": response, "context": context[:2]},
            metadata={"phase": state.current_phase.value},
        )

        updates["artifacts"] = [artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "message": "Разработано инженерное решение для датасета",
        })

        return updates


class DatasetEngineerCritic(ResearchCritic):
    """Критик Dataset Engineer"""

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Dataset Engineer Critic",
            review_focus=[
                "Pipeline robustness",
                "Validation completeness",
                "Documentation quality",
                "Scalability"
            ],
            quality_criteria=[
                "Code quality", "Error handling",
                "Reproducibility", "Performance"
            ],
        )

    async def review_research(self, state: ResearchState, artifact_to_review=None) -> Dict[str, Any]:
        artifacts = [a for a in state.artifacts if a.created_by == "Dataset Engineer"]
        if not artifacts:
            return {"review_text": "Нет артефактов", "verdict": "PENDING"}

        review = await self.generate_review(
            content=str(artifacts[-1].content),
            focus_areas=["Code quality", "Validation robustness", "Documentation"]
        )
        return {**review, "quality_score": self.get_quality_score(review)}
