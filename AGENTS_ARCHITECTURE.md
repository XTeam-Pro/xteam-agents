# Agent Team Architecture

## Overview

Полноценная команда из 10 специализированных AI агентов для enterprise-grade разработки ПО.

## Agent Roster

### 🧠 TechLeadAgent (Главный)
**Role**: Technical Leadership & Decision Authority
**Responsibilities**:
- Классификация и фреймирование задач
- Технические решения и долгосрочная целостность системы
- Формирование архитектурных рамок
- Валидация требований
- Выявление рисков
- Утверждение/отклонение решений других агентов
- Финальный гейт всех изменений

**Tools**: read_all_memories, write_episodic, escalate_to_user, approve_decision, reject_decision

---

### 🏗 ArchitectAgent
**Role**: System Architecture Design
**Responsibilities**:
- Проектирование системной архитектуры на уровне компонентов
- Определение границ систем и контекстов
- Взаимодействие сервисов
- Эволюция архитектуры
- Выявление точек отказа

**Tools**: read_all_memories, write_episodic, create_architecture_diagram, validate_boundaries

---

### ⚙ BackendAgent
**Role**: Business Logic Implementation
**Responsibilities**:
- Серверный код и API
- Интеграции
- Строгое следование контрактам
- Реализация бизнес-логики

**Tools**: read_all_memories, write_episodic, execute_code, run_tests, create_api

---

### 🎨 FrontendAgent
**Role**: User Interface & Client Logic
**Responsibilities**:
- UX реализация
- Управление состоянием клиента
- Производительность фронтенда
- Доступность (accessibility)
- Работа без предположений о backend

**Tools**: read_all_memories, write_episodic, execute_code, run_tests, preview_ui

---

### 🗄 DataAgent
**Role**: Data Architecture & Optimization
**Responsibilities**:
- Проектирование схем БД
- Миграции данных
- Индексы и оптимизация запросов
- Целостность данных
- Масштабируемость хранилищ

**Tools**: read_all_memories, write_episodic, create_migration, analyze_queries, validate_schema

---

### 🚀 DevOpsAgent
**Role**: Operations & Infrastructure
**Responsibilities**:
- CI/CD пайплайны
- Деплой стратегии
- Мониторинг и логирование
- Бэкапы и disaster recovery
- Стратегии отката

**Tools**: read_all_memories, write_episodic, deploy_service, setup_monitoring, create_pipeline

---

### 🧪 QAAgent
**Role**: Quality Assurance & Testing
**Responsibilities**:
- Поиск ошибок и крайних случаев
- Скрытые дефекты
- Проверка корректности
- Устойчивость системы
- Соответствие требованиям

**Tools**: read_all_memories, write_episodic, run_tests, analyze_coverage, find_edge_cases

---

### 🤖 AIAgentArchitect
**Role**: AI Systems Architecture
**Responsibilities**:
- Проектирование AI и agent-based подсистем
- Агентная архитектура
- Взаимодействие LLM
- Orchestration, memory, tools
- Ограничения безопасности ИИ

**Tools**: read_all_memories, write_episodic, design_agent_system, configure_llm, validate_ai_safety

---

### 🔐 SecurityAgent
**Role**: Security & Compliance
**Responsibilities**:
- Анализ угроз и уязвимостей
- Модели доступа
- Модели атак
- Соответствие требованиям безопасности
- Аудит безопасности

**Tools**: read_all_memories, write_episodic, scan_vulnerabilities, validate_permissions, audit_access

---

### ⚡ PerformanceAgent
**Role**: Performance Optimization
**Responsibilities**:
- Оптимизация производительности
- Устойчивость под нагрузкой
- Выявление узких мест
- Анализ latency, throughput, ресурсов
- Предложения оптимизаций

**Tools**: read_all_memories, write_episodic, profile_performance, analyze_bottlenecks, load_test

---

## RACI Matrix

