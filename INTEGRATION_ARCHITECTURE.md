# 🔗 Integration Architecture: Cognitive OS + Adversarial Agent Team

## 📊 Текущее состояние

### 1. Cognitive Operating System (Существующий)

**Компоненты:**
- **Memory Manager**: 4 бэкенда (Episodic/Redis, Semantic/Qdrant, Procedural/Neo4j, Audit/PostgreSQL)
- **LangGraph**: analyze → plan → execute → validate → commit → reflect
- **Memory Invariants**: Только commit_node пишет в shared memory
- **LLM Provider**: Интеграция с OpenAI/Anthropic
- **Action Executor**: Выполнение действий (HTTP, Shell, Code, CI)
- **MCP Server**: Model Context Protocol

**Граф:**
```
START → [analyze] → [plan] → [execute] → [validate] → [commit] → [reflect] → END
                       ↑                                   │
                       └────────── (replan) ──────────────┘
```

### 2. Adversarial Agent Team (Новый)

**Компоненты:**
- **OrchestratorAgent**: Классификация, routing, conflict resolution
- **10 Agent-Critic Pairs**: TechLead, Architect, Backend, Frontend, Data, DevOps, QA, AIArchitect, Security, Performance
- **Pair Interaction Manager**: Итеративное улучшение (до 5 раундов)
- **5D Quality Scoring**: Correctness, Completeness, Quality, Performance, Security
- **Conflict Resolution**: Эскалация к Orchestrator

**Граф:**
```
Task → [Orchestrator Classify] → [Execute Pairs] → [Resolve Conflicts] → [Final Decision]
                                         ↑                │
                                         └── (iterate) ───┘
```

---

## 🎯 Целевая архитектура интеграции

### Принцип интеграции

**Adversarial Agent Team работает ВНУТРИ Cognitive OS как специализированный исполнитель для сложных задач.**

```
┌─────────────────────────────────────────────────────────────────┐
│                     COGNITIVE OPERATING SYSTEM                   │
│  ┌──────────┐   ┌──────┐   ┌─────────┐   ┌──────────┐          │
│  │ analyze  │ → │ plan │ → │ execute │ → │ validate │ → ...    │
│  └──────────┘   └──────┘   └─────────┘   └──────────┘          │
│                               │    ↑                              │
│                               ↓    │                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │          ADVERSARIAL AGENT TEAM (Optional)                 │ │
│  │  ┌──────────────┐   ┌─────────────┐   ┌────────────────┐ │ │
│  │  │ Orchestrator │ → │ Agent Pairs │ → │ Final Decision │ │ │
│  │  └──────────────┘   └─────────────┘   └────────────────┘ │ │
│  │         ↓                  ↓                    ↓          │ │
│  │    Memory Manager    Memory Manager     Memory Manager    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                               │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    SHARED MEMORY LAYER                     │ │
│  │  Redis │ Qdrant │ Neo4j │ PostgreSQL │ Task State         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Ключевые решения

#### 1. **Когда использовать Adversarial Team?**

**Критерии активации:**
- Задача классифицируется как `complex` или `critical` в analyze node
- Требуется architectural decision
- Требуется code review высокого качества
- Требуется security audit
- Требуется performance optimization

**Типы задач:**
- `simple` → Стандартный execute node (один LLM call)
- `medium` → Execute node с validation
- `complex` → Adversarial Team (Agent-Critic pairs)
- `critical` → Full Adversarial Team + Extended validation

#### 2. **Точка интеграции: Execute Node**

Execute node будет иметь два режима:

**A. Standard Mode (существующий)**
```python
async def execute_standard(state: AgentState) -> dict:
    # Простое выполнение для простых задач
    result = await llm_provider.generate(...)
    return {"execution_result": result}
```

**B. Adversarial Mode (новый)**
```python
async def execute_adversarial(state: AgentState) -> dict:
    # Запускаем Adversarial Agent Team
    adversarial_state = create_adversarial_state(state)
    team_result = await adversarial_graph.ainvoke(adversarial_state)

    # Синхронизируем результаты обратно в AgentState
    return merge_adversarial_results(team_result, state)
