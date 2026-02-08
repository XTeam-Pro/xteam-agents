# 📚 Documentation Index

Полный указатель всей документации проекта с описанием содержимого.

## 🚀 Быстрый Старт (Начните отсюда)

| Для кого | Документ | Время | Что изучить |
|----------|----------|-------|-------------|
| Новичок | [README.md](./README.md) | 10 мин | Обзор проекта и что это |
| Разработчик | [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) | 15 мин | Как запустить MAGIC и QA |
| Архитектор | [CLAUDE.md](./CLAUDE.md) | 1 час | Полное руководство |
| Тестировщик | [qa-automation/](./qa-automation/) | 30 мин | QA Automation setup |
| DevOps | [DEPLOYMENT.md](./DEPLOYMENT.md) | 45 мин | Production deployment |

## 📖 Основные документы

### 1. [CLAUDE.md](./CLAUDE.md) ⭐ ГЛАВНЫЙ ДОКУМЕНТ
**Аудитория**: Разработчики и архитекторы
**Содержание**:
- Development commands (setup, testing, linting)
- Complete architecture overview
- MAGIC System full documentation
- QA Automation System documentation
- LangGraph state flow
- MCP Server implementation
- Configuration guide
- Key implementation patterns
- Common development workflows
- Testing strategy
- Security considerations

**Разделы**:
- What's New - Краткое описание новостей
- Architecture Overview - Полная архитектура
- MAGIC System - Детальное описание
- QA Automation System - Детальное описание
- Configuration - Все переменные окружения
- Important Files - Основные файлы
- Common Workflows - Типичные работы
- Testing Strategy - Стратегия тестирования
- Dashboard Features - Функции dashboard
- Security Considerations - Безопасность

### 2. [README.md](./README.md) ⭐ ПУБЛИЧНОЕ ОПИСАНИЕ
**Аудитория**: Все (начиная с новичков)
**Содержание**:
- Project overview и status
- Architecture diagram
- Agents description
- Integrated execution modes
- MAGIC System summary
- QA Automation System summary
- Memory backends
- Key invariants
- Quick start guide
- MCP Tools reference
- Configuration summary
- Development quick commands
- Production deployment

**Ключевые секции**:
- What's New
- Quick Start (Installation and Usage)
- MCP Tools (with MAGIC tools)
- Configuration (including MAGIC vars)
- Development
- Production Deployment

### 3. [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) ⭐ ПРАКТИЧЕСКИЙ GUIDE
**Аудитория**: Разработчики (сразу начать)
**Содержание**:
- 5-minute MAGIC System start
- 5-minute QA Automation start
- How to try MAGIC in action (Claude Desktop, REST API)
- Dashboard integration for both systems
- Configuration by scenarios (4 examples)
- Progress monitoring
- Development and extension
- Quick commands for developers
- Debugging and troubleshooting
- Further learning resources
- Educational examples
- Production readiness checklist
- Pro tips

**Практические примеры**:
- Критическая архитектура (GUIDED уровень)
- Стандартная задача (COLLABORATIVE)
- Автономный режим (AUTONOMOUS)
- QA тесты для новой функции

### 4. [UPDATES.md](./UPDATES.md) ⭐ DETAILED CHANGELOG
**Аудитория**: Разработчики и архитекторы
**Содержание**:
- Overview обновлений
- MAGIC System detailed description
- QA Automation detailed description
- When to use each system
- File summary (11 new, 8 modified)
- Architecture changes
- Documentation updates
- Backward compatibility
- Next steps for development
- Important files reference

**Что охватывает**:
- Полное описание обеих систем
- When to use scenarios
- File organization
- Integration points
- Production readiness

### 5. [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) ⭐ TECHNICAL DOCUMENTATION
**Аудитория**: Архитекторы и senior разработчики
**Содержание**:
- Complete MAGIC system implementation
- Data models and configuration
- Core MAGIC engine (6 subsystems)
- Graph integration points
- Orchestrator integration
- MCP tools and REST API
- Dashboard integration
- Testing coverage
- Architecture and design decisions
- Memory invariant preservation
- Autonomy levels (5 levels)
- Escalation strategy (decision matrix)
- Checkpoint strategy
- Human response processing (7 types)
- Progressive autonomy (evolution metrics)
- Configuration options
- Usage examples
- Backward compatibility
- Integration example
- Key features summary
- Production next steps

## 📋 Project Organization

### Core Cognitive OS
- [SSOT.md](./SSOT.md) - Single Source of Truth (архитектурный документ)
- [INTEGRATION_ARCHITECTURE.md](./INTEGRATION_ARCHITECTURE.md) - Adversarial Team
- [INTEGRATION_USAGE.md](./INTEGRATION_USAGE.md) - How to use Adversarial Team
- [TEAM_ROSTER.md](./TEAM_ROSTER.md) - All 21 agents

### Deployment & Infrastructure
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment with Traefik
- [TRAEFIK.md](./TRAEFIK.md) - Traefik reverse proxy configuration
- [docker-compose.yml](./docker-compose.yml) - Docker services
- [.env.example](./.env.example) - Environment variables template