| Область | TechLead | Architect | Backend | Frontend | Data | DevOps | QA | AI Arch | Security | Perf |
|---------|----------|-----------|---------|----------|------|--------|----|---------| ---------|------|
| Архитектура системы | **A** | **R** | I | I | C | C | I | C | C | C |
| Бизнес-требования | **A/R** | C | I | I | I | I | I | I | I | I |
| Выбор технологий | **A** | **R** | C | C | C | C | I | C | C | C |
| Backend логика | A | I | **R** | I | C | I | C | I | I | C |
| Frontend / UX | A | I | C | **R** | I | I | C | I | I | C |
| Data model | A | C | C | I | **R** | I | C | I | C | C |
| AI архитектура | A | C | I | I | I | I | I | **R** | C | C |
| CI/CD / Infra | A | I | I | I | I | **R** | I | I | C | C |
| Безопасность | A | C | I | I | C | C | I | C | **R** | I |
| Производительность | A | C | C | C | C | C | I | C | I | **R** |
| Тестирование | A | I | C | C | C | C | **R** | I | C | C |
| Финальный гейт | **A/R** | I | I | I | I | I | I | I | I | I |

**Legend**:
- **R** = Responsible (делает)
- **A** = Accountable (утверждает)
- **C** = Consulted (консультирует)
- **I** = Informed (уведомляется)

---

## Routing Rules

### Global Rule
```
ALL tasks → TechLeadAgent (classification & framing)
```

### Task-Specific Routing

#### Architecture
```
IF task.affects_architecture OR system_boundaries OR service_design
  → ArchitectAgent
  → TechLeadAgent (approval)
```

#### Backend
```
IF task.backend_logic OR API OR integrations
  → BackendAgent
```

#### Frontend
```
IF task.ui OR ux OR client_state
  → FrontendAgent
```

#### Data
```
IF task.db_schema OR migrations OR queries OR data_volume
  → DataAgent
```

#### AI/Agents
```
IF task.llm OR agents OR orchestration OR memory OR tools
  → AIAgentArchitect
```

#### DevOps
```
IF task.deploy OR ci_cd OR infra OR monitoring OR rollback
  → DevOpsAgent
```

#### Security
```
IF task.auth OR permissions OR sensitive_data OR external_access
  → SecurityAgent
```

#### Performance
```
IF task.performance OR latency OR throughput OR load
  → PerformanceAgent
```

#### QA
```
IF feature_complete OR release_candidate
  → QAAgent
```

---

## Escalation Rules

```
ANY agent MAY escalate to TechLeadAgent IF:
- Requirements are ambiguous
- Architecture constraints are violated
- Security or scaling risk is detected
- Decision is hard to reverse
- Cross-system impact
- Technical debt implications
```

---

## Canonical Flow

```
User / Product Requirement
   ↓
TechLeadAgent (scope, risks, constraints, routing decision)
   ↓
┌────────────────────────────────────┐
│ Thinking Agents (parallel)         │
│ - ArchitectAgent                   │
│ - AIAgentArchitect (if AI-related) │
│ - SecurityAgent (if sensitive)     │
│ - PerformanceAgent (if critical)   │
└────────────────────────────────────┘
   ↓
┌────────────────────────────────────┐
│ Execution Agents (parallel)        │
│ - BackendAgent                     │
│ - FrontendAgent                    │
│ - DataAgent                        │
│ - DevOpsAgent                      │
└────────────────────────────────────┘
   ↓
QAAgent (validation & testing)
   ↓
TechLeadAgent (FINAL APPROVAL & COMMIT)
```

---

## Immutable Context Rule

**Critical Constraint**:
- Вывод **TechLeadAgent** → **immutable context**
- Другие агенты **НЕ ИМЕЮТ ПРАВА**:
  - Менять архитектуру
  - Обходить ограничения
  - Принимать новые tech decisions
  - Изменять scope

**Exception**: Эскалация к TechLeadAgent для переоценки

---

## Decision Heuristic

```
IF decision is:
  - Irreversible OR
  - Expensive OR
  - Cross-system OR
  - Security-critical OR
  - Performance-critical
THEN
  → MUST escalate to TechLeadAgent
```

---

## State Management

### Agent State Schema
```python
class AgentTeamState:
    task_id: str
    original_request: str
    tech_lead_decision: TechLeadDecision  # IMMUTABLE after set
    architecture_plan: Optional[ArchitecturePlan]
    security_clearance: Optional[SecurityClearance]
    performance_requirements: Optional[PerformanceRequirements]

    # Execution outputs
    backend_output: Optional[BackendOutput]
    frontend_output: Optional[FrontendOutput]
    data_output: Optional[DataOutput]
    devops_output: Optional[DevOpsOutput]

    # QA results
    qa_results: Optional[QAResults]

    # Final
    final_approval: Optional[FinalApproval]
    artifacts: List[Artifact]
```

---

## Communication Protocol

### 1. Agent-to-Agent Communication
Agents communicate via **shared state** only. No direct messages.

