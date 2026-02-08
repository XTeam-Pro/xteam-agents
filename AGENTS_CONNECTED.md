# XTeam Agents - Подключенные Агенты и MCP Инструменты

**Статус**: ✅ **ВСЕ АГЕНТЫ ПОДКЛЮЧЕНЫ И РАБОТАЮТ**
**MCP Server**: `https://mcp.agents.xteam.pro`
**Дата**: 2026-02-08

## 🤖 Архитектура Агентов

### 1. Cognitive OS (Когнитивная операционная система)

**5 основных когнитивных агентов**, работающих по validated knowledge pipeline:

```
START → analyze → plan → execute → validate → commit → END
           ↑                              ↓
           └───────── (replan) ───────────┘
```

| Агент | Роль | Доступ к памяти | Расположение кода |
|-------|------|-----------------|-------------------|
| **Analyst** | Анализ задач, сбор контекста | Read all, Write episodic | `src/xteam_agents/graph/nodes/analyze.py` |
| **Architect** | Планирование решений, создание планов | Read all, Write episodic | `src/xteam_agents/graph/nodes/plan.py` |
| **Worker** | Выполнение действий, использование инструментов | Read all, Write episodic | `src/xteam_agents/graph/nodes/execute.py` |
| **Reviewer** | Валидация результатов | Read all, Write episodic | `src/xteam_agents/graph/nodes/validate.py` |
| **Commit Node** | Сохранение валидированных знаний | **Write shared (Qdrant, Neo4j)** | `src/xteam_agents/graph/nodes/commit.py` |

**Критический инвариант**: Только Commit Node может писать в shared memory (Qdrant + Neo4j)

---

### 2. Adversarial Agent Team (Состязательная команда)

**21 агент** для высококачественного выполнения сложных задач:

#### 2.1 Orchestrator (Координатор)
- **Роль**: Верховный координатор, классификация задач, разрешение конфликтов
- **Код**: `src/xteam_agents/agents/orchestrator.py`
- **Стратегия**: Balanced - нейтральный координатор

#### 2.2 Agent-Critic Пары (10 пар, 20 агентов)

| Агент | Критик | Домен | Стратегия Критика | Код |
|-------|--------|-------|-------------------|-----|
| **TechLead** | TechLeadCritic | Технологические решения | Balanced | `nodes/pairs/tech_lead.py` |
| **Architect** | ArchitectCritic | Системная архитектура | Adversarial | `nodes/pairs/architect.py` |
| **Backend** | BackendCritic | Backend разработка | Balanced | `nodes/pairs/backend.py` |
| **Frontend** | FrontendCritic | Frontend разработка | Balanced | `nodes/pairs/frontend.py` |
| **Data** | DataCritic | Data engineering | Balanced | `nodes/pairs/data.py` |
| **DevOps** | DevOpsCritic | DevOps и инфраструктура | Balanced | `nodes/pairs/devops.py` |
| **QA** | QACritic | Тестирование и качество | **Perfectionist** | `nodes/pairs/qa.py` |
| **AIArchitect** | AIArchitectCritic | AI/ML системы | Balanced | `nodes/pairs/ai_architect.py` |
| **Security** (Blue Team) | SecurityCritic (Red Team) | Безопасность | **Adversarial** | `nodes/pairs/security.py` |
| **Performance** | PerformanceCritic | Производительность | **Adversarial** | `nodes/pairs/performance.py` |

**Стратегии критиков**:
- **Balanced**: Конструктивная критика с балансом между качеством и практичностью
- **Adversarial**: Агрессивный поиск проблем и уязвимостей
- **Perfectionist**: Максимальный фокус на качество, zero tolerance к дефектам

#### 2.3 5D Quality Scoring

Каждый результат оценивается по 5 измерениям:
- **Correctness** (Корректность): Соответствие требованиям
- **Completeness** (Полнота): Все ли аспекты покрыты
- **Quality** (Качество кода): Читаемость, стиль, best practices
- **Performance** (Производительность): Эффективность решения
- **Security** (Безопасность): Отсутствие уязвимостей

---

### 3. Research Team (Научно-исследовательская команда)

**14+ агентов** для образовательных исследований, разработки датасетов и нейронных моделей:

#### 3.1 Scientists (Ученые - 5 агентов)