```

#### 3. **State Bridge: AgentState ↔ AdversarialAgentState**

Создадим адаптеры для конвертации состояний:

```python
class StateAdapter:
    @staticmethod
    def to_adversarial(agent_state: AgentState) -> AdversarialAgentState:
        """Convert AgentState → AdversarialAgentState"""
        return AdversarialAgentState(
            task_id=str(agent_state.task_id),
            original_request=agent_state.description,
            context=agent_state.context,
            # Map other fields...
        )

    @staticmethod
    def from_adversarial(
        adversarial_state: AdversarialAgentState,
        original_state: AgentState
    ) -> dict:
        """Extract results from AdversarialAgentState → AgentState updates"""
        return {
            "execution_result": adversarial_state.orchestrator_final_decision.rationale,
            "artifacts": adversarial_state.orchestrator_final_decision.artifacts_to_commit,
            "is_validated": adversarial_state.orchestrator_final_decision.approved,
            # Map pair results to subtasks...
        }
```

#### 4. **Memory Integration**

**Все агенты используют ОДИН MemoryManager:**

```python
# In BaseAgent and BaseCritic
class BaseAgent:
    def __init__(self, config: AgentConfig, settings: Settings, memory_manager: MemoryManager):
        self.config = config
        self.settings = settings
        self.memory_manager = memory_manager  # ← Shared instance
        self.llm = self._create_llm()
```

**Правила памяти:**
- **Agent/Critic работа** → Episodic memory (private, short-term)
- **Approved pairs** → Validation, затем commit_node → Shared memory
- **Audit trail** → Все действия логируются через MemoryManager

**Поток памяти:**
```
1. Orchestrator classify → Audit log
2. Agent execute → Episodic memory (draft)
3. Critic evaluate → Episodic memory (review)
4. If approved → Mark for commit
5. Cognitive OS validate node → Validates all pair results
6. Cognitive OS commit node → Shared memory (Semantic + Procedural)
```

#### 5. **LLM Provider Sharing**

Единый LLMProvider для всех агентов:

```python
# Initialize once
llm_provider = LLMProvider(settings)

# Share with cognitive graph
cognitive_graph = build_cognitive_graph(settings, llm_provider, memory_manager, action_executor)

# Share with adversarial team
orchestrator = OrchestratorAgent(settings, llm_provider, memory_manager)
pairs = initialize_agent_pairs(settings, llm_provider, memory_manager)
```

---

## 🏗️ Архитектура компонентов

### Новая структура каталогов

```
src/xteam_agents/
├── memory/              # ✅ Существующий - Memory Manager
├── llm/                 # ✅ Существующий - LLM Provider
├── models/              # ✅ Существующий - State, Memory models
├── action/              # ✅ Существующий - Action Executor
├── graph/               # ✅ Существующий - Cognitive Graph
│   ├── builder.py       # Модифицировать: добавить adversarial mode
│   └── nodes/
│       ├── execute.py   # Модифицировать: добавить adversarial routing
│       └── ...
├── agents/              # ✅ Существующий - Adversarial Team
│   ├── orchestrator.py
│   ├── base.py          # Модифицировать: добавить memory_manager
│   ├── pair_manager.py
│   ├── adversarial_graph.py
│   └── nodes/pairs/
│       └── *.py         # Модифицировать: добавить memory_manager
└── integration/         # 🆕 Новый - Integration layer
    ├── __init__.py
    ├── state_adapter.py # State conversion
    ├── executor.py      # Unified executor with routing
    └── orchestration.py # Top-level orchestration
```

---

## 🔄 Execution Flow

### Полный поток выполнения

```
1. User Request → Cognitive OS
   ↓
2. [analyze node]
   - Анализирует задачу
   - Определяет сложность (simple, medium, complex, critical)
   - Записывает в Episodic memory
   ↓
3. [plan node]
   - Создает plan
   - Разбивает на subtasks
   - Определяет нужны ли Agent Pairs для каждой subtask
   ↓
