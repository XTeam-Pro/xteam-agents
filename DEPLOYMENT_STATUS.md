# XTeam Agents - Статус Развертывания

**Дата**: 2026-02-08
**Статус**: ✅ **РАЗВЕРНУТО И РАБОТАЕТ**
**Режим**: Development с интеграцией в существующий Traefik

## 🚀 Развернутые Сервисы

| Сервис | Контейнер | Статус | Домен |
|--------|-----------|--------|-------|
| **MCP Server** | xteam-mcp-server | ✅ Healthy | `https://mcp.agents.xteam.pro` |
| **Dashboard** | xteam-dashboard | ✅ Running | `https://dashboard.agents.xteam.pro` |
| **Qdrant (Vector DB)** | xteam-qdrant | ✅ Running | `https://qdrant.agents.xteam.pro` |
| **Neo4j (Graph DB)** | xteam-neo4j | ✅ Running | `https://neo4j.agents.xteam.pro` |
| **PostgreSQL (Audit)** | xteam-postgres | ✅ Healthy | Internal only |
| **Redis (Episodic)** | xteam-redis | ✅ Healthy | Internal only |
| **n8n (Workflows)** | xteam-n8n | ✅ Running | `https://n8n.agents.xteam.pro` |

## 🔧 Конфигурация

### Сети
- **dev-studyninja-network** (external) - Подключение к общему Traefik
- **xteam-agents_xteam-network** (internal) - Внутренняя связь между сервисами

### Traefik Integration
Используется существующий Traefik контейнер `dev-traefik` из StudyNinja экосистемы:
- HTTP: порт 80 → HTTPS редирект
- HTTPS: порт 443 → SSL сертификаты Let's Encrypt
- Dashboard: порт 8082

### Environment Variables
Файл: `.env`
- `DOMAIN=agents.xteam.pro`
- `LLM_PROVIDER=openai`
- `MAGIC_ENABLED=true`
- Все database URLs настроены на Docker internal networking

## 📊 MCP Server

**Версия**: 0.1.0
**FastMCP**: 2.14.5
**Transport**: Server-Sent Events (SSE)
**Endpoint**: `http://0.0.0.0:8000` (internal), `https://mcp.agents.xteam.pro` (external)
**Health Check**: `/health` - возвращает `{"status":"ok","service":"xteam-agents","version":"0.1.0"}`

### Доступные MCP Tools (29 инструментов)

#### Task Management
- `submit_task` - Отправить новую задачу
- `get_task_status` - Проверить статус задачи
- `get_task_result` - Получить результат задачи
- `cancel_task` - Отменить выполняющуюся задачу
- `list_tasks` - Список всех задач

#### Memory & Knowledge
- `query_memory` - Поиск по всем типам памяти
- `search_knowledge` - Семантический поиск в базе знаний
- `get_knowledge_graph` - Граф знаний для задачи
- `get_task_audit_log` - История выполнения задачи

#### MAGIC System (Human-AI Collaboration)
- `configure_magic` - Настроить MAGIC для задачи
- `list_pending_escalations` - Список ожидающих эскалаций
- `respond_to_escalation` - Ответить на эскалацию
- `submit_feedback` - Отправить обратную связь
- `get_confidence_scores` - Получить оценки уверенности
- `get_magic_session` - Состояние коллаборативной сессии
- `get_evolution_metrics` - Метрики прогресса автономности

#### Administration
- `list_agents` - Список всех когнитивных агентов
- `get_audit_log` - Системный аудит лог
- `register_capability` - Регистрация новых возможностей
- `list_capabilities` - Список доступных действий
- `system_health` - Проверка здоровья системы

## 🤖 Integrated Agent Systems

### Cognitive OS (Основная система)
5 когнитивных агентов:
- **Analyst** - Анализ задач и контекста
- **Architect** - Планирование решений
- **Worker** - Выполнение действий
- **Reviewer** - Валидация результатов
- **Commit Node** - Сохранение валидированных знаний (единственный, кто пишет в shared memory)

### Adversarial Team (Для сложных задач)
21 агент для высококачественного выполнения:
- 1 Orchestrator (координатор)
- 10 Agent-Critic пар (итеративная доработка)
  - TechLead ↔ TechLeadCritic
  - Architect ↔ ArchitectCritic
  - Backend ↔ BackendCritic
  - Frontend ↔ FrontendCritic
  - Data ↔ DataCritic
  - DevOps ↔ DevOpsCritic
  - QA ↔ QACritic
  - AIArchitect ↔ AIArchitectCritic
  - Security (Blue Team) ↔ SecurityCritic (Red Team)
  - Performance ↔ PerformanceCritic

### Research Team (Научно-исследовательская группа)
14+ агентов для образовательных исследований:
- **Scientists**: Chief Scientist, Data Scientist, ML Researcher, Cognitive Scientist, Pedagogical Researcher
- **Methodologists**: Lead Methodologist, Curriculum Designer, Assessment Designer, Adaptive Learning Specialist
- **Content Team**: Content Architect, SME (Math), SME (Science), Dataset Engineer, Annotation Specialist

## 📈 Memory Architecture

| Backend | Technology | Purpose | Write Access |
|---------|-----------|---------|--------------|
| Redis | In-memory | Episodic (short-term) | Any node |
| Qdrant | Vector DB | Semantic (validated knowledge) | ✅ **Commit Node ONLY** |
| Neo4j | Graph DB | Procedural (relationships) | ✅ **Commit Node ONLY** |
| PostgreSQL | SQL | Audit log (append-only) | Any node (append) |