### 2. Escalation Protocol
```python
{
  "type": "ESCALATION",
  "from_agent": "BackendAgent",
  "to_agent": "TechLeadAgent",
  "reason": "Architecture constraint violation detected",
  "context": {...},
  "proposed_solution": "..."
}
```

### 3. Approval Protocol
```python
{
  "type": "APPROVAL_REQUEST",
  "from_agent": "ArchitectAgent",
  "decision": "Change database from PostgreSQL to Cassandra",
  "rationale": "...",
  "impact_analysis": {...}
}
```

---

## Implementation Strategy

### Phase 1: Core Agents (Week 1)
- TechLeadAgent
- ArchitectAgent
- BackendAgent
- QAAgent

### Phase 2: Specialized Agents (Week 2)
- DataAgent
- SecurityAgent
- PerformanceAgent

### Phase 3: Advanced Agents (Week 3)
- FrontendAgent
- DevOpsAgent
- AIAgentArchitect

### Phase 4: Integration & Optimization (Week 4)
- Full workflow testing
- Performance tuning
- Documentation

---

## Metrics & Observability

### Agent Performance Metrics
- Decision quality score
- Escalation rate
- Average task completion time
- Error detection rate (QA)
- Architecture violation prevention rate

### System Metrics
- End-to-end task completion time
- Agent utilization
- Escalation overhead
- Final approval rate
- Rollback rate

---

## Safety & Guardrails

### 1. No Agent Can:
- Directly commit to shared memory (only TechLeadAgent via commit_node)
- Override TechLeadAgent decisions
- Skip QA validation
- Deploy without DevOpsAgent approval
- Modify security policies without SecurityAgent review

### 2. Required Validations:
- All code changes → QAAgent review
- All architecture changes → ArchitectAgent + TechLeadAgent approval
- All security changes → SecurityAgent review
- All performance-critical changes → PerformanceAgent analysis

### 3. Automatic Rollback Triggers:
- QA failure
- Security vulnerability detected
- Performance regression > 20%
- Architecture constraint violation

---

## Example Scenarios

### Scenario 1: Add New API Endpoint
```
User: "Add GET /api/users/:id endpoint"
  → TechLeadAgent: classify as "backend API task"
  → BackendAgent: implement endpoint
  → QAAgent: test endpoint
  → TechLeadAgent: approve & commit
```

### Scenario 2: Redesign Database Schema
```
User: "Optimize user table for 10M records"
  → TechLeadAgent: classify as "architecture + data + performance"
  → ArchitectAgent: analyze impact on system boundaries
  → DataAgent: design schema changes
  → PerformanceAgent: validate performance requirements
  → BackendAgent: implement changes
  → DevOpsAgent: plan migration strategy
  → QAAgent: validate data integrity
  → TechLeadAgent: approve & commit
```

### Scenario 3: Security Issue
```
SecurityAgent: detects SQL injection vulnerability
  → ESCALATE to TechLeadAgent
  → TechLeadAgent: classify as "critical security fix"
  → SecurityAgent: propose fix
  → BackendAgent: implement fix
  → QAAgent: validate fix
  → DevOpsAgent: deploy hotfix
  → TechLeadAgent: approve & commit
```

---

## Configuration

### Agent LLM Models
```yaml
tech_lead: claude-opus-4-5  # Strongest reasoning
architect: claude-sonnet-4-5  # Good reasoning, cost-effective
backend: claude-sonnet-4-5
frontend: claude-sonnet-4-5
data: claude-sonnet-4-5
devops: claude-sonnet-4-5
qa: claude-sonnet-4-5
ai_architect: claude-opus-4-5  # Complex AI reasoning
security: claude-opus-4-5  # Critical decisions
performance: claude-sonnet-4-5
```

### Agent Temperatures
```yaml
tech_lead: 0.3  # Conservative decisions
architect: 0.5  # Balanced creativity
backend: 0.2  # Precise implementation
frontend: 0.4  # Some creativity for UX
data: 0.2  # Precise schema design
devops: 0.3  # Reliable infrastructure
qa: 0.1  # Strict testing
ai_architect: 0.5  # Creative AI solutions
security: 0.1  # No risks
performance: 0.3  # Methodical optimization
```

---

## Next Steps

1. Implement agent graph structure
2. Create routing logic
3. Implement escalation mechanism
4. Add RACI validation
5. Create agent-specific tools
6. Build monitoring dashboard
7. Write comprehensive tests
8. Deploy to production