### Development
- [CLAUDE.md](./CLAUDE.md) - Development guide (THIS IS THE MAIN DEV DOCUMENT)
- [src/](./src/) - Source code
- [tests/](./tests/) - Test suite
- [examples/](./examples/) - Example scripts
- [scripts/](./scripts/) - Utility scripts

### QA & Testing
- [qa-automation/](./qa-automation/) - QA automation project
- [qa-automation/src/agents/](./qa-automation/src/agents/) - QA agents
- [qa-automation/tests/](./qa-automation/tests/) - Test suites
- [qa-automation/config/](./qa-automation/config/) - QA configuration
- [qa-automation/reports/](./qa-automation/reports/) - Test results
- [.trae/documents/QA-Quick-Start-Example.md](./.trae/documents/QA-Quick-Start-Example.md) - QA practical guide

### Dashboard
- [dashboard/](./dashboard/) - Streamlit dashboard
- [dashboard/app.py](./dashboard/app.py) - Main dashboard app
- [dashboard/README.md](./dashboard/README.md) - Dashboard documentation

### Documentation Index
- [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) - **ВЫ ЗДЕСЬ** (This file)
- [DOCUMENTATION_UPDATE_SUMMARY.md](./DOCUMENTATION_UPDATE_SUMMARY.md) - Summary of updates
- [UPDATES.md](./UPDATES.md) - What changed in version 2.0

## 🎓 Learning Paths

### Path 1: I'm New to the Project
1. Read [README.md](./README.md) (10 min)
2. Read [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) (15 min)
3. Try 5-minute setup for MAGIC or QA (15 min)
4. Look at dashboard examples (10 min)
5. Read [CLAUDE.md](./CLAUDE.md) for details (1+ hours)

### Path 2: I'm a Developer
1. Read [CLAUDE.md](./CLAUDE.md) architecture section (20 min)
2. Read [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) (15 min)
3. Run tests: `pytest tests/unit/test_magic.py -v` (5 min)
4. Try the examples in [CLAUDE.md](./CLAUDE.md) (30+ min)
5. Read full [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) (30 min)
6. Explore [src/xteam_agents/](./src/xteam_agents/) code

### Path 3: I Need QA Setup
1. Read [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) QA section (10 min)
2. Read [.trae/documents/QA-Quick-Start-Example.md](./.trae/documents/QA-Quick-Start-Example.md) (30 min)
3. Run: `cd qa-automation && npm install && npm run qa:orchestrate -- --phase=analysis`
4. Look at generated user stories
5. Run tests: `npm run test:all`
6. View reports: `npm run qa:serve-report`

### Path 4: I'm Doing Production Deployment
1. Read [DEPLOYMENT.md](./DEPLOYMENT.md) (30 min)
2. Read [TRAEFIK.md](./TRAEFIK.md) (20 min)
3. Read [CLAUDE.md](./CLAUDE.md) Configuration section (10 min)
4. Configure MAGIC settings: [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) (15 min)
5. Run setup script: `sudo ./scripts/setup-traefik.sh`
6. Monitor dashboard for health

### Path 5: I Want to Understand Architecture
1. Read [README.md](./README.md) Architecture section (15 min)
2. Read [CLAUDE.md](./CLAUDE.md) Architecture Overview (30 min)
3. Read [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) Design Decisions (20 min)
4. Read [SSOT.md](./SSOT.md) (30 min)
5. Read [INTEGRATION_ARCHITECTURE.md](./INTEGRATION_ARCHITECTURE.md) (30 min)
6. Review code in [src/xteam_agents/](./src/xteam_agents/)

## 🔍 Find Information By Topic

### MAGIC System
- **What is it?** → [README.md](./README.md) section "MAGIC System"
- **How to use?** → [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) "5-minute start"
- **Full details?** → [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md)
- **Configuration?** → [CLAUDE.md](./CLAUDE.md) "Configuration" section
- **How to test?** → [CLAUDE.md](./CLAUDE.md) "Testing MAGIC System"
- **Examples?** → [tests/unit/test_magic.py](./tests/unit/test_magic.py)

### QA Automation
- **What is it?** → [README.md](./README.md) section "QA Automation"
- **How to use?** → [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) "5-minute start"
- **Detailed guide?** → [.trae/documents/QA-Quick-Start-Example.md](./.trae/documents/QA-Quick-Start-Example.md)
- **Test types?** → [UPDATES.md](./UPDATES.md) section "Test Types"
- **Commands?** → [CLAUDE.md](./CLAUDE.md) "Running QA Automation"
- **Dashboard?** → [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) "Dashboard Integration"

### Cognitive OS
- **Overview?** → [README.md](./README.md) "Architecture"
- **Details?** → [CLAUDE.md](./CLAUDE.md) "Cognitive Graph Flow"
- **Complete spec?** → [SSOT.md](./SSOT.md)
- **Memory system?** → [CLAUDE.md](./CLAUDE.md) "Memory Backend Architecture"
- **How agents work?** → [CLAUDE.md](./CLAUDE.md) "The Five Cognitive Agents"

