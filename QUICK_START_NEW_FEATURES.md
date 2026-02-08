# Быстрый старт: MAGIC и QA Automation

Этот файл поможет вам быстро начать работу с новыми системами.

## 🚀 5-минутный старт MAGIC System

### 1. Включить MAGIC

Отредактируйте `.env`:

```bash
MAGIC_ENABLED=true
MAGIC_DEFAULT_AUTONOMY=collaborative
MAGIC_DEFAULT_CONFIDENCE_THRESHOLD=0.6
MAGIC_DEFAULT_ESCALATION_TIMEOUT=300
```

### 2. Запустить систему

```bash
# Запустить все сервисы в Docker
docker-compose up -d

# В другом терминале запустить MCP server
python -m xteam_agents --http

# В третьем терминале запустить dashboard
cd dashboard
streamlit run app.py
```

### 3. Открыть MAGIC Control Dashboard

1. Откройте `http://localhost:8501` в браузере
2. Нажмите "MAGIC Control" в меню слева
3. Откроется 5-табная интерфейс

## 🎯 Попробовать MAGIC на работе

### Через Claude Desktop

1. Обновите конфиг Claude Desktop с `MAGIC_ENABLED=true`
2. Используйте инструмент `configure_magic`:

```json
{
  "task_id": "my-task-123",
  "autonomy_level": "guided",
  "confidence_threshold": 0.8,
  "checkpoints": ["after_analyze", "after_plan"]
}
```

3. Отправьте задачу через `submit_task`
4. Посмотрите эскалирования в MAGIC Control Dashboard
5. Ответьте на эскалирования через `respond_to_escalation`

### Через REST API

```bash
# Получить ожидающие эскалирования
curl http://localhost:8000/api/magic/escalations

# Ответить на эскалирование
curl -X POST http://localhost:8000/api/magic/escalations/{id}/respond \
  -H "Content-Type: application/json" \
  -d '{
    "response_type": "guidance",
    "content": "Please ensure error handling is robust",
    "human_id": "user@example.com"
  }'

# Получить scores уверенности
curl http://localhost:8000/api/magic/confidence/task-123

# Получить metrics эволюции
curl http://localhost:8000/api/magic/evolution
```

## 🧪 5-минутный старт QA Automation

### 1. Инициализировать QA проект

```bash
cd qa-automation

# Установить зависимости
npm install

# Проверить конфигурацию
cat config/qa-config.json
```

### 2. Сгенерировать User Stories

```bash
npm run qa:orchestrate -- --phase=analysis
```

Это создаст `reports/user_stories_complete.json` с автоматически сгенерированными историями.

### 3. Запустить тесты

```bash
# Все тесты
npm run test:all

# Или поэтапно:
npm run test:api      # Быстрые API тесты
npm run test:e2e      # E2E тесты (медленнее)
npm run test:visual   # Visual regression
```

### 4. Создать отчет

```bash
npm run qa:orchestrate -- --phase=reporting
npm run qa:serve-report
```

Откроется Allure отчет с результатами.

## 📊 Dashboard Integration

Обе системы интегрированы в Streamlit dashboard:

**MAGIC Control** (когда `MAGIC_ENABLED=true`):
- Pending Escalations - Список ожидающих эскалаций
- Active Sessions - Активные сессии сотрудничества
- Confidence Dashboard - Radar chart по 5 измерениям
- Feedback & Learning - Отправить обратную связь
- Evolution Metrics - Рекомендации по автономии

**QA Automation**:
- User Stories Coverage - Матрица покрытия
- Test Results - Результаты тестов
- Coverage Metrics - Статистика автоматизации

## 🔧 Конфигурация по сценариям

### Сценарий 1: Критическая архитектура (нужен человеческий обзор)

```python
request = {
    "description": "Design new payment microservice",
    "magic": {
        "autonomy_level": "guided",
        "confidence_threshold": 0.8,
        "checkpoints": ["after_analyze", "after_plan"],
        "escalation_timeout": 600
    }
}
```

**Результат**: Система будет эскалировать анализ и план для человеческого обзора.

### Сценарий 2: Стандартная задача с прогрессивным доверием

```python
request = {
    "description": "Fix login bug",
    "magic": {
        "autonomy_level": "collaborative",
        "confidence_threshold": 0.6,
        "checkpoints": []  # Нет явных чекпойнтов
    }
}
```

**Результат**: Система будет эскалировать только если уверенность < 0.6.

### Сценарий 3: Автономный режим без человека

```python
request = {
    "description": "Update package versions",
    "magic": {
        "autonomy_level": "autonomous",
        "checkpoints": []
    }
}
```

**Результат**: Система эскалирует только при сбое выполнения.

### Сценарий 4: Тесты для новой функции (QA)

```bash
cd qa-automation

# 1. Сгенерировать истории для новой функции
npm run qa:orchestrate -- --phase=analysis

# 2. Запустить critical path тесты (P0 задачи)
npm run test:critical

# 3. Запустить все тесты
npm run test:all

# 4. Проверить покрытие
npm run qa:serve-report
```

