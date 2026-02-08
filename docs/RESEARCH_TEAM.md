

# Research Team - Научно-исследовательская команда

## Обзор

Research Team - это специализированная команда ученых, методистов и специалистов по созданию образовательного контента, интегрированная в экосистему xteam-agents. Команда проводит глубокие исследования, разрабатывает инновационные подходы и создает высококачественные образовательные датасеты и нейронные модели для платформы StudyNinja.

## Архитектура команды

### 1. Scientists (Ученые) - 5 агентов

#### Chief Scientist (Главный ученый)
**Роль**: Координатор всех научных исследований
**Компетенции**:
- Формулировка исследовательских вопросов
- Дизайн экспериментов
- Научная координация команды
- Интеграция результатов
- Валидация научных выводов

**Ответственность**:
- Разработка исследовательской стратегии
- Распределение задач между учеными
- Обеспечение научной строгости
- Peer review и качество

#### Data Scientist (Специалист по данным)
**Роль**: Анализ данных, разработка датасетов, Learning Analytics
**Компетенции**:
- Статистический анализ
- Feature engineering
- Дизайн датасетов
- A/B тестирование
- Предсказательная аналитика

**Специализация для StudyNinja**:
- Датасеты для адаптивного обучения
- Метрики эффективности (mastery scores)
- Аналитика knowledge graph
- Предсказательные модели (risk of dropout)

#### ML Researcher (Исследователь ML)
**Роль**: Разработка нейронных архитектур и моделей
**Компетенции**:
- Deep Learning architectures
- Knowledge Tracing models (DKT, SAKT)
- Graph Neural Networks
- Model optimization
- Transfer learning

**Специализация для StudyNinja**:
- Модели для предсказания mastery level
- Adaptive question selection algorithms
- GNN для knowledge graph
- Assessment AI (question generation, grading)

#### Cognitive Scientist (Когнитивный психолог)
**Роль**: Исследование когнитивных процессов обучения
**Компетенции**:
- Cognitive Load Theory
- Memory systems (encoding, retrieval)
- Attention mechanisms
- Metacognition
- Motivation psychology

**Специализация для StudyNinja**:
- Оптимизация cognitive load для struggling students
- Дизайн "small wins" для confidence building
- Spacing и interleaving стратегии
- Metacognitive prompts в AI tutor

#### Pedagogical Researcher (Педагог-исследователь)
**Роль**: Разработка педагогических методов и instructional design
**Компетенции**:
- Instructional Design (ADDIE, UbD)
- Scaffolding и differentiation
- Formative/summative assessment
- Mastery learning
- Adaptive teaching strategies

**Специализация для StudyNinja**:
- Pedagogy для struggling students
- Mastery-based progression
- Adaptive scaffolding через AI
- Assessment design

### 2. Methodologists (Методисты) - 4 агента

#### Lead Methodologist
**Роль**: Руководство методической работой
**Компетенции**: Координация разработки методик, standards alignment

#### Curriculum Designer (Разработчик учебных программ)
**Роль**: Проектирование curriculum в форме knowledge graph
**Компетенции**:
- Curriculum mapping
- Prerequisite chains
- Learning pathways design
- Neo4j graph schema design

**Специализация для StudyNinja**:
- Curriculum как Neo4j graph
- Adaptive pathways
- Multiple entry points
- Remediation branches

#### Assessment Designer
**Роль**: Разработка систем оценивания
**Компетенции**: Formative/summative assessment, rubrics, adaptive testing

#### Adaptive Learning Specialist
**Роль**: Специализация на адаптивных алгоритмах обучения
**Компетенции**: Personalization, competency-based learning, ITS design

### 3. Content Team (Команда контента) - 5 агентов

#### Content Architect
**Роль**: Архитектура образовательного контента
**Компетенции**: Content strategy, organization, quality standards

#### Subject Matter Expert (Math)
**Роль**: Экспертиза по математике
**Компетенции**: Math curriculum, problem design, common misconceptions

#### Subject Matter Expert (Science)
**Роль**: Экспертиза по естественным наукам
**Компетенции**: Science curriculum, inquiry-based learning

