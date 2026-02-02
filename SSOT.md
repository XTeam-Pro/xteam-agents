# XTeam-agents MCP Server - Technical Specification (SSOT)

**Project:** XTeam-agents  
**System Role:** Cognitive Operating System (Multi-Agent)  
**Architecture:** Multi-Agent Cognitive Graph  
**Frameworks:** LangGraph, LangChain, FastMCP  
**Language:** Python 3.11+  
**Status:** APPROVED FOR DEVELOPMENT  
**Document Type:** Single Source of Truth (SSOT)

## 0. Назначение документа

Настоящее ТЗ определяет архитектуру, компоненты, правила и порядок реализации системы XTeam-agents MCP Server.

Документ предназначен для:
*   Backend Engineers
*   AI / ML Engineers
*   DevOps Engineers

**Любые архитектурные решения вне данного документа считаются недопустимыми, если не зафиксированы как официальные изменения.**

---

## 1. Концепция системы (Executive Summary)

XTeam-agents — это **когнитивная операционная система**, а не чат-бот и не набор инструментов.

Система реализует **замкнутый когнитивный цикл**:
`Наблюдение → Анализ → План → Действие → Проверка → Память → Адаптация`

**Ключевая цель:**
*   воспроизводимые решения,
*   управляемая коллективная память,
*   отсутствие «галлюцинаций»,
*   строгая валидация перед фиксацией знаний.

---

## 2. Когнитивная архитектура (Canonical Model)

Система состоит из пяти фундаментальных слоёв:

| Слой | Назначение |
| :--- | :--- |
| **Perception Layer** | Органы чувств (наблюдение мира) |
| **LangGraph** | Скелет (управление процессом мышления) |
| **LangChain** | Нервная система (LLM + сигналы) |
| **Action Layer** | Мышцы (контролируемые действия) |
| **MemoryManager** | Долговременная память |

---

## 3. Базовые архитектурные принципы (НЕ НАРУШАЕМЫЕ)

1.  **Memory-First Design**
    *   Память первична, вычисления вторичны.
2.  **Zero-Trust to Agents**
    *   Агенты **не имеют прямого доступа** к БД.
3.  **Single Write Point to Shared Memory**
    *   Shared Memory пишется **только** в commit-узле.
4.  **Strict Validation Before Knowledge**
    *   Ничто не становится знанием без валидации.
5.  **Explainability by Design**
    *   Любое знание должно быть объяснимо.

---

## 4. Perception Layer (Органы чувств)

### 4.1 Назначение
Perception Layer отвечает за **получение фактов о мире**, не полученных через LLM-рассуждение.
Это **наблюдения**, а не интерпретации.

### 4.2 Типы сенсоров

#### 4.2.1 System Sensors
*   состояние задач;
*   зависания;
*   превышение бюджета;
*   ошибки памяти.

#### 4.2.2 Environment Sensors
*   ответы API;
*   CI / build-статусы;
*   изменения Git;
*   пользовательская обратная связь.

#### 4.2.3 Temporal Sensors
*   дедлайны;
*   таймауты;
*   cron-события.

### 4.3 Контракт Observation

```python
class Observation(BaseModel):
    observation_id: UUID
    source: str
    category: Literal["system", "environment", "temporal"]
    signal: str
    confidence: float
    task_id: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]
```

**Инварианты:**
*   Observation не использует LLM.
*   Observation не пишет напрямую в память.
*   Observation может инициировать новый цикл анализа.

---

## 5. Оркестрация (LangGraph)

### 5.1 Роль LangGraph
LangGraph — **единственный допустимый механизм управления процессом мышления**.
FSM, while-циклы и ручная оркестрация **запрещены**.

### 5.2 Состояние (State Schema)

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

    task_id: str
    current_phase: str  # ANALYZE | PLAN | EXECUTE | VALIDATE | COMMIT

    plan: Optional[List[str]]
    code_artifacts: Optional[dict]
    validation_report: Optional[str]

    memory_scope: str        # default: private
    is_validated: bool       # default: False
```

### 5.3 Узлы графа (обязательные)

1.  **analyze_node (Analyst)**
    *   читает semantic + procedural память;
    *   формирует контекст знаний.
2.  **plan_node (Architect)**
    *   декомпозирует задачу;
    *   формирует план.
3.  **execute_node (Worker)**
    *   выполняет план;
    *   пишет только **private / episodic**.
4.  **validate_node (Reviewer)**
    *   запускает тесты;
    *   проверяет требования;
    *   выставляет `is_validated`.
5.  **commit_node (System)**
    *   единственная точка записи в **shared**;
    *   переносит данные в semantic / procedural.

### 5.4 Цикл коррекции (обязателен)

```
Analyze → Plan → Execute → Validate
                ↑        ↓
             Re-Plan ← Failed
```

---

## 6. Memory Subsystem (MemoryManager)

### 6.1 Типы памяти

| Тип | Назначение | Технология |
| :--- | :--- | :--- |
| **Episodic** | Контекст, логи | Redis |
| **Semantic** | Подтверждённые знания | Qdrant |
| **Procedural** | Паттерны и workflow | Neo4j |
| **Audit** | Трассировка | PostgreSQL |

### 6.2 MemoryArtifact

```python
class MemoryArtifact(BaseModel):
    id: UUID
    content: str
    source_agent: str
    task_id: str
    type: Literal["episodic", "semantic", "procedural"]
    scope: Literal["private", "shared"]
    is_validated: bool
    metadata: Dict[str, Any]
```

### 6.3 Правила записи
*   **episodic** → можно без валидации
*   **semantic** → только shared + validated
*   **procedural** → только commit node

---

## 7. Action Layer (Мышцы)

### 7.1 Назначение
Action Layer — **контролируемое исполнение**, а не вызов tool.

### 7.2 ActionExecutor
Отдельный компонент для:
*   выполнения кода;
*   HTTP / shell;
*   CI / n8n / deployment.

**LLM не выполняет действий напрямую**.

### 7.3 Capability Registry (обязательно)

```python
class Capability(BaseModel):
    name: str
    inputs: List[str]
    effects: List[str]
    rollback_supported: bool
    risk_level: Literal["low", "medium", "high"]
```

**Без регистрации capability → действие запрещено.**

### 7.4 ActionResult

```python
class ActionResult(BaseModel):
    action_id: UUID
    success: bool
    measurable_effect: str
    logs: str
    duration_ms: int
```

---

## 8. Интеграция LangChain

*   LangChain используется **только внутри узлов**.
*   `temperature = 0` (детерминизм).
*   `write_shared_memory` tool **запрещён**.

---

## 9. Инфраструктура (Docker)

**Обязательные сервисы:**
*   mcp-server (Python)
*   redis
*   qdrant
*   neo4j
*   postgres
*   n8n

**Запуск:**
```bash
docker compose up -d
```

---

## 10. Безопасность

**Запрещено:**
*   прямой доступ агентов к БД;
*   запись в shared вне commit node;
*   выполнение не зарегистрированных действий.

---

## 11. План реализации

| День | Результат |
| :--- | :--- |
| 1 | Инфраструктура |
| 2–3 | MemoryManager |
| 4–5 | LangGraph nodes |
| 6 | MCP API + streaming |

---

## 12. Критерии приёмки (Definition of Done)

Система принимается, если:
1.  знания появляются только после commit;
2.  рестарт сервера не теряет задачу;
3.  validation реально блокирует ошибки;
4.  каждое знание объяснимо.

---

## 13. Итоговая формула системы

**Perception → Cognition → Action → Memory → Adaptation**

Это и есть **Cognitive Operating System**, а не агент-чат.