| Агент | Роль | Экспертиза | Код |
|-------|------|------------|-----|
| **Chief Scientist** | Координатор исследований | Стратегия, методология | `agents/research_team/nodes/scientists/chief.py` |
| **Data Scientist** | Датасеты и аналитика | Learning Analytics, статистика | `agents/research_team/nodes/scientists/data.py` |
| **ML Researcher** | Нейронные модели | Knowledge Tracing, GNN, Transformers | `agents/research_team/nodes/scientists/ml.py` |
| **Cognitive Scientist** | Когнитивные процессы | Memory, attention, cognitive load | `agents/research_team/nodes/scientists/cognitive.py` |
| **Pedagogical Researcher** | Педагогика | Instructional design, assessment | `agents/research_team/nodes/scientists/pedagogical.py` |

#### 3.2 Methodologists (Методисты - 4 агента)

| Агент | Роль | Фокус | Код |
|-------|------|-------|-----|
| **Lead Methodologist** | Координатор методической работы | Curriculum, pedagogy | `agents/research_team/nodes/methodologists/lead.py` |
| **Curriculum Designer** | Дизайн учебных программ | Knowledge graphs, pathways | `agents/research_team/nodes/methodologists/curriculum.py` |
| **Assessment Designer** | Дизайн оценивания | Формативное/суммативное | `agents/research_team/nodes/methodologists/assessment.py` |
| **Adaptive Learning Specialist** | Адаптивное обучение | Персонализация, алгоритмы | `agents/research_team/nodes/methodologists/adaptive.py` |

#### 3.3 Content Team (Команда контента - 5 агентов)

| Агент | Роль | Специализация | Код |
|-------|------|---------------|-----|
| **Content Architect** | Архитектура контента | Структура, онтологии | `agents/research_team/nodes/content_team/architect.py` |
| **SME (Math)** | Эксперт по математике | K-12 математика | `agents/research_team/nodes/content_team/sme_math.py` |
| **SME (Science)** | Эксперт по наукам | Физика, химия, биология | `agents/research_team/nodes/content_team/sme_science.py` |
| **Dataset Engineer** | Инженерия датасетов | ETL, validation pipelines | `agents/research_team/nodes/content_team/dataset_engineer.py` |
| **Annotation Specialist** | Аннотация данных | Labeling, quality control | `agents/research_team/nodes/content_team/annotation.py` |

#### 3.4 Critics (Рецензенты)

По одному критику на каждого агента для peer review (14 критиков)

**Типы исследовательских задач**:
- Dataset Design/Collection/Annotation
- Model Architecture/Training/Evaluation
- Curriculum Design, Assessment Design
- Learning Analytics, A/B Testing
- Cognitive Analysis, Pedagogical Strategy

---

## 🛠 MCP Tools (29 инструментов)

### Task Management (5 инструментов)

| Tool | Описание | Параметры | Код |
|------|----------|-----------|-----|
| `submit_task` | Отправить новую задачу | description, priority, context, magic | `server/tools/task_tools.py:register_task_tools()` |
| `get_task_status` | Проверить статус задачи | task_id | `server/tools/task_tools.py` |
| `get_task_result` | Получить результат задачи | task_id | `server/tools/task_tools.py` |
| `cancel_task` | Отменить задачу | task_id | `server/tools/task_tools.py` |
| `list_tasks` | Список всех задач | status_filter | `server/tools/task_tools.py` |

### Memory & Knowledge (4 инструмента)

| Tool | Описание | Параметры | Код |
|------|----------|-----------|-----|
| `query_memory` | Поиск по всем типам памяти | query, memory_type, limit | `server/tools/memory_tools.py` |
| `search_knowledge` | Семантический поиск | query, limit, threshold | `server/tools/memory_tools.py` |
| `get_knowledge_graph` | Граф знаний для задачи | task_id | `server/tools/memory_tools.py` |
| `get_task_audit_log` | История выполнения | task_id | `server/tools/memory_tools.py` |

### MAGIC System (7 инструментов)

Human-AI Collaboration система:

| Tool | Описание | Параметры | Код |
|------|----------|-----------|-----|
| `configure_magic` | Настроить MAGIC для задачи | task_id, autonomy_level, confidence_threshold, checkpoints | `server/tools/magic_tools.py` |
| `list_pending_escalations` | Список ожидающих эскалаций | task_id | `server/tools/magic_tools.py` |
| `respond_to_escalation` | Ответить на эскалацию | escalation_id, response_type, content | `server/tools/magic_tools.py` |
| `submit_feedback` | Отправить обратную связь | task_id, feedback_type, content, rating | `server/tools/magic_tools.py` |
| `get_confidence_scores` | Получить оценки уверенности | task_id | `server/tools/magic_tools.py` |
| `get_magic_session` | Состояние коллаборативной сессии | session_id | `server/tools/magic_tools.py` |
| `get_evolution_metrics` | Метрики прогресса автономности | - | `server/tools/magic_tools.py` |