### Adversarial Team
- **What is it?** → [README.md](./README.md) "Integrated Execution"
- **Full architecture?** → [INTEGRATION_ARCHITECTURE.md](./INTEGRATION_ARCHITECTURE.md)
- **How to use?** → [INTEGRATION_USAGE.md](./INTEGRATION_USAGE.md)
- **All 21 agents?** → [TEAM_ROSTER.md](./TEAM_ROSTER.md)
- **Code example?** → [examples/integrated_execution.py](./examples/integrated_execution.py)

### Configuration
- **All env vars?** → [CLAUDE.md](./CLAUDE.md) "Configuration" section
- **MAGIC settings?** → [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) "Configuration"
- **Template?** → [.env.example](./.env.example)
- **Production setup?** → [DEPLOYMENT.md](./DEPLOYMENT.md)

### MCP Tools
- **Task tools?** → [CLAUDE.md](./CLAUDE.md) MCP section
- **Memory tools?** → [CLAUDE.md](./CLAUDE.md) MCP section
- **MAGIC tools?** → [README.md](./README.md) "MAGIC Tools" section
- **Admin tools?** → [CLAUDE.md](./CLAUDE.md) MCP section
- **REST API?** → [CLAUDE.md](./CLAUDE.md) "REST API Endpoints"

### Testing
- **Unit tests?** → [CLAUDE.md](./CLAUDE.md) "Testing Strategy"
- **Integration tests?** → [tests/integration/](./tests/integration/)
- **E2E tests?** → [qa-automation/tests/e2e/](./qa-automation/tests/e2e/)
- **MAGIC tests?** → [tests/unit/test_magic.py](./tests/unit/test_magic.py)
- **How to run?** → [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) "Quick Commands"

### Dashboard
- **Features?** → [CLAUDE.md](./CLAUDE.md) "Dashboard Features"
- **MAGIC pages?** → [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) "Dashboard Integration"
- **QA pages?** → [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) "Dashboard Integration"
- **How to run?** → [dashboard/README.md](./dashboard/README.md)

### Deployment
- **Production?** → [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Traefik?** → [TRAEFIK.md](./TRAEFIK.md)
- **Docker?** → [docker-compose.yml](./docker-compose.yml)
- **SSL certs?** → [DEPLOYMENT.md](./DEPLOYMENT.md)
- **MAGIC in prod?** → [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) "Next Steps"

## 📞 Getting Help

### If you need...
- **Quick answer** → Check [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md)
- **Detailed documentation** → Go to [CLAUDE.md](./CLAUDE.md)
- **Technical spec** → Read [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md)
- **Code examples** → Check [tests/](./tests/) and [qa-automation/](./qa-automation/)
- **Production help** → See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Troubleshooting** → [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md) "Debugging"

### Documentation Structure
```
📚 Documentation
├── 🚀 Quick Start
│   ├── README.md (Project overview)
│   ├── QUICK_START_NEW_FEATURES.md (Practical guide)
│   └── UPDATES.md (What changed)
├── 📖 Main Documentation
│   └── CLAUDE.md (Everything for developers)
├── 🔧 Technical Docs
│   ├── MAGIC_IMPLEMENTATION.md (MAGIC details)
│   ├── SSOT.md (Architecture spec)
│   ├── INTEGRATION_ARCHITECTURE.md (Adversarial Team)
│   └── INTEGRATION_USAGE.md (Adversarial Team usage)
├── 🚀 Deployment
│   ├── DEPLOYMENT.md (Production setup)
│   └── TRAEFIK.md (Reverse proxy)
├── 🧪 QA
│   └── qa-automation/QA-Quick-Start-Example.md
├── 📊 This File
│   ├── DOCUMENTATION_INDEX.md (You are here)
│   └── DOCUMENTATION_UPDATE_SUMMARY.md (What was updated)
└── 💾 Code
    ├── src/ (Source code)
    ├── tests/ (Tests)
    └── examples/ (Examples)
```

## ✅ Documentation Checklist

- [x] Main guide (CLAUDE.md) - Complete
- [x] Quick start (QUICK_START_NEW_FEATURES.md) - Complete
- [x] MAGIC documentation (MAGIC_IMPLEMENTATION.md) - Complete
- [x] QA documentation (qa-automation/) - Complete
- [x] Configuration guide - Complete
- [x] Deployment guide (DEPLOYMENT.md) - Complete
- [x] Architecture documentation (SSOT.md) - Complete
- [x] MCP tools documentation - Complete
- [x] Dashboard documentation - Complete
- [x] Testing guide - Complete
- [x] Index file (this file) - Complete

## 🎯 Next Steps

1. **If new to project**: Start with [README.md](./README.md)
2. **If developer**: Go to [CLAUDE.md](./CLAUDE.md)
3. **If want to test**: Try [QUICK_START_NEW_FEATURES.md](./QUICK_START_NEW_FEATURES.md)
4. **If need production**: Read [DEPLOYMENT.md](./DEPLOYMENT.md)
5. **If need details**: Check specific document above

---

**Last Updated**: 2026-02-08
**Documentation Version**: 2.0 (with MAGIC System and QA Automation)
