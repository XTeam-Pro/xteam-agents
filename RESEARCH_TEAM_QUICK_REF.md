# Research Team - Quick Reference

## 🚀 Быстрый старт

```python
from xteam_agents.integration.research_adapter import ResearchTeamAdapter
from xteam_agents.agents.research_team import ResearchTaskType, ResearchComplexity

adapter = ResearchTeamAdapter(llm_provider, memory_manager)

result = await adapter.invoke_research_team(
    research_question="Ваш исследовательский вопрос",
    task_type=ResearchTaskType.DATASET_DESIGN,
    complexity=ResearchComplexity.COMPLEX,
    objectives=["Цель 1", "Цель 2"],
)
```

## 👥 Команда (14+ агентов)

### Scientists (5)
| Агент | Специализация |
|-------|---------------|
| Chief Scientist | Координация, стратегия |
| Data Scientist | Датасеты, статистика, analytics |
| ML Researcher | Нейронные модели, архитектуры |
| Cognitive Scientist | Когнитивные процессы, memory |
| Pedagogical Researcher | Instructional design, методы |

### Methodologists (4)
- Lead Methodologist, Curriculum Designer, Assessment Designer, Adaptive Learning Specialist

### Content Team (5)
- Content Architect, SME Math, SME Science, Dataset Engineer, Annotation Specialist

### Critics (14)
По одному на каждого агента

## 📋 Типы задач

```python
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

# Аналитика
ResearchTaskType.LEARNING_ANALYTICS
ResearchTaskType.A_B_TESTING
```

## 📊 Уровни сложности

```python
ResearchComplexity.EXPLORATORY  # Предварительное исследование
ResearchComplexity.STANDARD     # Стандартное
ResearchComplexity.COMPLEX      # Сложное, междисциплинарное
ResearchComplexity.CRITICAL     # Критическое, полная команда
```

## 📁 Ключевые файлы

```
src/xteam_agents/agents/research_team/
├── research_state.py          # Модели состояния
├── research_base.py           # Базовые классы
├── research_graph.py          # LangGraph
└── nodes/                     # Все агенты
    ├── scientists/
    ├── methodologists/
    └── content_team/

integration/
└── research_adapter.py        # Адаптер

examples/
└── research_team_usage.py     # Примеры

docs/
└── RESEARCH_TEAM.md           # Документация
```

## 📖 Документация

| Файл | Содержание |
|------|------------|
| `RESEARCH_TEAM_SUMMARY.md` | Общий обзор системы |
| `RESEARCH_TEAM_INTEGRATION.md` | Руководство по интеграции |
| `RESEARCH_TEAM_INDEX.md` | Полный индекс файлов |
| `RESEARCH_TEAM_QUICK_REF.md` | Этот файл |
| `docs/RESEARCH_TEAM.md` | Полная документация |

## 🎯 Результаты

```python
result = {
    "delivery_package": {
        "integrated_report": "...",
        "implementation_tasks": [...]
    },
    "artifacts": [...],      # От каждого агента
    "findings": [...],       # Научные открытия
    "quality_score": 0.85,   # 0-1
    "status": "completed"
}
```

## ⚙️ Конфигурация (.env)

```bash
RESEARCH_TEAM_ENABLED=true
RESEARCH_MAX_PARALLEL_AGENTS=3
RESEARCH_TIMEOUT_MINUTES=60
RESEARCH_QUALITY_THRESHOLD=0.7
```

## 🧪 Тестирование

```bash
# Unit tests
pytest tests/unit/test_research_team.py

# Примеры
python examples/research_team_usage.py
```

## 🔗 Интеграция с Cognitive OS

```python
# В analyze node
if requires_research(state):
    return {"execution_mode": ExecutionMode.RESEARCH}

# Routing
def route_after_analyze(state):
    if state.execution_mode == ExecutionMode.RESEARCH:
        return "execute_research"
```

## 📞 Поддержка

- **Примеры**: `examples/research_team_usage.py`
- **Документация**: `docs/RESEARCH_TEAM.md`
- **Тесты**: `tests/unit/test_research_team.py`

## ✅ Статус реализации

**Phase 1 (Текущий)** ✅
- ✅ Архитектура
- ✅ 5 Scientists + Critics
- ✅ 1 Methodologist
- ✅ 1 Content Team
- ✅ Adapter
- ✅ Документация

**Phase 2** (Следующий)
- [ ] Остальные Methodologists (3)
- [ ] Остальные Content Team (4)
- [ ] Cognitive OS integration

---

**Создано**: 6,500+ строк кода и документации
**Готово к использованию**: ✅
