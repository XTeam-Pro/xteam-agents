# 🔗 Интеграция Cognitive OS + Adversarial Agent Team

## 📊 Краткий обзор

### Что есть сейчас

1. **Cognitive Operating System** - работает автономно
   - Memory Manager (Redis, Qdrant, Neo4j, PostgreSQL)
   - LangGraph: analyze → plan → execute → validate → commit → reflect
   - MCP Server, Action Executor

2. **Adversarial Agent Team** - работает автономно
   - 21 агент (1 Orchestrator + 10 Agent-Critic pairs)
   - Итеративное улучшение качества
   - 5D scoring, conflict resolution

### Проблема

Системы изолированы и не используют общие ресурсы (память, LLM provider).

---

## 🎯 Решение: Иерархическая интеграция

```
┌─────────────────────────────────────────────┐
│         COGNITIVE OS (Top-level)            │
│                                             │
│  analyze → plan → EXECUTE → validate → ...  │
│                     ↓                        │
│            ┌────────────────┐               │
│            │ Unified        │               │
│            │ Executor       │               │
│            └───┬────────┬───┘               │
│                │        │                    │
│         simple │        │ complex            │
│                ↓        ↓                    │
│         ┌─────────┐  ┌──────────────────┐  │
│         │Standard │  │ Adversarial Team │  │
│         │  LLM    │  │  (21 agents)     │  │
│         └─────────┘  └──────────────────┘  │
│                                             │
│         ┌─────────────────────────────┐    │
│         │   Shared Memory Manager     │    │
│         │   Shared LLM Provider       │    │
│         └─────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### Ключевая идея

**Adversarial Team работает ВНУТРИ Cognitive OS как специализированный executor для сложных задач.**

---

## 🔄 Execution Flow

### Простая задача (Simple/Medium)
```
User → analyze → plan → execute (standard LLM) → validate → commit
```

### Сложная задача (Complex/Critical)
```
User → analyze → plan → execute (Adversarial Team) → validate → commit
                              ↓
                    Orchestrator classify
                              ↓
                    Agent-Critic pairs (iterate)
                              ↓
                    Conflict resolution
                              ↓
                    Final decision → back to validate
```

---

## 🔧 Изменения в архитектуре

### 1. Execute Node получает два режима

**Before:**
```python
execute_node:
  → LLM generates result
  → Done
```

**After:**
```python
execute_node:
  → Check complexity
  → IF simple: Standard LLM
  → IF complex: Adversarial Team
  → Return result
```

### 2. Общие ресурсы

**Memory Manager** - один экземпляр для всех:
- Cognitive OS nodes используют его
- Adversarial agents используют его
- Memory invariants enforced

**LLM Provider** - один экземпляр для всех:
- Shared connection pool
- Consistent model configuration
- Cost optimization

### 3. State Bridge

Создается адаптер между состояниями:
- `AgentState` (Cognitive OS) ↔ `AdversarialAgentState` (Agent Team)
- Автоматическая конвертация на входе/выходе

---

## 📋 План реализации

### Phase 1: Foundation
1. ✅ **State Adapter** - конвертация состояний
2. ✅ **Memory Integration** - добавить memory_manager во все agents
3. ✅ **LLM Sharing** - передавать llm_provider в agents

### Phase 2: Execute Enhancement
4. ✅ **Complexity Detection** - analyze node классифицирует сложность
5. ✅ **Unified Executor** - роутинг standard/adversarial
6. ✅ **Execute Node Update** - использует Unified Executor

### Phase 3: Graph Integration
7. ✅ **Graph Builder Update** - инициализирует adversarial graph
8. ✅ **Main Entry Point** - unified initialization

### Phase 4: Testing
9. ✅ **Integration Tests** - оба режима execution
10. ✅ **Examples** - демо integrated flow

---

## 💡 Ключевые преимущества

### ✅ Гибкость
- Простые задачи → Быстро (standard LLM)
- Сложные задачи → Качественно (adversarial team)

### ✅ Эффективность
- Единый Memory Manager
- Единый LLM Provider
- Избегаем дублирования

### ✅ Качество
- Memory invariants работают для всех агентов
- Validated knowledge pipeline intact
- Audit trail полный

### ✅ Масштабируемость
- Добавлять новые agent pairs легко
- Cognitive OS независим от agent team
- Clear separation of concerns

---

## 📁 Структура файлов

### Новые файлы
```
src/xteam_agents/integration/
├── __init__.py
├── state_adapter.py      # AgentState ↔ AdversarialAgentState
├── executor.py           # Unified executor with routing
└── orchestration.py      # Top-level orchestration
```

### Модифицируемые файлы
```
src/xteam_agents/
├── agents/
│   ├── base.py                  # + memory_manager parameter
│   ├── orchestrator.py          # + memory_manager parameter
│   ├── adversarial_graph.py     # + llm_provider, memory_manager
│   └── nodes/pairs/*.py         # + memory_manager parameter
├── graph/
│   ├── builder.py               # + adversarial_graph initialization
│   └── nodes/
│       ├── analyze.py           # + complexity classification
│       └── execute.py           # + unified executor routing
└── __main__.py                  # + unified initialization
```

---

## 🚀 Следующие шаги

**Option A: Полная реализация (4 дня)**
- Реализовать все 4 фазы последовательно
- End-to-end testing
- Production ready

**Option B: MVP реализация (1 день)**
- Phase 1 + Phase 2 (core functionality)
- Basic integration test
- Proof of concept

**Option C: Пошаговая реализация**
- Делать по одной фазе с review
- Incremental testing
- Safe rollout

---

## 📄 Документация

Полная архитектура: **[INTEGRATION_ARCHITECTURE.md](./INTEGRATION_ARCHITECTURE.md)**

Включает:
- Detailed component diagrams
- Complete execution flow
- Implementation details
- Code snippets
- Testing strategy

---

**Готов начать реализацию?** Выберите опцию (A, B, или C).