## 📈 Мониторинг прогресса

### MAGIC Evolution Metrics

```bash
# В Python
from xteam_agents.magic import MAGICCore

magic = MAGICCore(memory_manager, llm_provider)
metrics = await magic.evolution.compute_metrics()

print(f"Escalation rate: {metrics['escalation_rate']}")
print(f"Approval rate: {metrics['approval_rate']}")
print(f"Autonomy recommendations: {metrics['autonomy_recommendations']}")
```

### QA Progress Matrix

```bash
# После запуска тестов
cat qa-automation/reports/progress_matrix.json

# Или в dashboard
# QA Automation tab → Coverage Metrics
```

## 🧑‍💻 Разработка и расширение

### Добавить новый MAGIC checkpoint

```python
# В src/xteam_agents/graph/builder.py
graph.add_conditional_edge(
    "execute",
    checkpoint_after_execute,  # Новый checkpoint узел
    {
        "continue": "validate",
        "escalate": "human_checkpoint",
        "fail": "fail_handler"
    }
)
```

### Добавить новый тип теста в QA

```bash
cd qa-automation

# Создать новую директорию теста
mkdir tests/integration

# Создать Jest конфиг
cat > jest.integration.config.js << 'EOF'
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/tests/integration/**/*.spec.ts'],
  testTimeout: 30000,
  maxWorkers: 1
};
EOF

# Добавить npm script в package.json
# "test:integration": "jest --config=jest.integration.config.js"
```

## ⚡ Быстрые команды

```bash
# MAGIC тесты
pytest tests/unit/test_magic.py -v

# QA с watch режимом
cd qa-automation && npm run test:e2e -- --watch

# Оба сразу
pytest tests/unit/test_magic.py -v && \
  cd qa-automation && npm run test:all

# Отключить MAGIC на время
MAGIC_ENABLED=false python -m xteam_agents --http

# Проверить MAGIC конфиг
python -c "from xteam_agents.config import Settings; print(Settings().MAGIC_ENABLED)"
```

## 🔍 Отладка

### MAGIC не эскалирует задачи?

1. Проверьте: `MAGIC_ENABLED=true` в `.env`
2. Проверьте `confidence_threshold` - может быть слишком низкий
3. Проверьте `autonomy_level` - TRUSTED никогда не эскалирует
4. Включите DEBUG logging: `LOG_LEVEL=DEBUG`

```bash
# Проверить статус
curl http://localhost:8000/api/magic/escalations

# Проверить уверенность
curl http://localhost:8000/api/magic/confidence/task-123
```

### QA тесты не запускаются?

```bash
cd qa-automation

# Проверить установку
npm list puppeteer jest

# Проверить конфиг
npx jest --showConfig

# Запустить с verbose
npm run test:e2e -- --verbose
```

### Общие проблемы

| Проблема | Решение |
|----------|---------|
| MAGIC tools не видны в Claude | Перезагрузить Claude Desktop |
| Эскалирования не появляются | Включить MAGIC_ENABLED=true и перезагрузить |
| QA тесты timeout | Увеличить testTimeout в jest.config.js |
| Утечка памяти в E2E | Запустить с `--detectOpenHandles` флагом |

## 📚 Дальнейшее изучение

- **CLAUDE.md** - Полное руководство для разработчиков
- **MAGIC_IMPLEMENTATION.md** - Техническая документация по MAGIC
- **tests/unit/test_magic.py** - Примеры использования MAGIC
- **qa-automation/tests/** - Примеры тестов
- **dashboard/app.py** - Интеграция Dashboard

## 🎓 Обучающие примеры

```bash
# Запустить MAGIC пример
python examples/magic_example.py

# Запустить интегрированный пример
python examples/integrated_execution.py

# Запустить QA пример
cd qa-automation
npm run qa:orchestrate -- --phase=analysis
```

## ✅ Checklist для готовности к production

- [ ] MAGIC_ENABLED установлен в зависимости от потребностей
- [ ] Настроены уровни автономии по умолчанию
- [ ] Тесты MAGIC пройдены: `pytest tests/unit/test_magic.py`
- [ ] QA тесты настроены и проходят: `cd qa-automation && npm run test:all`
- [ ] Dashboard доступен и показывает метрики
- [ ] Webhook настроен для notifications (опционально)
- [ ] Команда обучена использовать MAGIC Control
- [ ] Audit log мониторится для compliance

## 💡 Pro Tips

1. **Начните с GUIDED уровнем** - меньше эскалаций, но важные решения под контролем
2. **Увеличивайте confidence_threshold постепенно** - начните с 0.7, затем 0.8
3. **Используйте checkpoints для критических задач** - after_analyze и after_plan
4. **Мониторьте evolution metrics** - они указывают на необходимость корректировки
5. **Не отключайте audit log** - нужен для analysis и compliance
6. **Запускайте QA critical tests в CI/CD** - убедитесь что P0 пути работают
7. **Используйте MAGIC feedback** - генерируемые guidelines улучшают будущие задачи