#### Dataset Engineer (Инженер датасетов)
**Роль**: Инженерная реализация датасетов
**Компетенции**:
- Data pipelines (ETL)
- Annotation systems (LabelStudio)
- Data versioning (DVC)
- Quality assurance automation

**Специализация для StudyNinja**:
- Educational question datasets
- Neo4j graph data pipelines
- Annotation workflows
- Data validation automation

#### Annotation Specialist
**Роль**: Управление процессом аннотации данных
**Компетенции**: Annotation guidelines, quality control, inter-annotator agreement

### 4. Critics (Рецензенты) - по 1 на каждого агента

Каждый агент имеет соответствующего критика, который проводит peer review:
- **Chief Scientist Critic**: Валидация стратегии и методологии
- **Data Scientist Critic**: Проверка статистической корректности
- **ML Researcher Critic**: Валидация ML решений
- **Cognitive Scientist Critic**: Проверка когнитивных принципов
- **Pedagogical Researcher Critic**: Валидация педагогических методов
- И т.д.

## Типы исследовательских задач

```python
class ResearchTaskType(str, Enum):
    # Фундаментальные исследования
    FUNDAMENTAL_RESEARCH = "fundamental_research"
    LITERATURE_REVIEW = "literature_review"
    HYPOTHESIS_TESTING = "hypothesis_testing"

    # Разработка датасетов
    DATASET_DESIGN = "dataset_design"
    DATA_COLLECTION = "data_collection"
    DATA_ANNOTATION = "data_annotation"
    DATASET_VALIDATION = "dataset_validation"

    # Разработка моделей
    MODEL_ARCHITECTURE = "model_architecture"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_OPTIMIZATION = "model_optimization"

    # Методическая разработка
    CURRICULUM_DESIGN = "curriculum_design"
    ASSESSMENT_DESIGN = "assessment_design"
    PEDAGOGICAL_STRATEGY = "pedagogical_strategy"
    ADAPTIVE_ALGORITHM = "adaptive_algorithm"

    # Аналитика
    LEARNING_ANALYTICS = "learning_analytics"
    COGNITIVE_ANALYSIS = "cognitive_analysis"
    EFFECTIVENESS_STUDY = "effectiveness_study"
    A_B_TESTING = "ab_testing"
```

## Workflow исследования

```
1. INITIALIZATION
   ├─ Orchestrator классифицирует задачу
   ├─ Chief Scientist формирует стратегию
   └─ Назначаются ответственные агенты

2. LITERATURE REVIEW (если нужно)
   └─ Анализ существующих подходов

3. METHODOLOGY DESIGN
   └─ Разработка методологии исследования

4. DATA PREPARATION (для dataset/analytics задач)
   ├─ Data Scientist: дизайн датасета
   └─ Dataset Engineer: реализация pipelines

5. IMPLEMENTATION
   ├─ ML Researcher: разработка моделей
   ├─ Cognitive Scientist: когнитивный анализ
   ├─ Pedagogical Researcher: педагогические стратегии
   └─ Curriculum Designer: структура curriculum

6. EXPERIMENTATION (если нужно)
   └─ Проведение экспериментов, A/B тестов

7. ANALYSIS
   └─ Анализ результатов всеми агентами

8. VALIDATION
   └─ Peer review от Critics

9. DOCUMENTATION
   └─ Создание итоговых отчетов и документации

10. DELIVERY
    ├─ Integration report
    ├─ Implementation tasks для dev team
    └─ Deliverables (datasets, models, documentation)
```

## LangGraph Architecture

```
START
  ↓
classify_task (Orchestrator)
  ↓
chief_scientist (Стратегия)
  ↓
[Параллельная работа специалистов]
  ├─ data_scientist
  ├─ ml_researcher
  ├─ cognitive_scientist
  ├─ pedagogical_researcher
  └─ curriculum_designer
  ↓
dataset_engineer (Реализация)
  ↓
peer_review (Critics)
  ↓
integrate (Итоговый отчет)
  ↓
END
```

## Интеграция с Cognitive OS

Research Team интегрируется через `ResearchTeamAdapter`:

```python
from xteam_agents.integration.research_adapter import ResearchTeamAdapter

adapter = ResearchTeamAdapter(llm_provider, memory_manager)

result = await adapter.invoke_research_team(
    research_question="Разработать датасет для адаптивного обучения",
    task_type=ResearchTaskType.DATASET_DESIGN,
    complexity=ResearchComplexity.COMPLEX,
    objectives=["Цель 1", "Цель 2"],
    constraints=["Ограничение 1"],
)
```

### Маршрутизация из Cognitive OS

В `analyze` node Cognitive OS может определить, что нужно исследование:

```python
if task_requires_research(state):
    state.execution_mode = ExecutionMode.RESEARCH
    # → маршрутизация в Research Team
```

## Результаты работы команды

### Deliverables Package

```python
{
    "integrated_report": "Executive summary + detailed findings",
    "artifacts": [
        {
            "type": "dataset_specification",
            "content": {...},
            "created_by": "Data Scientist"
        },
        {
            "type": "model_architecture",
            "content": {...},
            "created_by": "ML Researcher"
        },
        {
            "type": "curriculum_design",
            "content": {...},
            "created_by": "Curriculum Designer"
        }
    ],
    "findings": [
        {
            "title": "Optimal spacing interval",
            "confidence": 0.95,
            "implications": [...]
        }
    ],
    "implementation_tasks": [
        {
            "task": "Implement data collection pipeline",
            "assigned_to": "backend_team",
            "priority": "high"
        }
    ],
    "quality_score": 0.87
}
```

## Примеры использования

См. `examples/research_team_usage.py`:
- Dataset Design Example
- Model Architecture Design Example
- Curriculum Design Example
- Learning Analytics Example
- A/B Testing Design Example

## Конфигурация

Параметры Research Team в `.env`:

```bash
# Research Team Configuration
RESEARCH_TEAM_ENABLED=true
RESEARCH_MAX_PARALLEL_AGENTS=3
RESEARCH_TIMEOUT_MINUTES=60
RESEARCH_QUALITY_THRESHOLD=0.7
```

## Мониторинг и метрики

Ключевые метрики Research Team:
- **Research Quality Score**: Оценка от Critics (0-1)
- **Artifact Count**: Количество созданных артефактов
- **Finding Confidence**: Средняя уверенность в находках
- **Time to Delivery**: Время от запроса до delivery package
- **Implementation Success Rate**: Успешность внедрения рекомендаций

## Best Practices

1. **Четкая формулировка вопроса**: Research question должен быть specific и measurable
2. **Определение objectives**: 3-5 конкретных целей
3. **Realistic constraints**: Указывать реальные ограничения (время, ресурсы, privacy)
4. **Complexity classification**: Правильная оценка сложности для назначения агентов
5. **Peer review**: Всегда проходить через Critics для качества
6. **Actionable recommendations**: Результаты должны быть внедряемыми

## Integration с Development Team

Research Team → Development Tasks:

```
Research Findings
  ↓
Implementation Tasks (prioritized)
  ↓
Backend Team / Frontend Team / DevOps
  ↓
Deployment
  ↓
Monitoring & Evaluation
  ↓
[Feedback loop to Research Team]
```

## Roadmap

### Phase 1 (Current)
- ✅ Core architecture
- ✅ 5 Scientists + Critics
- ✅ Basic methodologists
- ✅ Dataset Engineer
- ✅ Integration adapter

### Phase 2 (Next)
- [ ] Full methodologists team (4 agents)
- [ ] Complete content team (5 agents)
- [ ] Advanced orchestration (parallel execution)
- [ ] Real-time collaboration between agents

### Phase 3 (Future)
- [ ] Automated literature review (web search integration)
- [ ] Experiment execution automation
- [ ] Continuous research (background mode)
- [ ] Research memory (long-term findings storage)

## Troubleshooting

**Problem**: Research takes too long
- **Solution**: Reduce complexity or scope, use parallel execution

**Problem**: Low quality scores from Critics
- **Solution**: Refine research question, add more constraints, iterate

**Problem**: Implementation tasks не внедряются
- **Solution**: Более конкретные и actionable recommendations

## Связанные документы

- [CLAUDE.md](../CLAUDE.md) - Основная документация проекта
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Деплой и инфраструктура
- [API Documentation] - API для вызова Research Team
