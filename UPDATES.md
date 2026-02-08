# Latest Updates - Version 2.0

## Overview

Два крупных системных обновления интегрированы в проект:

1. **MAGIC System** - Система управления человеко-ИИ взаимодействием
2. **QA Automation** - Многоагентная система автоматизированного тестирования

Обе системы полностью интегрированы с существующей архитектурой Cognitive OS и Adversarial Agent Team.

## 1. MAGIC System (Metacognitive Awareness, Adaptive Learning, Generative Collaboration, Intelligent Escalation, Continuous Evolution)

### Что это?

Опциональный слой для управления взаимодействием человека и ИИ на каждом этапе когнитивного конвейера:

```
analyze → [checkpoint] → plan → [checkpoint] → execute → [checkpoint] → validate → [checkpoint] → commit
```

### Ключевые особенности

- **5 уровней автономии**: SUPERVISED → GUIDED → COLLABORATIVE → AUTONOMOUS → TRUSTED
- **Интеллектуальное эскалирование**: Маршрутизация человеку на основе уровня уверенности и автономии
- **Оценка уверенности**: Многомерная оценка (5 измерений)
- **Человеческие чекпойнты**: 4 опциональных этапа (after_analyze, after_plan, after_execute, after_validate)
- **Обучение от обратной связи**: Преобразование обратной связи в постоянные руководства
- **Прогрессивная автономия**: Отслеживание метрик и рекомендации по корректировке
- **100% обратно совместимо**: Нулевые накладные расходы при отключении

### Когда использовать?

- Критические задачи, требующие одобрения человека
- Задачи с специфичными для домена ограничениями
- Непрерывное обучение от обратной связи человека
- Требования по соответствию и аудиту
- Сложные архитектурные решения, требующие экспертизы

### Быстрый старт

```bash
# Включить MAGIC в .env
MAGIC_ENABLED=true
MAGIC_DEFAULT_AUTONOMY=collaborative
MAGIC_DEFAULT_CONFIDENCE_THRESHOLD=0.6

# Запустить систему
python -m xteam_agents --http

# В другом терминале откройте Streamlit dashboard:
cd dashboard
streamlit run app.py
```

В dashboard найдите новую страницу "MAGIC Control" для управления эскалирован и отслеживания прогресса.

### Файлы для изучения

**Новые файлы:**
- `src/xteam_agents/magic/core.py` - Центральный координатор
- `src/xteam_agents/magic/metacognition.py` - Оценка уверенности
- `src/xteam_agents/magic/escalation.py` - Логика эскалирования
- `src/xteam_agents/magic/session.py` - Управление сессиями
- `src/xteam_agents/magic/feedback.py` - Сбор обратной связи
- `src/xteam_agents/magic/evolution.py` - Прогрессивная автономия
- `src/xteam_agents/graph/nodes/human_checkpoint.py` - Узлы чекпойнтов
- `src/xteam_agents/models/magic.py` - Все модели Pydantic
- `src/xteam_agents/server/tools/magic_tools.py` - 7 инструментов MCP
- `tests/unit/test_magic.py` - Полный набор тестов

**Модифицированные файлы:**
- `src/xteam_agents/config.py` - 7 новых MAGIC переменных конфигурации
- `src/xteam_agents/models/state.py` - 7 опциональных полей MAGIC в AgentState
- `src/xteam_agents/models/audit.py` - 8 новых типов событий MAGIC
- `src/xteam_agents/graph/builder.py` - Условные края чекпойнтов
- `src/xteam_agents/graph/nodes/commit.py` - Привязка руководств
- `src/xteam_agents/orchestrator.py` - Инициализация MAGICCore
- `src/xteam_agents/server/app.py` - Регистрация инструментов и REST API
- `dashboard/app.py` - Новая страница "MAGIC Control"

### Документация