**Критический инвариант**: Только commit_node может писать в shared memory (Qdrant + Neo4j)

## 🔐 Security & Access

### Внутренние порты (только Docker сеть)
- MCP Server: 8000
- Dashboard: 8501
- Redis: 6379
- PostgreSQL: 5432
- Qdrant: 6333, 6334
- Neo4j: 7474, 7687
- n8n: 5678

### Внешний доступ (через Traefik HTTPS)
Все сервисы доступны только через HTTPS с автоматическими Let's Encrypt сертификатами:
- `https://mcp.agents.xteam.pro` - MCP Server API
- `https://dashboard.agents.xteam.pro` - Streamlit Dashboard
- `https://qdrant.agents.xteam.pro` - Qdrant UI
- `https://neo4j.agents.xteam.pro` - Neo4j Browser
- `https://n8n.agents.xteam.pro` - n8n Workflows (Basic Auth: admin/xteam_password)

### API Keys
- OpenAI: Настроен (dummy key для development)
- Anthropic: Настроен (dummy key для development)

**⚠️ ВАЖНО**: Для production использования необходимо обновить API ключи в `.env` файле!

## 🧪 Testing & Verification

### Health Checks
```bash
# MCP Server
curl https://mcp.agents.xteam.pro/health

# Ожидаемый ответ:
# {"status":"ok","service":"xteam-agents","version":"0.1.0"}
```

### Docker Commands
```bash
# Просмотр статуса всех контейнеров
docker compose ps

# Логи MCP сервера
docker logs xteam-mcp-server -f

# Логи Dashboard
docker logs xteam-dashboard -f

# Перезапуск MCP сервера
docker compose restart mcp-server

# Остановка всех сервисов
docker compose down

# Запуск всех сервисов
docker compose up -d
```

### Проверка подключения к базам данных
```bash
# Redis
docker exec xteam-redis redis-cli ping
# Должен вернуть: PONG

# PostgreSQL
docker exec xteam-postgres psql -U postgres -d xteam -c "SELECT 1"
# Должен вернуть: 1

# Neo4j (через cypher-shell)
docker exec xteam-neo4j cypher-shell -u neo4j -p xteam_password "RETURN 1"
# Должен вернуть: 1
```

## 📚 Documentation

- **README.md** - Общее описание системы
- **CLAUDE.md** - Руководство для разработчиков
- **MAGIC_IMPLEMENTATION.md** - Документация MAGIC системы
- **RESEARCH_TEAM_SUMMARY.md** - Описание Research Team
- **INTEGRATION_ARCHITECTURE.md** - Архитектура интеграции
- **TEAM_ROSTER.md** - Список всех 21 агентов Adversarial Team

## 🔄 Next Steps

### Для Production
1. **Обновить API ключи** в `.env`:
   - Заменить `OPENAI_API_KEY` на реальный ключ
   - Заменить `ANTHROPIC_API_KEY` на реальный ключ (если используется Anthropic)

2. **Настроить DNS**:
   - `mcp.agents.xteam.pro` → IP сервера
   - `dashboard.agents.xteam.pro` → IP сервера
   - `qdrant.agents.xteam.pro` → IP сервера
   - `neo4j.agents.xteam.pro` → IP сервера
   - `n8n.agents.xteam.pro` → IP сервера

3. **Настроить SSL сертификаты**:
   - Let's Encrypt автоматически выпустит сертификаты при первом обращении
   - Email для уведомлений: `admin@xteam.pro` (настроен в `.env`)

4. **Мониторинг**:
   - Настроить оповещения для health checks
   - Настроить логирование в внешнюю систему
   - Настроить метрики (Prometheus/Grafana)

### Для Development
1. **Тестирование MCP интеграции**:
   ```bash
   # Запустить примеры
   docker exec xteam-mcp-server python examples/integrated_execution.py
   ```

2. **Настройка Claude Desktop**:
   - Добавить конфигурацию в `~/Library/Application Support/Claude/claude_desktop_config.json`
   - См. README.md секцию "Using with Claude Desktop"

3. **Разработка новых агентов**:
   - См. CLAUDE.md секцию "Adding a New Agent Node"
   - Все агенты находятся в `src/xteam_agents/agents/`

## 🐛 Troubleshooting

### MCP Server не запускается
```bash
# Проверить логи
docker logs xteam-mcp-server

# Проверить зависимости
docker exec xteam-mcp-server pip list | grep -E "fastmcp|langchain|openai"
```

### Базы данных недоступны
```bash
# Проверить health checks
docker compose ps

# Проверить сетевое подключение
docker exec xteam-mcp-server ping redis
docker exec xteam-mcp-server ping postgres
docker exec xteam-mcp-server ping neo4j
docker exec xteam-mcp-server ping qdrant
```

### Traefik не маршрутизирует запросы
```bash
# Проверить, что контейнеры подключены к правильной сети
docker inspect xteam-mcp-server --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}'
# Должен показать: dev-studyninja-network и xteam-agents_xteam-network

# Проверить labels Traefik
docker inspect xteam-mcp-server --format='{{json .Config.Labels}}' | jq
```

## 📞 Support

Для вопросов и поддержки:
- GitHub Issues: https://github.com/xteam/xteam-agents/issues
- Documentation: См. файлы в корне проекта

---

**Статус**: ✅ Система полностью развернута и готова к использованию в development режиме