**MAGIC Autonomy Levels**:
- `supervised`: Каждое действие требует одобрения
- `guided`: Важные решения требуют одобрения
- `collaborative`: Сбалансированный режим (по умолчанию)
- `autonomous`: Высокая автономность
- `trusted`: Максимальная автономность

### Code Tools (4 инструмента)

| Tool | Описание | Параметры | Код |
|------|----------|-----------|-----|
| `execute_python` | Выполнить Python код | code, timeout | `server/tools/code_tools.py` |
| `analyze_code` | Анализ кода | code, language | `server/tools/code_tools.py` |
| `format_code` | Форматирование кода | code, language | `server/tools/code_tools.py` |
| `run_tests` | Запустить тесты | test_path, framework | `server/tools/code_tools.py` |

### Web Tools (3 инструмента)

| Tool | Описание | Параметры | Код |
|------|----------|-----------|-----|
| `fetch_url` | Загрузить URL | url, method, headers | `server/tools/web_tools.py` |
| `search_web` | Веб поиск | query, num_results | `server/tools/web_tools.py` |
| `extract_content` | Извлечь контент | url, selector | `server/tools/web_tools.py` |

### Filesystem Tools (4 инструмента)

| Tool | Описание | Параметры | Код |
|------|----------|-----------|-----|
| `read_file` | Прочитать файл | path | `server/tools/filesystem_tools.py` |
| `write_file` | Записать файл | path, content | `server/tools/filesystem_tools.py` |
| `list_directory` | Список файлов | path, recursive | `server/tools/filesystem_tools.py` |
| `file_exists` | Проверить существование | path | `server/tools/filesystem_tools.py` |

### Administration (2 инструмента)

| Tool | Описание | Параметры | Код |
|------|----------|-----------|-----|
| `list_agents` | Список всех агентов | - | `server/tools/admin_tools.py` |
| `system_health` | Проверка здоровья системы | - | `server/tools/admin_tools.py` |

---

## 📡 REST API Endpoints

Помимо MCP tools, доступны REST API endpoints:

### Task API
- `POST /api/tasks` - Создать задачу
- `GET /api/tasks` - Список задач
- `GET /api/tasks/{task_id}` - Детали задачи
- `POST /api/tasks/{task_id}/cancel` - Отменить задачу

### Memory API
- `GET /api/memory/search?query=...` - Поиск в памяти
- `POST /api/chat` - RAG чат

### Agents API
- `GET /api/agents/status` - Статус всех агентов

### Metrics API
- `GET /api/metrics/quality` - Метрики качества
- `GET /api/metrics/quality?task_id=...` - Метрики для задачи

### MAGIC API
- `GET /api/magic/escalations` - Список эскалаций
- `POST /api/magic/escalations/{id}/respond` - Ответить
- `GET /api/magic/sessions` - Активные сессии
- `POST /api/magic/feedback` - Отправить фидбек
- `GET /api/magic/confidence/{task_id}` - Уверенность
- `GET /api/magic/evolution` - Метрики эволюции

### Filesystem API
- `GET /api/files/list?path=...` - Список файлов
- `GET /api/files/read?path=...` - Прочитать файл

### Health
- `GET /health` - Health check

---

## 🎯 Примеры Использования

### 1. Простая задача (Standard execution)

```python
# Через MCP tool
result = await mcp.call_tool("submit_task", {
    "description": "Исправить опечатку в README",
    "priority": 1,
    "context": {"file": "README.md"}
})

# Через REST API
curl -X POST https://mcp.agents.xteam.pro/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Исправить опечатку в README", "priority": 1}'
```

### 2. Сложная задача (Adversarial Team)

```python
result = await mcp.call_tool("submit_task", {
    "description": "Разработать систему аутентификации с JWT и OAuth2",
    "priority": 5,  # complex
    "context": {
        "requirements": ["JWT", "OAuth2", "refresh tokens", "role-based access"]
    }
})

# Система автоматически активирует 21-agent Adversarial Team
```

### 3. Исследовательская задача (Research Team)

```python
from xteam_agents.integration.research_adapter import ResearchTeamAdapter
from xteam_agents.agents.research_team.research_state import ResearchTaskType

adapter = ResearchTeamAdapter(llm_provider, memory_manager)
result = await adapter.invoke_research_team(
    research_question="Разработать датасет для адаптивного обучения математике",
    task_type=ResearchTaskType.DATASET_DESIGN,
    complexity=ResearchComplexity.COMPLEX,
    objectives=[
        "Создать структуру датасета для K-8 математики",
        "Определить метрики качества",
        "Разработать pipeline аннотации"
    ],
)
```

### 4. Задача с MAGIC (Human oversight)