4. [execute node] ← ТОЧКА ИНТЕГРАЦИИ

   IF task.complexity in ['simple', 'medium']:
       → Standard execution
       → LLM generates result

   ELSE IF task.complexity in ['complex', 'critical']:
       → Adversarial execution
       ├─ Convert AgentState → AdversarialAgentState
       ├─ Run Adversarial Agent Team:
       │  ├─ Orchestrator classifies & selects pairs
       │  ├─ Execute pairs (iterative Agent-Critic)
       │  │  ├─ Each agent writes to Episodic memory
       │  │  ├─ Each critic evaluates (5D scoring)
       │  │  └─ Iterate until approved or escalate
       │  ├─ Resolve conflicts (if any)
       │  └─ Orchestrator makes final decision
       ├─ Convert AdversarialAgentState → AgentState updates
       └─ Return enriched execution result
   ↓
5. [validate node]
   - Validates execution result
   - Checks artifacts in Episodic memory
   - Marks artifacts for commit if valid
   ↓
6. [commit node] (ONLY node that writes to shared memory)
   - Takes validated artifacts from Episodic
   - Commits to Shared memory (Semantic + Procedural)
   - Audit log
   ↓
7. [reflect node]
   - Summarizes execution
   - Stores lessons learned
   ↓
8. END
```

---

## 📋 Implementation Plan

### Phase 1: Foundation (Day 1)

#### Task 1.1: State Adapter
**File:** `src/xteam_agents/integration/state_adapter.py`

```python
from xteam_agents.models.state import AgentState
from xteam_agents.agents.adversarial_state import AdversarialAgentState

class StateAdapter:
    @staticmethod
    def to_adversarial(state: AgentState) -> AdversarialAgentState:
        """Convert AgentState to AdversarialAgentState"""
        pass

    @staticmethod
    def from_adversarial(
        adv_state: AdversarialAgentState,
        original: AgentState
    ) -> dict:
        """Extract updates from AdversarialAgentState"""
        pass
