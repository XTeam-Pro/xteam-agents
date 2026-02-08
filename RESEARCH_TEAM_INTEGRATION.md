# Research Team - Integration Guide

Руководство по интеграции научно-исследовательской команды в экосистему StudyNinja.

## Обзор интеграции

Research Team интегрируется на нескольких уровнях:

1. **Cognitive OS Integration** - вызов из основного workflow
2. **Direct Invocation** - прямой вызов для исследовательских задач
3. **Background Research** - автономные исследования по расписанию
4. **Development Pipeline** - передача результатов в dev team

## 1. Интеграция с Cognitive OS

### Шаг 1: Расширение ExecutionMode

Добавьте новый режим в `src/xteam_agents/models/state.py`:

```python
class ExecutionMode(str, Enum):
    STANDARD = "standard"
    ADVERSARIAL = "adversarial"
    RESEARCH = "research"  # NEW
```

### Шаг 2: Обновление analyze node

В `src/xteam_agents/graph/nodes/analyze.py` добавьте логику определения research задач:

```python
async def analyze_node(state: AgentState) -> Dict[str, Any]:
    # Существующая логика классификации
    ...

    # NEW: Определение research задач
    if requires_research(state):
        return {
            "execution_mode": ExecutionMode.RESEARCH,
            "analysis": {
                "requires_research": True,
                "research_type": classify_research_task(state),
                "complexity": estimate_research_complexity(state),
            }
        }
    ...

def requires_research(state: AgentState) -> bool:
    """Определяет, требуется ли научное исследование"""
    keywords = [
        "dataset", "model architecture", "curriculum design",
        "learning analytics", "a/b test", "research",
        "study", "experiment", "analysis"
    ]
    task_lower = state.task_context.get("description", "").lower()
    return any(keyword in task_lower for keyword in keywords)
```

### Шаг 3: Добавление research execution node

Создайте новый node в `src/xteam_agents/graph/nodes/execute_research.py`:

```python
from xteam_agents.integration.research_adapter import get_research_adapter

async def execute_research_node(state: AgentState) -> Dict[str, Any]:
    """
    Выполнение исследования через Research Team.
    """
    adapter = get_research_adapter(
        llm_provider=state.llm_provider,
        memory_manager=state.memory_manager,
    )

    # Конвертация AgentState → ResearchState
    research_state = adapter.convert_agent_state_to_research_state(state)

    # Запуск Research Team
    result = await adapter.invoke_research_team(
        research_question=research_state.research_question,
        task_type=research_state.task_type,
        complexity=research_state.complexity,
        objectives=research_state.objectives,
        scope=research_state.scope,
        constraints=research_state.constraints,
    )

    # Конвертация результатов обратно
    updates = adapter.convert_research_state_to_agent_state(
        research_state=result,
        original_agent_state=state,
    )

    return updates
```

### Шаг 4: Обновление router

В `src/xteam_agents/graph/edges.py` добавьте маршрутизацию:

```python
def route_after_analyze(state: AgentState) -> str:
    """Маршрутизация после анализа"""
    mode = state.execution_mode

    if mode == ExecutionMode.RESEARCH:
        return "execute_research"  # NEW
    elif mode == ExecutionMode.ADVERSARIAL:
        return "adversarial_execute"
    else:
        return "plan"
```

### Шаг 5: Обновление graph builder

В `src/xteam_agents/graph/builder.py`:

```python
from xteam_agents.graph.nodes.execute_research import execute_research_node

def build_cognitive_graph(...):
    workflow = StateGraph(AgentState)

    # Существующие ноды
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("plan", plan_node)
    # ...

    # NEW: Research node
    workflow.add_node("execute_research", execute_research_node)

    # Conditional edge от analyze
    workflow.add_conditional_edges(
        "analyze",
        route_after_analyze,
        {
            "plan": "plan",
            "adversarial_execute": "adversarial_execute",
            "execute_research": "execute_research",  # NEW
        }
    )

    # Research → validate
    workflow.add_edge("execute_research", "validate")

    return workflow.compile()
```

## 2. Прямой вызов (Direct Invocation)

Для задач, которые явно являются исследовательскими:

```python
from xteam_agents.integration.research_adapter import ResearchTeamAdapter
from xteam_agents.agents.research_team import (
    ResearchTaskType,
    ResearchComplexity,
)

# В любом месте системы
adapter = ResearchTeamAdapter(llm_provider, memory_manager)

result = await adapter.invoke_research_team(
    research_question="Разработать датасет для алгебры",
    task_type=ResearchTaskType.DATASET_DESIGN,
    complexity=ResearchComplexity.COMPLEX,
    objectives=["Цель 1", "Цель 2"],
)

# Результаты доступны в result
delivery_package = result["delivery_package"]
artifacts = result["artifacts"]
implementation_tasks = delivery_package.get("implementation_tasks", [])
```

## 3. Background Research (Опционально)

Для автономных фоновых исследований:

### Создайте scheduler

```python
# src/xteam_agents/scheduler/research_scheduler.py

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class ResearchScheduler:
    """Планировщик фоновых исследований"""

    def __init__(self, adapter: ResearchTeamAdapter):
        self.adapter = adapter
        self.scheduler = AsyncIOScheduler()

    def schedule_periodic_research(
        self,
        research_question: str,
        task_type: ResearchTaskType,
        cron_expression: str,  # "0 2 * * *" для 2am ежедневно
    ):
        """Запланировать периодическое исследование"""
        self.scheduler.add_job(
            self._run_research,
            trigger="cron",
            **self._parse_cron(cron_expression),
            args=[research_question, task_type],
        )

    async def _run_research(
        self,
        research_question: str,
        task_type: ResearchTaskType,
    ):
        """Выполнить исследование в фоне"""
        result = await self.adapter.invoke_research_team(
            research_question=research_question,
            task_type=task_type,
            complexity=ResearchComplexity.STANDARD,
            objectives=["Автоматическое исследование"],
        )

        # Сохранить результаты
        await self._store_results(result)

    def start(self):
        self.scheduler.start()

# Использование
scheduler = ResearchScheduler(adapter)

# Еженедельный анализ learning analytics
scheduler.schedule_periodic_research(
    research_question="Проанализировать эффективность обучения за неделю",
    task_type=ResearchTaskType.LEARNING_ANALYTICS,
    cron_expression="0 2 * * 1",  # Каждый понедельник в 2am
)

scheduler.start()
```

## 4. Integration с Development Pipeline

### Автоматическая передача задач в dev team

```python
# src/xteam_agents/integration/dev_team_adapter.py

class DevTeamAdapter:
    """Адаптер для передачи задач от Research Team в Dev Team"""

    async def process_research_delivery(
        self,
        delivery_package: Dict[str, Any],
    ) -> List[str]:
        """
        Обработка delivery package от Research Team.

        Returns:
            List of created task IDs
        """
        implementation_tasks = delivery_package.get("implementation_tasks", [])

        task_ids = []
        for task in implementation_tasks:
            # Создание задачи в task tracker (Jira, GitHub Issues, etc.)
            task_id = await self.create_dev_task(
                title=task["task"],
                description=task.get("description", ""),
                priority=task.get("priority", "medium"),
                assigned_to=task.get("assigned_to", "backend_team"),
                labels=["research", "data-driven"],
                research_context=delivery_package.get("integrated_report"),
            )
            task_ids.append(task_id)

        return task_ids

    async def create_dev_task(self, **kwargs) -> str:
        """Создать задачу в task tracker"""
        # Интеграция с Jira/GitHub/etc
        pass
```

## 5. MCP Server Tools

Добавьте Research Team tools в MCP server:

```python
# src/xteam_agents/server/tools/research_tools.py

from fastmcp import FastMCP

mcp = FastMCP("xteam-agents")

@mcp.tool()
async def submit_research_task(
    research_question: str,
    task_type: str,
    complexity: str = "standard",
    objectives: list = None,
) -> dict:
    """
    Отправить исследовательскую задачу в Research Team.

    Args:
        research_question: Исследовательский вопрос
        task_type: Тип задачи (dataset_design, model_architecture, etc.)
        complexity: Сложность (exploratory, standard, complex, critical)
        objectives: Список целей

    Returns:
        Task ID и статус
    """
    adapter = get_research_adapter(llm_provider, memory_manager)

    result = await adapter.invoke_research_team(
        research_question=research_question,
        task_type=ResearchTaskType(task_type),
        complexity=ResearchComplexity(complexity),
        objectives=objectives or [],
    )

    return {
        "task_id": result.get("task_id"),
        "status": result.get("status"),
        "quality_score": result.get("quality_score"),
    }

@mcp.tool()
async def get_research_results(task_id: str) -> dict:
    """Получить результаты исследования по ID"""
    # Implementation
    pass
```

## 6. Конфигурация

Добавьте в `.env`:

```bash
# Research Team Configuration
RESEARCH_TEAM_ENABLED=true
RESEARCH_MAX_PARALLEL_AGENTS=3
RESEARCH_TIMEOUT_MINUTES=60
RESEARCH_QUALITY_THRESHOLD=0.7
RESEARCH_AUTO_DELIVERY=true  # Автоматическая передача в dev team

# Background Research
RESEARCH_SCHEDULE_ANALYTICS=true
RESEARCH_ANALYTICS_CRON="0 2 * * 1"  # Понедельник 2am
```

## 7. Мониторинг

### Добавьте метрики

```python
# src/xteam_agents/monitoring/research_metrics.py

from prometheus_client import Counter, Histogram, Gauge

research_tasks_total = Counter(
    "research_tasks_total",
    "Total research tasks submitted",
    ["task_type", "complexity"]
)

research_duration = Histogram(
    "research_duration_seconds",
    "Research task duration",
    ["task_type"]
)

research_quality_score = Gauge(
    "research_quality_score",
    "Research quality score from critics",
    ["task_type"]
)

research_artifacts_created = Counter(
    "research_artifacts_created",
    "Total artifacts created",
    ["artifact_type", "created_by"]
)
```

## 8. Testing

Создайте интеграционные тесты:

```python
# tests/integration/test_research_integration.py

@pytest.mark.integration
async def test_cognitive_os_to_research_team():
    """Тест интеграции Cognitive OS → Research Team"""

    initial_state = AgentState(
        task_context={
            "description": "Разработать датасет для обучения",
            "task_id": "task_001",
        }
    )

    # Запуск через Cognitive OS
    result = await cognitive_graph.ainvoke(initial_state)

    # Проверка, что Research Team был вызван
    assert result.get("execution_mode") == ExecutionMode.RESEARCH
    assert "delivery_package" in result
    assert result["status"] == "completed"
```

## Roadmap интеграции

### Phase 1 (Текущий)
- ✅ Базовая структура Research Team
- ✅ Adapter для интеграции
- ✅ Примеры использования

### Phase 2
- [ ] Интеграция с Cognitive OS (execute_research node)
- [ ] MCP server tools
- [ ] Dev team adapter для автоматической передачи задач

### Phase 3
- [ ] Background research scheduler
- [ ] Мониторинг и метрики
- [ ] Dashboard для Research Team

### Phase 4
- [ ] Automated literature review (web search integration)
- [ ] Real-time collaboration между агентами
- [ ] Research memory (long-term findings storage)

## Troubleshooting

**Проблема**: Research Team не вызывается из Cognitive OS
- Проверьте, что `requires_research()` правильно классифицирует задачи
- Убедитесь, что routing обновлен в `route_after_analyze()`

**Проблема**: Долгое выполнение исследований
- Увеличьте `RESEARCH_TIMEOUT_MINUTES`
- Используйте `ResearchComplexity.STANDARD` вместо `COMPLEX`
- Проверьте параллельность выполнения агентов

**Проблема**: Низкое качество результатов
- Проверьте качество research question (должен быть specific)
- Убедитесь, что objectives четко сформулированы
- Проверьте логи от Critics для feedback

## Связанные документы

- [docs/RESEARCH_TEAM.md](docs/RESEARCH_TEAM.md) - Полная документация
- [examples/research_team_usage.py](examples/research_team_usage.py) - Примеры
- [CLAUDE.md](CLAUDE.md) - Основная документация проекта
