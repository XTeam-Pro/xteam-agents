# 🎭 Adversarial Agent Team - Complete Index

## 📦 Полная структура проекта

Создана полная архитектура команды из **21 AI агента** с adversarial подходом (агент-критик пары + оркестратор).

---

## 📚 Документация (6 файлов)

### 🎯 Главный документ
**[AGENTS_README.md](AGENTS_README.md)** - **НАЧНИТЕ ЗДЕСЬ**
- Обзор adversarial подхода
- Быстрый старт
- FAQ
- Основные концепции

### 📖 Детальная спецификация
**[ADVERSARIAL_AGENTS.md](ADVERSARIAL_AGENTS.md)** - Полная архитектура
- Описание всех 21 агентов
- Adversarial flow детали
- Critic стратегии (Constructive, Adversarial, Perfectionist)
- Примеры сценариев
- Conflict resolution механизм

### 👥 Визуальный справочник
**[TEAM_ROSTER.md](TEAM_ROSTER.md)** - Все агенты в таблицах
- 10 пар агент-критик
- 1 оркестратор
- Модели и температуры
- Approval thresholds
- Специализации

### 📋 Краткий обзор
**[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Quick reference
- Phase-based execution
- Critic evaluation system
- Target metrics
- Configuration highlights
- Next steps

### 💡 Примеры использования
**[AGENTS_USAGE.md](AGENTS_USAGE.md)** - Usage guide
- Примеры workflows
- RACI матрица
- Escalation сценарии
- Best practices

### 📚 Оригинальная архитектура (deprecated)
**[AGENTS_ARCHITECTURE.md](AGENTS_ARCHITECTURE.md)** - Old design
- Первая итерация (10 агентов без критиков)
- Заменена на adversarial подход

---

## 💻 Код реализации (6 файлов)

```
src/xteam_agents/agents/
```

### Adversarial система (основная)

#### 1. **adversarial_config.py** - Конфигурация
```python
# Содержит:
- AgentRole (21 ролей)
- AgentConfig (конфиг каждого агента)
- AgentPairConfig (конфиг пар)
- CriticEvaluation (5-dimensional scoring)
- CriticStrategy (Constructive/Adversarial/Perfectionist)
- AGENT_CONFIGS dict (все 21 агента)
- AGENT_PAIRS dict (все 10 пар)
- Helper functions
```

#### 2. **adversarial_state.py** - State management
```python
# Содержит:
- AdversarialAgentState (главный state)
- OrchestratorDecision (initial decision)
- OrchestratorFinalDecision (final approval)
- AgentOutput (выход агента)
- CriticReview (ревью критика)
- PairResult (результат пары)
- Conflict (конфликт для эскалации)
- State reducers для LangGraph
```

#### 3. **adversarial_init.py** - Package initialization
```python
# Экспортирует все для использования:
from xteam_agents.agents import (
    AdversarialAgentState,
    AgentRole,
    get_pair_config,
    ...
)
```

### Оригинальная система (legacy)

#### 4. **config.py** - Original RACI config
```python
# Оригинальная RACI архитектура
# Сохранена для справки
# Используйте adversarial_config.py
```

#### 5. **state.py** - Original state models
```python
# Оригинальные модели состояния
# Сохранены для справки
# Используйте adversarial_state.py
```

#### 6. **routing.py** - Original routing logic
```python
# Оригинальная routing логика
# Будет переписана для adversarial flow
```

#### 7. **__init__.py** - Old package init
```python
# Экспортирует оригинальные модули
# Будет обновлен для adversarial системы
```

---

## 🏗 Архитектура в цифрах

### Агенты
- **21 Total Agents**
  - 1 OrchestratorAgent
  - 10 Action Agents
  - 10 Critic Agents

### Модели LLM
- **5 Opus agents** (критические решения)
  - Orchestrator, TechLead + Critic, AIArchitect + Critic, Security + Critic
- **16 Sonnet agents** (стандартная работа)
  - Все остальные

### Temperature Range
- **Lowest**: 0.1 (QAAgent, SecurityAgent)
- **Highest**: 0.9 (SecurityCritic - Red Team)
- **Average**: 0.5

### Approval Thresholds
- **Highest**: 9.0 (Security pair)
- **Standard**: 7.0-8.0 (most pairs)
- **Iterations**: 3 (standard), 5 (security)

---

## 🔄 Adversarial Flow Summary

```
┌─────────────────────────────────────────┐
│ USER REQUEST                            │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 🎯 ORCHESTRATOR                         │
│ - Classifies task                       │
│ - Selects pairs                         │
│ - Defines criteria                      │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 10 AGENT-CRITIC PAIRS                   │
│ (Each pair iterates 1-5 times)         │
│                                         │
│ For each pair:                          │
│   Agent proposes → Critic reviews       │
│   If rejected → Agent revises           │
│   Repeat until:                         │
│   - Approved (threshold met)            │
│   - Escalated (max iterations)          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 🎯 ORCHESTRATOR RESOLUTION              │
│ - Reviews all pair results              │
│ - Resolves conflicts                    │
│ - Final decision                        │
│ - Commits or rejects                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ OUTCOME                                 │
│ ✅ Approved & Committed                │
│ ❌ Rejected with feedback              │
└─────────────────────────────────────────┘
```

---

## 📊 Система оценки (5D Scoring)

Каждый критик оценивает решение агента по 5 параметрам (0-10):

1. **Correctness** - техническая корректность
2. **Completeness** - полнота решения
3. **Quality** - качество кода/дизайна
4. **Performance** - производительность
5. **Security** - безопасность

**Одобрение** если:
- `average_score >= approval_threshold` (7.0-9.0)
- `min_score >= min_threshold` (5.0-7.0)

---

## 🎭 Три стратегии критиков

### 1. Constructive (7 пар)
**Используют**: TechLead, Architect, Backend, Frontend, Data, DevOps, AIArchitect

**Подход**: Помогают улучшить решение
- Находят проблемы
- Предлагают альтернативы
- Collaborative tone

### 2. Adversarial (1 пара)
**Используют**: Security (Red Team)

**Подход**: Активно атакуют систему
- Attacker mindset
- Ищут уязвимости
- Симулируют атаки
- Temperature 0.9 (самый креативный)

### 3. Perfectionist (2 пары)
**Используют**: QA, Performance

**Подход**: Никогда не удовлетворены
- Extremely high standards
- Push for excellence
- Find edge cases

---

## 🛡 Разрешение конфликтов

### Уровни эскалации

```
Level 1: Pair Iteration (Agent ↔ Critic)
  - Max 3-5 rounds
  - 90% случаев решаются здесь
    ↓
Level 2: Escalation to Orchestrator
  - Reviews both positions
  - May consult other agents
  - 10% случаев
    ↓
Level 3: Binding Decision
  - Orchestrator's decision is FINAL
  - IMMUTABLE
  - No appeals
```

---

## 📈 Target Metrics (KPIs)

| Метрика | Target | Actual | Status |
|---------|--------|--------|--------|
| Overall Quality | > 8.0 | TBD | ⏳ |
| Approval Rate | 60-80% | TBD | ⏳ |
| Avg Iterations | 1.5-2.0 | TBD | ⏳ |
| Escalation Rate | < 10% | TBD | ⏳ |

---

## 🚀 Quick Start Guide

### Для чтения

1. **Начните с**: [AGENTS_README.md](AGENTS_README.md)
2. **Посмотрите агентов**: [TEAM_ROSTER.md](TEAM_ROSTER.md)
3. **Детали архитектуры**: [ADVERSARIAL_AGENTS.md](ADVERSARIAL_AGENTS.md)
4. **Примеры использования**: [AGENTS_USAGE.md](AGENTS_USAGE.md)

### Для разработки

1. **Config**: `src/xteam_agents/agents/adversarial_config.py`
2. **State**: `src/xteam_agents/agents/adversarial_state.py`
3. **Init**: `src/xteam_agents/agents/adversarial_init.py`

### Для использования (когда реализовано)

```python
from xteam_agents.agents import (
    AdversarialAgentState,
    AgentRole,
    get_pair_config
)

# Create task
state = AdversarialAgentState(
    task_id="task_001",
    original_request="Your task here"
)

# Orchestrator handles everything automatically
```

---

## 🎯 Use Cases

### По сложности

| Task | Selected Pairs | Time | Iterations |
|------|---------------|------|------------|
| Simple API | Backend, QA | 3-5 min | 2-3 |
| Auth Feature | TechLead, Security, Data, Backend, QA | 15-20 min | 8-12 |
| Architecture Change | All pairs | 25-30 min | 15-20 |

### По категориям

| Category | Primary Pairs |
|----------|--------------|
| Backend Logic | Backend, Data, QA |
| Frontend UI | Frontend, QA |
| Security | Security, Backend, Data, QA |
| Performance | Performance, Data, Backend |
| AI/ML | AIArchitect, Backend, Performance |
| Infrastructure | DevOps, Security, Performance |

---

## 📖 Полный список файлов

### Документация (6 файлов)
```
✅ AGENTS_README.md              (Main entry point)
✅ ADVERSARIAL_AGENTS.md         (Full architecture)
✅ TEAM_ROSTER.md               (All 21 agents)
✅ IMPLEMENTATION_SUMMARY.md    (Quick reference)
✅ AGENTS_USAGE.md              (Usage examples)
✅ AGENTS_ARCHITECTURE.md       (Original - deprecated)
```

### Код (6 файлов)
```
✅ adversarial_config.py         (Agent configurations)
✅ adversarial_state.py          (State management)
✅ adversarial_init.py           (Package init)
✅ config.py                     (Original RACI)
✅ state.py                      (Original state)
✅ routing.py                    (Original routing)
✅ __init__.py                   (Old package init)
```

### Дополнительно
```
✅ AGENTS_INDEX.md              (This file - navigation)
```

**Total**: 13 файлов созданы

---

## ✅ Статус реализации

### Завершено
- [x] Полная архитектурная спецификация
- [x] Конфигурация всех 21 агентов
- [x] State models для adversarial flow
- [x] Система 5D scoring
- [x] Conflict resolution design
- [x] Comprehensive documentation
- [x] Code structure

### Next Steps (для реализации)
- [ ] Orchestrator agent implementation
- [ ] Pair interaction logic
- [ ] LangGraph graph builder
- [ ] Agent node implementations
- [ ] Critic node implementations
- [ ] Metrics tracking
- [ ] Integration tests
- [ ] Dashboard UI

---

## 🎓 Ключевые концепции

### 1. Adversarial = Quality
Каждое решение проверяется оппонентом → выше качество

### 2. Orchestrator = Authority
Верховный координатор, разрешает все конфликты

### 3. Iterative = Better
1-5 раундов улучшают решение до отличного

### 4. Measurable = Objective
5D scoring убирает субъективность

### 5. Escalation = Normal
10% эскалаций - здоровый показатель

---

## 💡 Философия проекта

> **"Iron sharpens iron, and one person sharpens another."**
> — Proverbs 27:17

Adversarial подход гарантирует:
- ✅ Высшее качество через противостояние
- ✅ Минимум слепых зон
- ✅ Естественная коррекция ошибок
- ✅ Непрерывное улучшение
- ✅ Battle-tested решения

---

## 📞 Navigation

### Хочу понять концепцию
→ [AGENTS_README.md](AGENTS_README.md)

### Хочу увидеть всех агентов
→ [TEAM_ROSTER.md](TEAM_ROSTER.md)

### Хочу детали архитектуры
→ [ADVERSARIAL_AGENTS.md](ADVERSARIAL_AGENTS.md)

### Хочу примеры использования
→ [AGENTS_USAGE.md](AGENTS_USAGE.md)

### Хочу краткий обзор
→ [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

### Хочу начать разработку
→ `src/xteam_agents/agents/adversarial_*.py`

---

## 🎉 Summary

**Создана полная архитектура**:
- 21 AI агент с adversarial подходом
- 1 Orchestrator + 10 Agent-Critic пар
- 5-dimensional quality scoring
- Conflict resolution механизм
- Comprehensive documentation
- Code structure ready for implementation

**Status**: ✅ Architecture complete, ready for implementation

**Version**: 1.0

**Created**: 2026-02-03

---

🎭 **Adversarial Agent Team**
*Every agent needs an opponent to reach their best*