```python
# Отправить задачу с MAGIC configuration
result = await mcp.call_tool("submit_task", {
    "description": "Рефакторинг критического модуля аутентификации",
    "priority": 4,  # critical
    "magic": {
        "autonomy_level": "guided",
        "confidence_threshold": 0.8,
        "checkpoints": ["after_analyze", "after_plan", "after_execute"],
        "escalation_timeout": 600
    }
})

# Система будет эскалировать на человека при низкой уверенности
# Проверить эскалации:
escalations = await mcp.call_tool("list_pending_escalations")

# Ответить на эскалацию:
await mcp.call_tool("respond_to_escalation", {
    "escalation_id": "...",
    "response_type": "approval",
    "content": "Approved, proceed with refactoring"
})
```

### 5. Мониторинг выполнения

```python
# Проверить статус
status = await mcp.call_tool("get_task_status", {"task_id": task_id})

# Получить результат
result = await mcp.call_tool("get_task_result", {"task_id": task_id})

# Просмотреть audit log
audit = await mcp.call_tool("get_task_audit_log", {"task_id": task_id})

# Статус всех агентов
agents = await mcp.call_tool("list_agents")
```

---

## 🔌 Интеграция с Claude Desktop

Добавить в `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "xteam-agents": {
      "command": "python",
      "args": ["-m", "xteam_agents"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "REDIS_URL": "redis://localhost:6379/0",
        "QDRANT_URL": "http://localhost:6333",
        "NEO4J_URL": "bolt://localhost:7687",
        "NEO4J_PASSWORD": "xteam_password",
        "POSTGRES_URL": "postgresql://postgres:xteam_password@localhost:5432/xteam",
        "MAGIC_ENABLED": "true"
      }
    }
  }
}
```

Или для удаленного сервера:

```json
{
  "mcpServers": {
    "xteam-agents-remote": {
      "command": "curl",
      "args": ["-X", "POST", "https://mcp.agents.xteam.pro/sse"],
      "transport": "sse"
    }
  }
}
```

---

## 📊 Мониторинг и Метрики

### Dashboard
- URL: `https://dashboard.agents.xteam.pro`
- Streamlit interface с real-time мониторингом
- Страницы: Live Agents, Adversarial Team, Quality Metrics, Tasks, Chat, MAGIC Control

### Проверка здоровья агентов

```bash
# Cognitive agents
curl https://mcp.agents.xteam.pro/api/agents/status

# System health
curl https://mcp.agents.xteam.pro/health
```

### Метрики качества

```bash
# Последние оценки качества
curl https://mcp.agents.xteam.pro/api/metrics/quality

# Для конкретной задачи
curl https://mcp.agents.xteam.pro/api/metrics/quality?task_id=...
```

---

## 🧠 Memory Architecture

| Backend | Technology | Содержит | Write Access | URL |
|---------|-----------|----------|--------------|-----|
| **Redis** | In-memory cache | Episodic (short-term) | Any node | redis://xteam-redis:6379 |
| **Qdrant** | Vector DB | Semantic (validated) | Commit node only | http://xteam-qdrant:6333 |
| **Neo4j** | Graph DB | Procedural (relationships) | Commit node only | bolt://xteam-neo4j:7687 |
| **PostgreSQL** | SQL | Audit log (append-only) | Any node (append) | postgresql://xteam-postgres:5432/xteam |

**Критический инвариант**: Только commit_node может писать в shared memory (Qdrant + Neo4j)

---

## 🔐 Security

- Все сервисы доступны только через HTTPS
- Let's Encrypt SSL сертификаты
- Внутренние сервисы (Redis, PostgreSQL) не имеют внешнего доступа
- JWT аутентификация (планируется)
- Audit log для всех операций

---

## 📚 Документация

- **README.md** - Общее описание
- **CLAUDE.md** - Руководство для разработчиков
- **DEPLOYMENT_STATUS.md** - Статус развертывания
- **MAGIC_IMPLEMENTATION.md** - MAGIC система
- **RESEARCH_TEAM_SUMMARY.md** - Research Team
- **TEAM_ROSTER.md** - Adversarial Team roster
- **INTEGRATION_ARCHITECTURE.md** - Архитектура интеграции

---

**Итого**:
- **40+ агентов** (5 Cognitive + 21 Adversarial + 14+ Research + Critics)
- **29 MCP tools**
- **20+ REST API endpoints**
- **4 памяти** (Redis, Qdrant, Neo4j, PostgreSQL)
- **Полностью развернуто** на `https://mcp.agents.xteam.pro`

✅ **ВСЕ СИСТЕМЫ РАБОТАЮТ**
