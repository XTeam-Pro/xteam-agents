# Research Team - Quick Start

Научно-исследовательская команда для разработки образовательных датасетов, нейронных моделей и методик обучения.

## Быстрый старт

### 1. Базовое использование

```python
from xteam_agents.agents.research_team import (
    create_research_team_graph,
    ResearchState,
    ResearchTaskType,
    ResearchComplexity,
)
from xteam_agents.llm.provider import get_llm_provider
from xteam_agents.memory.manager import MemoryManager

# Инициализация
llm_provider = get_llm_provider()
memory_manager = MemoryManager()
research_graph = create_research_team_graph(llm_provider, memory_manager)

# Создание задачи
initial_state = ResearchState(
    task_id="research_001",
    task_type=ResearchTaskType.DATASET_DESIGN,
    complexity=ResearchComplexity.COMPLEX,
    research_question="Разработать датасет вопросов по алгебре с градацией сложности",
    objectives=[
        "Определить структуру датасета",
        "Разработать таксономию сложности",
        "Создать annotation guidelines",
    ],
)

# Запуск исследования
result = await research_graph.ainvoke(initial_state)

print(f"Status: {result['status']}")
print(f"Quality: {result['quality_score']}")
print(f"Artifacts: {len(result['artifacts'])}")
```

### 2. Через адаптер (рекомендуется)

```python
from xteam_agents.integration.research_adapter import ResearchTeamAdapter

adapter = ResearchTeamAdapter(llm_provider, memory_manager)

result = await adapter.invoke_research_team(
    research_question="Создать модель для предсказания mastery level",
    task_type=ResearchTaskType.MODEL_ARCHITECTURE,
    complexity=ResearchComplexity.COMPLEX,
    objectives=["Спроектировать архитектуру", "Обосновать выбор"],
)
```

## Состав команды

### Scientists (5)
- Chief Scientist
- Data Scientist
- ML Researcher
- Cognitive Scientist
- Pedagogical Researcher

### Methodologists (4)
- Lead Methodologist
- Curriculum Designer
- Assessment Designer
- Adaptive Learning Specialist

### Content Team (5)
- Content Architect
- SME Math
- SME Science
- Dataset Engineer
- Annotation Specialist

### Critics (14)
По одному на каждого агента

## Типы задач

```python
from xteam_agents.agents.research_team import ResearchTaskType

# Датасеты
ResearchTaskType.DATASET_DESIGN
ResearchTaskType.DATA_COLLECTION
ResearchTaskType.DATA_ANNOTATION

# Модели
ResearchTaskType.MODEL_ARCHITECTURE
ResearchTaskType.MODEL_TRAINING
ResearchTaskType.MODEL_EVALUATION

# Методика
ResearchTaskType.CURRICULUM_DESIGN
ResearchTaskType.ASSESSMENT_DESIGN
ResearchTaskType.PEDAGOGICAL_STRATEGY

# Аналитика
ResearchTaskType.LEARNING_ANALYTICS
ResearchTaskType.A_B_TESTING
```

## Примеры

См. `examples/research_team_usage.py`:
- Dataset Design
- Model Architecture
- Curriculum Design
- Learning Analytics
- A/B Testing

## Документация

Полная документация: `docs/RESEARCH_TEAM.md`

## Workflow

```
classify → Chief Scientist → Specialists → Peer Review → Integration → Delivery
```

## Результаты

```python
{
    "delivery_package": {
        "integrated_report": "...",
        "implementation_tasks": [...]
    },
    "artifacts": [...],  # От каждого агента
    "findings": [...],   # Научные открытия
    "quality_score": 0.85,
    "status": "completed"
}
```