```

#### Task 1.2: Memory Manager Integration
**Files to modify:**
- `src/xteam_agents/agents/base.py`
- `src/xteam_agents/agents/orchestrator.py`
- `src/xteam_agents/agents/nodes/pairs/*.py`

**Changes:**
```python
# Add memory_manager parameter to all agents
class BaseAgent:
    def __init__(
        self,
        config: AgentConfig,
        settings: Settings,
        memory_manager: MemoryManager  # ← Add this
    ):
        self.memory_manager = memory_manager
```

#### Task 1.3: LLM Provider Sharing
**File to modify:** `src/xteam_agents/agents/adversarial_graph.py`

```python
class AdversarialGraphBuilder:
    def __init__(
        self,
        settings: Settings,
        llm_provider: LLMProvider,      # ← Add this
        memory_manager: MemoryManager   # ← Add this
    ):
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
```

### Phase 2: Execute Node Enhancement (Day 2)

#### Task 2.1: Complexity Detection
**File to modify:** `src/xteam_agents/graph/nodes/analyze.py`

Add complexity classification:
```python
async def analyze_node(state: AgentState) -> dict:
    # ... existing analysis ...

    # Add complexity classification
    complexity = await classify_complexity(state.description, llm_provider)

    return {
        "analysis": analysis_result,
        "context": {
            **state.context,
            "complexity": complexity  # ← Add this
        }
    }
```

#### Task 2.2: Unified Executor
**File:** `src/xteam_agents/integration/executor.py`

```python
class UnifiedExecutor:
    """Unified executor that routes to standard or adversarial mode."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        memory_manager: MemoryManager,
        action_executor: ActionExecutor,
        adversarial_graph: StateGraph,
        settings: Settings
    ):
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
        self.action_executor = action_executor
        self.adversarial_graph = adversarial_graph
        self.settings = settings

    async def execute(self, state: AgentState) -> dict:
        complexity = state.context.get("complexity", "simple")

        if complexity in ["complex", "critical"]:
            return await self.execute_adversarial(state)
        else:
            return await self.execute_standard(state)

    async def execute_standard(self, state: AgentState) -> dict:
        # Existing standard execution logic
        pass

    async def execute_adversarial(self, state: AgentState) -> dict:
        # Convert state
        adv_state = StateAdapter.to_adversarial(state)

        # Run adversarial team
        result = await self.adversarial_graph.ainvoke(adv_state)

        # Convert back
        updates = StateAdapter.from_adversarial(result, state)

        return updates
```

#### Task 2.3: Modify Execute Node
**File to modify:** `src/xteam_agents/graph/nodes/execute.py`

Replace direct execution with UnifiedExecutor:
```python
def create_execute_node(
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
    action_executor: ActionExecutor,
    adversarial_graph: StateGraph,  # ← Add this
    settings: Settings
):
    executor = UnifiedExecutor(
        llm_provider,
        memory_manager,
        action_executor,
        adversarial_graph,
        settings
    )

    async def execute_node(state: AgentState) -> dict:
        return await executor.execute(state)

    return execute_node
```

### Phase 3: Graph Integration (Day 3)

#### Task 3.1: Update Graph Builder
**File to modify:** `src/xteam_agents/graph/builder.py`

```python
def build_cognitive_graph(
    settings: Settings,
    llm_provider: LLMProvider,
    memory_manager: MemoryManager,
    action_executor: ActionExecutor,
) -> StateGraph:
    # Build adversarial graph
    adversarial_graph = create_adversarial_graph(
        settings,
        llm_provider,
        memory_manager
    )

    # Create nodes (with adversarial support)
    execute_node = create_execute_node(
        llm_provider,
        memory_manager,
        action_executor,
        adversarial_graph,  # ← Pass adversarial graph
        settings
    )

    # ... rest of graph building
```

#### Task 3.2: Main Entry Point
**File to modify:** `src/xteam_agents/__main__.py`

Update initialization to create integrated system:
```python
async def main():
    settings = Settings()

    # Initialize shared components
    llm_provider = LLMProvider(settings)
    memory_manager = MemoryManager(settings)
    action_executor = ActionExecutor(settings)

    await memory_manager.connect()

    # Build integrated graph
    graph = build_cognitive_graph(
        settings,
        llm_provider,
        memory_manager,
        action_executor
    )

    # Execute
    result = await graph.ainvoke(initial_state)
```

### Phase 4: Testing & Documentation (Day 4)

#### Task 4.1: Integration Tests
**File:** `tests/integration/test_full_flow.py`

Test cases:
- Simple task → Standard execution
- Complex task → Adversarial execution
- Memory consistency across modes
- State conversion accuracy

#### Task 4.2: Example Scripts
**File:** `examples/integrated_execution.py`

Show both execution modes side-by-side

#### Task 4.3: Update Documentation
Update:
- `CLAUDE.md` - Development commands
- `AGENTS_README.md` - Integration architecture
- `README.md` - Quick start with new flow

---

## 🎯 Benefits

### 1. **Best of Both Worlds**
- **Cognitive OS**: Structured workflow, memory management, validation pipeline
- **Adversarial Team**: High-quality output through iterative refinement

### 2. **Flexible Complexity Handling**
- Simple tasks → Fast, lightweight
- Complex tasks → Thorough, high-quality

### 3. **Unified Memory**
- All agents use same MemoryManager
- Memory invariants enforced
- Complete audit trail

### 4. **Resource Efficiency**
- LLM Provider shared across all agents
- Avoid duplicate API calls
- Connection pooling

### 5. **Scalability**
- Add new agent pairs without changing Cognitive OS
- Modify Cognitive OS without affecting Agent Team
- Clear separation of concerns

---

## 🚀 Next Steps

1. **Review this architecture** - Get approval on integration approach
2. **Phase 1 Implementation** - Foundation components
3. **Phase 2 Implementation** - Execute node enhancement
4. **Phase 3 Implementation** - Full graph integration
5. **Phase 4 Testing** - End-to-end validation

Would you like me to proceed with implementation?