Полная документация: [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md)
Руководство для разработчиков: [CLAUDE.md](./CLAUDE.md#magic-system-human-ai-collaboration)

### Тестирование

```bash
# Тесты MAGIC (включают проверки обратной совместимости)
pytest tests/unit/test_magic.py -v

# С включенным MAGIC
MAGIC_ENABLED=true pytest tests/unit/test_magic.py -v
```

## 2. QA Automation System

### Что это?

Многоагентная система оркестрации автоматизированного тестирования:

```
analysis → test_creation → execution → reporting
```

### Ключевые особенности

- **Генерация User Stories**: Автоматическая генерация пользовательских историй из понимания системы
- **6 типов тестов**: E2E, API, Visual Regression, Performance, Security, Accessibility
- **Агенты создания тестов**: Автоматическая генерация кода тестов
- **Оркестрация**: Фазы: Analysis → Test Creation → Execution → Reporting
- **Отслеживание прогресса**: Матрица покрытия и статус автоматизации по функциям
- **Готовность к CI/CD**: Интеграция GitHub Actions включена
- **Интеграция Dashboard**: Метрики QA в реальном времени и отчеты

### Быстрый старт

```bash
# Перейти в директорию QA
cd qa-automation

# Установить зависимости
npm install

# Сгенерировать пользовательские истории (анализ)
npm run qa:orchestrate -- --phase=analysis

# Запустить все тесты
npm run test:all

# Создать отчет
npm run qa:orchestrate -- --phase=reporting

# Просмотреть результаты
npm run qa:serve-report
```

### Структура проекта

```
qa-automation/
├── src/agents/
│   ├── orchestrator.ts              # Оркестратор QA
│   └── user-story-analyst.ts        # Анализ пользовательских историй
├── tests/
│   ├── e2e/                         # E2E тесты (Puppeteer)
│   ├── api/                         # API тесты (Jest)
│   ├── visual/                      # Visual regression (PixelMatch)
│   ├── performance/                 # Performance tests (Lighthouse)
│   ├── security/                    # Security tests (OWASP)
│   └── a11y/                        # Accessibility tests (Axe)
├── config/
│   └── qa-config.json               # Конфигурация QA
└── reports/
    ├── progress_matrix.json         # Матрица прогресса
    └── allure-results/              # Результаты Allure
```

### Типы тестов

| Тип | Инструмент | Назначение | Скорость |
|-----|-----------|-----------|----------|
| E2E | Puppeteer/Playwright | Полные пользовательские сценарии | Медленные |
| API | Jest/Axios | Валидация REST endpoints | Быстрые |
| Visual | PixelMatch | Сравнение скриншотов | Средние |
| Performance | Lighthouse | Время загрузки и метрики | Средние |
| Security | OWASP | Сканирование уязвимостей | Быстрые |
| A11y | Axe | Соответствие доступности | Быстрые |

### Dashboard интеграция

Новая страница "QA Automation" в Streamlit dashboard показывает:
- Матрица прогресса покрытия
- Результаты тестов в реальном времени
- Метрики автоматизации
- Статус пользовательских историй

### Команды npm

```bash
# Анализ и генерация историй
npm run qa:orchestrate -- --phase=analysis

# Создание тестов
npm run qa:orchestrate -- --phase=test_creation

# Запуск тестов
npm run test:all           # Все тесты
npm run test:e2e           # Только E2E
npm run test:api           # Только API
npm run test:visual        # Только visual regression
npm run test:critical      # Только critical paths (P0)

# Отчеты
npm run qa:orchestrate -- --phase=reporting
npm run qa:report          # Allure отчет
npm run qa:serve-report    # Просмотр в браузере
```

### Документация

Руководство для разработчиков: [CLAUDE.md](./CLAUDE.md#qa-automation-system)
Быстрый старт: [.trae/documents/QA-Quick-Start-Example.md](./.trae/documents/QA-Quick-Start-Example.md)

## Архитектурные изменения

### Когнитивный граф с MAGIC

Граф теперь поддерживает опциональные чекпойнты человека:

```
START → analyze → [MAGIC checkpoint?] → plan → [MAGIC checkpoint?] →
execute → [MAGIC checkpoint?] → validate → [MAGIC checkpoint?] → commit → END
```

Каждый чекпойнт может:
- Запросить утверждение человека
- Сортировать по уровню уверенности
- Собирать обратную связь для обучения
- Прогрессировать автономию

### Инвариант памяти MAGIC

MAGIC система полностью уважает критический инвариант:
- **Только commit_node может писать в общую память** (Qdrant + Neo4j)
- Система обратной связи ставит в очередь артефакты с `is_validated=True`
- Нет отдельного пути записи для MAGIC
- Все направления и решения остаются в приватной памяти до утверждения

### Интеграция с Adversarial Team

Adversarial Team по-прежнему активируется для сложных/критических задач:
- MAGIC система работает рядом (не внутри) Adversarial Team
- Может эскалировать результаты Adversarial Team человеку
- Собирает обратную связь на выход Adversarial Team
- Хранит усвоенные рекомендации в общей памяти

## Обновления документации

Все документация была актуализирована:

- **[CLAUDE.md](./CLAUDE.md)** - Полное руководство для разработчиков с MAGIC и QA Automation
- **[README.md](./README.md)** - Обновлено описание нового функционала
- **[MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md)** - Полная техническая документация по MAGIC
- Добавлены новые документы QA Automation в `.trae/documents/`

## Обратная совместимость

✅ **100% обратная совместимо**

- Все поля MAGIC в AgentState по умолчанию None/пусто
- MAGIC компоненты опциональны везде
- Граф использует прямые ребра, когда `magic_core=None`
- Узлы чекпойнтов возвращают пустой dict, когда MAGIC отключен
- Оценка уверенности пропускается, когда MAGIC отключен
- Нет изменений в существующих API
- Все существующие тесты должны пройти

## Следующие шаги

### Для быстрого старта

1. Обновить `.env`:
```bash
MAGIC_ENABLED=true
MAGIC_DEFAULT_AUTONOMY=collaborative
```

2. Запустить систему:
```bash
docker-compose up -d
python -m xteam_agents --http
cd dashboard && streamlit run app.py
```

3. Использовать MAGIC tools в Claude Desktop или через REST API

### Для QA Automation

1. Перейти в `qa-automation/`
2. Запустить `npm install`
3. Запустить `npm run qa:orchestrate -- --phase=analysis`
4. Просмотреть результаты в dashboard

### Для производства

- Включить MAGIC в production: `MAGIC_ENABLED=true`
- Настроить уровни автономии по умолчанию для вашего домена
- Обучить команду использовать MAGIC Control dashboard
- Начать с COLLABORATIVE уровня, постепенно доверие возрастает
- Мониторить evolution metrics для оптимизации thresholds

## Важные файлы

| Файл | Описание |
|------|---------|
| [CLAUDE.md](./CLAUDE.md) | Полное руководство для разработчиков |
| [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) | MAGIC техническая документация |
| [README.md](./README.md) | Обновленный README с новой функциональностью |
| [src/xteam_agents/magic/](./src/xteam_agents/magic/) | Модули MAGIC системы |
| [qa-automation/](./qa-automation/) | QA Automation проект |
| [tests/unit/test_magic.py](./tests/unit/test_magic.py) | MAGIC тесты |

## Поддержка

Для вопросов и помощи:
- Читайте [CLAUDE.md](./CLAUDE.md) для подробного руководства
- Проверьте [MAGIC_IMPLEMENTATION.md](./MAGIC_IMPLEMENTATION.md) для технических деталей
- Смотрите примеры в `examples/` и тесты в `tests/`
