# QA Automation Agent - Comprehensive Testing Framework

## Обзор

Этот документ содержит инструкции для SOLO Builder по созданию comprehensive QA тестирования с использованием Puppeteer. Система включает команду QA агентов с различными ролями, автоматическую генерацию пользовательских историй, и матрицу отслеживания прогресса.

## Архитектура QA Команды

### Роли QA Агентов

```yaml
qa_team:
  orchestrator:
    name: "QA Orchestrator"
    responsibility: "Координация всей команды QA, распределение задач, сбор результатов"
    tools: ["task_delegation", "report_aggregation", "priority_management"]

  roles:
    - role: "Test Architect"
      persona: "Стратег тестирования"
      responsibilities:
        - Анализ требований и функциональности
        - Создание Test Strategy Document
        - Определение scope тестирования
        - Классификация типов тестов (unit, integration, e2e, performance)
      output:
        - test_strategy.json
        - user_stories_matrix.json
        - test_coverage_plan.json

    - role: "User Story Analyst"
      persona: "Аналитик пользовательских историй"
      responsibilities:
        - Генерация всех возможных user stories
        - Создание user journey maps
        - Определение edge cases и corner cases
        - Приоритизация сценариев (P0, P1, P2, P3)
      output:
        - user_stories_complete.json
        - journey_maps.json
        - edge_cases_catalog.json

    - role: "E2E Test Engineer"
      persona: "Инженер end-to-end тестирования"
      responsibilities:
        - Написание Puppeteer тестов для критических путей
        - Создание page object models
        - Реализация test fixtures и helpers
        - Настройка test runners (Jest/Mocha)
      tools: ["puppeteer", "jest", "axios"]
      output:
        - e2e_tests/
        - page_objects/
        - test_helpers/

    - role: "API Test Engineer"
      persona: "Инженер API тестирования"
      responsibilities:
        - Тестирование REST/GraphQL endpoints
        - Валидация request/response schemas
        - Проверка authentication и authorization
        - Performance testing API endpoints
      tools: ["axios", "jest", "json-schema-validator"]
      output:
        - api_tests/
        - api_schemas/
        - api_performance_results.json

    - role: "Visual Regression Tester"
      persona: "Тестер визуальных регрессий"
      responsibilities:
        - Screenshot comparison тесты
        - CSS regression detection
        - Responsive design testing
        - Cross-browser compatibility
      tools: ["puppeteer", "pixelmatch", "jest-image-snapshot"]
      output:
        - visual_tests/
        - screenshots_baseline/
        - visual_regression_reports/

    - role: "Performance Tester"
      persona: "Тестер производительности"
      responsibilities:
        - Load testing с Puppeteer
        - Lighthouse audits
        - Memory leak detection
        - Bundle size analysis
      tools: ["puppeteer", "lighthouse", "clinic.js"]
      output:
        - performance_reports/
        - lighthouse_scores.json
        - memory_profiles/

    - role: "Security Tester"
      persona: "Тестер безопасности"
      responsibilities:
        - OWASP Top 10 vulnerability scanning
        - XSS/CSRF/SQL injection tests
        - Authentication bypass attempts
        - Sensitive data exposure checks
      tools: ["puppeteer", "zap-proxy", "snyk"]
      output:
        - security_reports/
        - vulnerability_scan_results.json

    - role: "Accessibility Tester"
      persona: "Тестер доступности"
      responsibilities:
        - WCAG 2.1 compliance checks
        - Screen reader compatibility
        - Keyboard navigation testing
        - Color contrast validation
      tools: ["puppeteer", "axe-core", "pa11y"]
      output:
        - accessibility_reports/
        - wcag_compliance_matrix.json

    - role: "Test Reporter"
      persona: "Репортер результатов"
      responsibilities:
        - Генерация comprehensive test reports
        - Создание дашбордов с метриками
        - Интеграция с CI/CD
        - Отслеживание test flakiness
      tools: ["jest-html-reporter", "allure", "custom-dashboard"]
      output:
        - test_reports/
        - test_metrics_dashboard.html
        - flaky_tests_report.json
```

## Конфигурация QA Агента

### 1. Файл конфигурации команды

```json
{
  "qa_config": {
    "version": "1.0.0",
    "project": "xteam-agents-dashboard",
    "environment": {
      "baseURL": "http://localhost:8501",
      "apiURL": "http://localhost:8000",
      "testTimeout": 30000,
      "retries": 2
    },
    "puppeteer": {
      "headless": false,
      "slowMo": 50,
      "viewport": {
        "width": 1920,
        "height": 1080
      },
      "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security"
      ]
    },
    "team": {
      "enabled_roles": [
        "test_architect",
        "user_story_analyst",
        "e2e_test_engineer",
        "api_test_engineer",
        "visual_regression_tester",
        "performance_tester",
        "security_tester",
        "accessibility_tester",
        "test_reporter"
      ],
      "execution_order": [
        "test_architect",
        "user_story_analyst",
        "e2e_test_engineer",
        "api_test_engineer",
        "visual_regression_tester",
        "performance_tester",
        "security_tester",
        "accessibility_tester",
        "test_reporter"
      ]
    },
    "coverage_targets": {
      "user_stories_coverage": 95,
      "code_coverage": 80,
      "api_coverage": 100,
      "critical_path_coverage": 100
    },
    "reporting": {
      "formats": ["json", "html", "junit"],
      "dashboard_enabled": true,
      "slack_notifications": true,
      "email_notifications": false
    }
  }
}
```

### 2. Структура проекта

```
qa-automation/
├── config/
│   ├── qa-config.json
│   ├── environments.json
│   └── test-data.json
├── src/
│   ├── agents/
│   │   ├── orchestrator.ts
│   │   ├── test-architect.ts
│   │   ├── user-story-analyst.ts
│   │   ├── e2e-test-engineer.ts
│   │   ├── api-test-engineer.ts
│   │   ├── visual-regression-tester.ts
│   │   ├── performance-tester.ts
│   │   ├── security-tester.ts
│   │   ├── accessibility-tester.ts
│   │   └── test-reporter.ts
│   ├── page-objects/
│   │   ├── base-page.ts
│   │   ├── overview-page.ts
│   │   ├── live-agents-page.ts
│   │   ├── adversarial-team-page.ts
│   │   ├── quality-metrics-page.ts
│   │   └── ...
│   ├── test-data/
│   │   ├── user-stories.json
│   │   ├── test-scenarios.json
│   │   └── mock-data.json
│   ├── helpers/
│   │   ├── puppeteer-helper.ts
│   │   ├── api-helper.ts
│   │   ├── database-helper.ts
│   │   └── screenshot-helper.ts
│   └── utils/
│       ├── logger.ts
│       ├── retry.ts
│       └── data-generator.ts
├── tests/
│   ├── e2e/
│   │   ├── critical-paths/
│   │   ├── user-flows/
│   │   └── regression/
│   ├── api/
│   │   ├── tasks/
│   │   ├── memory/
│   │   └── agents/
│   ├── visual/
│   ├── performance/
│   ├── security/
│   └── accessibility/
├── reports/
│   ├── test-results/
│   ├── coverage/
│   ├── screenshots/
│   └── videos/
└── package.json
```

## Генерация User Stories и Journey Maps

### User Story Analyst Agent - Алгоритм

```typescript
interface UserStory {
  id: string;
  title: string;
  description: string;
  persona: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  acceptance_criteria: string[];
  preconditions: string[];
  steps: TestStep[];
  expected_results: string[];
  edge_cases: EdgeCase[];
  dependencies: string[];
  estimated_time: number; // minutes
  automation_status: 'automated' | 'manual' | 'not_started';
}

interface EdgeCase {
  scenario: string;
  trigger: string;
  expected_behavior: string;
  severity: 'critical' | 'major' | 'minor';
}

interface TestStep {
  step_number: number;
  action: string;
  selector?: string;
  input?: string;
  expected_state: string;
}

// Пример генерации User Stories для Dashboard
const generateUserStories = () => {
  const stories: UserStory[] = [
    {
      id: "US-001",
      title: "Просмотр Live Agents в реальном времени",
      description: "Как пользователь, я хочу видеть текущее состояние агентов в реальном времени",
      persona: "System Administrator",
      priority: "P0",
      acceptance_criteria: [
        "Mission Control header отображает корректные данные",
        "Анимация агента соответствует текущему состоянию",
        "Cognitive graph подсвечивает активный узел",
        "Terminal показывает последние 20 событий",
        "Автообновление каждые 5 секунд"
      ],
      preconditions: [
        "Dashboard запущен и доступен",
        "Минимум 1 активная задача в системе",
        "PostgreSQL содержит audit_log записи"
      ],
      steps: [
        {
          step_number: 1,
          action: "Открыть главную страницу dashboard",
          expected_state: "Страница загружена, sidebar видим"
        },
        {
          step_number: 2,
          action: "Кликнуть 'Live Agents' в sidebar",
          selector: "text=Live Agents",
          expected_state: "Страница Live Agents отображена"
        },
        {
          step_number: 3,
          action: "Выбрать активную задачу из dropdown",
          selector: "[data-testid='task-selector']",
          expected_state: "Mission Control header показывает task_id"
        },
        {
          step_number: 4,
          action: "Проверить отображение анимации",
          expected_state: "Lottie анимация загружена или emoji fallback отображен"
        },
        {
          step_number: 5,
          action: "Проверить cognitive graph",
          expected_state: "Активный узел подсвечен зеленым (#00ff9f)"
        },
        {
          step_number: 6,
          action: "Проверить matrix terminal",
          expected_state: "Логи отображены с цветовой кодировкой агентов"
        }
      ],
      expected_results: [
        "Mission Control header отображен корректно",
        "3 колонки (Stage, Flow, Terminal) видимы",
        "Glassmorphism эффекты применены",
        "Neon glow на активных элементах",
        "Нет ошибок в console"
      ],
      edge_cases: [
        {
          scenario: "Нет активных задач",
          trigger: "Все задачи completed/failed",
          expected_behavior: "Показать информационное сообщение + последние 10 задач",
          severity: "major"
        },
        {
          scenario: "Lottie CDN недоступен",
          trigger: "Network error при загрузке анимации",
          expected_behavior: "Показать CSS-анимированный emoji fallback",
          severity: "minor"
        },
        {
          scenario: "Задача переходит в fail state",
          trigger: "task_failed event в audit_log",
          expected_behavior: "Анимация меняется на ❌, current_node = 'fail'",
          severity: "critical"
        },
        {
          scenario: "База данных недоступна",
          trigger: "PostgreSQL connection timeout",
          expected_behavior: "Показать error message, предложить retry",
          severity: "critical"
        }
      ],
      dependencies: ["PostgreSQL", "MCP Server", "Redis"],
      estimated_time: 15,
      automation_status: "automated"
    },

    {
      id: "US-002",
      title: "Submit новой задачи через sidebar",
      description: "Как пользователь, я хочу отправить новую задачу агентам",
      persona: "Developer",
      priority: "P0",
      acceptance_criteria: [
        "Форма submit task доступна в sidebar",
        "Description и Priority поля валидируются",
        "Успешный submit показывает task_id",
        "Новая задача появляется в списке задач"
      ],
      preconditions: [
        "MCP Server доступен на порту 8000",
        "API endpoint /api/tasks работает"
      ],
      steps: [
        {
          step_number: 1,
          action: "Открыть sidebar",
          expected_state: "Форма 'Submit New Task' видна"
        },
        {
          step_number: 2,
          action: "Ввести описание задачи",
          selector: "textarea[placeholder*='Description']",
          input: "Test task for QA automation",
          expected_state: "Текст введен в textarea"
        },
        {
          step_number: 3,
          action: "Выбрать priority slider",
          selector: "[data-testid='priority-slider']",
          input: "4",
          expected_state: "Slider на позиции 4"
        },
        {
          step_number: 4,
          action: "Нажать 'Submit Task'",
          selector: "button:has-text('Submit Task')",
          expected_state: "Request отправлен"
        },
        {
          step_number: 5,
          action: "Проверить success message",
          expected_state: "Success notification с task_id"
        }
      ],
      expected_results: [
        "Task создан в PostgreSQL",
        "task_id возвращен в response",
        "Success message отображен",
        "Форма очищена после submit"
      ],
      edge_cases: [
        {
          scenario: "Пустое описание",
          trigger: "Submit без ввода текста",
          expected_behavior: "Validation error, submit заблокирован",
          severity: "major"
        },
        {
          scenario: "MCP Server недоступен",
          trigger: "API endpoint timeout",
          expected_behavior: "Error message 'Connection failed'",
          severity: "critical"
        },
        {
          scenario: "Очень длинное описание (>10000 символов)",
          trigger: "Paste большого текста",
          expected_behavior: "Validation или truncation",
          severity: "minor"
        }
      ],
      dependencies: ["MCP Server API"],
      estimated_time: 10,
      automation_status: "automated"
    },

    {
      id: "US-003",
      title: "Визуализация Adversarial Team статуса",
      description: "Как пользователь, я хочу видеть статус всех 21 агентов",
      persona: "Team Lead",
      priority: "P1",
      acceptance_criteria: [
        "Отображены все 21 агент (1 Orchestrator + 10 пар)",
        "Индикаторы статуса (зеленый/серый) работают",
        "Agent-Critic debates расширяются",
        "События color-coded (💡, 🔍, ✏️)"
      ],
      preconditions: [
        "Задача использует adversarial team (complexity=complex/critical)",
        "Audit log содержит adversarial agent events"
      ],
      steps: [
        {
          step_number: 1,
          action: "Навигация на 'Adversarial Team' page",
          selector: "text=Adversarial Team",
          expected_state: "Страница загружена"
        },
        {
          step_number: 2,
          action: "Выбрать задачу с adversarial execution",
          expected_state: "Список агентов отображен"
        },
        {
          step_number: 3,
          action: "Проверить grid агентов",
          expected_state: "21 карточка агента видна"
        },
        {
          step_number: 4,
          action: "Expand Agent-Critic debate",
          selector: "[data-testid='debate-expander']",
          expected_state: "События debate отображены"
        }
      ],
      expected_results: [
        "Все агенты отображены корректно",
        "Статусы обновляются в реальном времени",
        "Debates читаемы и color-coded",
        "Performance адекватный (< 2s load)"
      ],
      edge_cases: [
        {
          scenario: "Задача не использует adversarial team",
          trigger: "Simple task selected",
          expected_behavior: "Показать 'No adversarial execution for this task'",
          severity: "minor"
        },
        {
          scenario: "Большое количество debate events (>1000)",
          trigger: "Long-running complex task",
          expected_behavior: "Pagination или lazy loading",
          severity: "major"
        }
      ],
      dependencies: ["Audit Log", "Adversarial Team execution"],
      estimated_time: 12,
      automation_status: "automated"
    },

    {
      id: "US-004",
      title: "Quality Metrics визуализация (5D Radar Chart)",
      description: "Как пользователь, я хочу видеть 5D quality scores",
      persona: "Quality Engineer",
      priority: "P1",
      acceptance_criteria: [
        "Radar chart отображает 5 dimensions",
        "Approval threshold (7.0) показан",
        "Bar chart breakdown по dimensions",
        "Recent evaluations с badges"
      ],
      preconditions: [
        "Quality metrics существуют в API",
        "Минимум 1 completed evaluation"
      ],
      steps: [
        {
          step_number: 1,
          action: "Открыть Quality Metrics page",
          selector: "text=Quality Metrics",
          expected_state: "Страница загружена"
        },
        {
          step_number: 2,
          action: "Проверить radar chart",
          expected_state: "Plotly radar chart visible"
        },
        {
          step_number: 3,
          action: "Hover over dimension",
          expected_state: "Tooltip с exact value"
        },
        {
          step_number: 4,
          action: "Скролл к recent evaluations",
          expected_state: "Таблица с badges (green/yellow/red)"
        }
      ],
      expected_results: [
        "Charts корректно отрисованы",
        "Данные соответствуют API",
        "Interactivity работает (hover, click)",
        "Responsive на разных экранах"
      ],
      edge_cases: [
        {
          scenario: "Нет evaluations",
          trigger: "Пустая база данных",
          expected_behavior: "Показать 'No evaluations yet'",
          severity: "major"
        },
        {
          scenario: "Некоторые dimensions = 0",
          trigger: "Incomplete evaluation",
          expected_behavior: "Chart отображает 0, не ломается",
          severity: "minor"
        }
      ],
      dependencies: ["Quality Metrics API"],
      estimated_time: 10,
      automation_status: "automated"
    }
  ];

  return stories;
};
```

## Матрица отслеживания прогресса (Progress Tracking Matrix)

### 1. Структура матрицы

```json
{
  "progress_matrix": {
    "project": "xteam-agents-dashboard",
    "generated_at": "2026-02-06T04:00:00Z",
    "total_user_stories": 50,
    "coverage_metrics": {
      "user_stories_covered": 45,
      "coverage_percentage": 90,
      "automated_tests": 38,
      "manual_tests": 7,
      "not_tested": 5
    },
    "test_execution_summary": {
      "total_tests_run": 245,
      "passed": 230,
      "failed": 10,
      "skipped": 5,
      "pass_rate": 93.88,
      "execution_time_seconds": 1250
    },
    "stories": [
      {
        "id": "US-001",
        "title": "Просмотр Live Agents в реальном времени",
        "priority": "P0",
        "status": "completed",
        "test_coverage": {
          "e2e_tests": [
            {
              "test_id": "E2E-001",
              "file": "tests/e2e/live-agents/view-agents.spec.ts",
              "status": "passed",
              "last_run": "2026-02-06T03:45:00Z",
              "duration_ms": 8500,
              "screenshots": ["baseline", "actual", "diff"]
            }
          ],
          "api_tests": [
            {
              "test_id": "API-005",
              "file": "tests/api/agents/status.spec.ts",
              "status": "passed",
              "last_run": "2026-02-06T03:42:00Z",
              "duration_ms": 250
            }
          ],
          "visual_tests": [
            {
              "test_id": "VIS-001",
              "file": "tests/visual/live-agents.spec.ts",
              "status": "passed",
              "diff_percentage": 0.05
            }
          ],
          "performance_tests": [
            {
              "test_id": "PERF-001",
              "file": "tests/performance/live-agents-load.spec.ts",
              "status": "passed",
              "metrics": {
                "page_load_time_ms": 1850,
                "time_to_interactive_ms": 2100,
                "lighthouse_score": 92
              }
            }
          ],
          "accessibility_tests": [
            {
              "test_id": "A11Y-001",
              "file": "tests/accessibility/live-agents.spec.ts",
              "status": "passed",
              "violations": 0
            }
          ]
        },
        "edge_cases_tested": [
          {
            "case_id": "EC-001-1",
            "scenario": "Нет активных задач",
            "status": "passed"
          },
          {
            "case_id": "EC-001-2",
            "scenario": "Lottie CDN недоступен",
            "status": "passed"
          },
          {
            "case_id": "EC-001-3",
            "scenario": "Задача в fail state",
            "status": "passed"
          },
          {
            "case_id": "EC-001-4",
            "scenario": "База данных недоступна",
            "status": "failed",
            "reason": "Error message не соответствует ожидаемому тексту"
          }
        ],
        "defects": [
          {
            "defect_id": "BUG-045",
            "severity": "minor",
            "description": "Error message текст не user-friendly",
            "status": "open"
          }
        ],
        "automation_percentage": 95,
        "manual_verification_needed": [
          "Визуальная проверка neon glow эффектов на разных мониторах"
        ]
      },
      {
        "id": "US-002",
        "title": "Submit новой задачи через sidebar",
        "priority": "P0",
        "status": "completed",
        "test_coverage": {
          "e2e_tests": [
            {
              "test_id": "E2E-002",
              "file": "tests/e2e/tasks/submit-task.spec.ts",
              "status": "passed",
              "last_run": "2026-02-06T03:46:00Z",
              "duration_ms": 5200
            }
          ],
          "api_tests": [
            {
              "test_id": "API-010",
              "file": "tests/api/tasks/create-task.spec.ts",
              "status": "passed",
              "last_run": "2026-02-06T03:43:00Z",
              "duration_ms": 180
            }
          ]
        },
        "edge_cases_tested": [
          {
            "case_id": "EC-002-1",
            "scenario": "Пустое описание",
            "status": "passed"
          },
          {
            "case_id": "EC-002-2",
            "scenario": "MCP Server недоступен",
            "status": "passed"
          },
          {
            "case_id": "EC-002-3",
            "scenario": "Очень длинное описание",
            "status": "passed"
          }
        ],
        "defects": [],
        "automation_percentage": 100,
        "manual_verification_needed": []
      }
    ],
    "critical_paths": [
      {
        "path_id": "CP-001",
        "name": "Happy Path - Full Task Lifecycle",
        "steps": [
          "US-002: Submit task",
          "US-001: Monitor in Live Agents",
          "US-006: View task status",
          "US-012: Check completion in audit log"
        ],
        "status": "passed",
        "execution_time_ms": 45000,
        "last_run": "2026-02-06T03:50:00Z"
      },
      {
        "path_id": "CP-002",
        "name": "Adversarial Team Execution Path",
        "steps": [
          "US-002: Submit complex task",
          "US-003: Monitor Adversarial Team",
          "US-004: Check Quality Metrics",
          "US-012: Verify audit trail"
        ],
        "status": "passed",
        "execution_time_ms": 120000,
        "last_run": "2026-02-06T03:55:00Z"
      }
    ],
    "flaky_tests": [
      {
        "test_id": "E2E-015",
        "file": "tests/e2e/chat/send-message.spec.ts",
        "flakiness_rate": 15,
        "reason": "Race condition при auto-refresh",
        "recommended_action": "Добавить explicit wait для message появления"
      }
    ],
    "test_debt": [
      {
        "story_id": "US-025",
        "title": "Export audit log to CSV",
        "priority": "P2",
        "reason_not_tested": "Низкий приоритет, требуется manual download verification",
        "planned_automation_date": "2026-02-15"
      }
    ]
  }
}
```

### 2. Dashboard для отображения матрицы

```typescript
interface ProgressDashboard {
  overview: {
    total_stories: number;
    automation_coverage: number;
    pass_rate: number;
    test_debt_count: number;
  };

  by_priority: {
    P0: { total: number; covered: number; passed: number };
    P1: { total: number; covered: number; passed: number };
    P2: { total: number; covered: number; passed: number };
    P3: { total: number; covered: number; passed: number };
  };

  by_test_type: {
    e2e: { count: number; passed: number; failed: number };
    api: { count: number; passed: number; failed: number };
    visual: { count: number; passed: number; failed: number };
    performance: { count: number; passed: number; failed: number };
    security: { count: number; passed: number; failed: number };
    accessibility: { count: number; passed: number; failed: number };
  };

  trends: {
    date: string;
    tests_run: number;
    pass_rate: number;
    new_bugs: number;
    fixed_bugs: number;
  }[];

  recommendations: string[];
}
```

## Puppeteer Test Examples

### 1. Page Object Model

```typescript
// src/page-objects/live-agents-page.ts
export class LiveAgentsPage {
  constructor(private page: Page) {}

  // Selectors
  private selectors = {
    title: 'h1:has-text("Mission Control: Live Cognitive Graph")',
    taskSelector: '[data-testid="task-selector"]',
    missionControlHeader: '.mission-control-header',
    missionId: '.mc-value.neon-text',
    stageColumn: '.glass-card:has-text("THE STAGE")',
    flowColumn: '.glass-card:has-text("THE FLOW")',
    terminalColumn: '.glass-card:has-text("THE TERMINAL")',
    animation: '.animation-container',
    animationFallback: '.agent-fallback',
    currentPhase: '.agent-status-display h2',
    cognitiveGraph: '[data-testid="cognitive-graph"]',
    terminalLines: '.terminal-line',
    neonText: '.neon-text'
  };

  // Navigation
  async navigate() {
    await this.page.goto('/');
    await this.page.click('text=Live Agents');
    await this.page.waitForSelector(this.selectors.title);
  }

  // Interactions
  async selectTask(taskId: string) {
    await this.page.selectOption(this.selectors.taskSelector, taskId);
    await this.page.waitForTimeout(1000); // Wait for data load
  }

  async waitForMissionControlHeader() {
    await this.page.waitForSelector(this.selectors.missionControlHeader);
  }

  // Assertions
  async getMissionId(): Promise<string> {
    return await this.page.textContent(this.selectors.missionId) || '';
  }

  async getCurrentPhase(): Promise<string> {
    const text = await this.page.textContent(this.selectors.currentPhase);
    return text?.trim() || '';
  }

  async isAnimationDisplayed(): Promise<boolean> {
    const animation = await this.page.$(this.selectors.animation);
    const fallback = await this.page.$(this.selectors.animationFallback);
    return !!(animation || fallback);
  }

  async getTerminalLogCount(): Promise<number> {
    const lines = await this.page.$$(this.selectors.terminalLines);
    return lines.length;
  }

  async getTerminalLogs(): Promise<Array<{timestamp: string; agent: string; message: string}>> {
    const lines = await this.page.$$(this.selectors.terminalLines);
    const logs = [];

    for (const line of lines) {
      const timestamp = await line.$eval('.timestamp', el => el.textContent);
      const agent = await line.$eval('.agent-name', el => el.textContent);
      const message = await line.$eval('.message', el => el.textContent);

      logs.push({
        timestamp: timestamp?.replace(/[\[\]]/g, '') || '',
        agent: agent?.trim() || '',
        message: message?.trim() || ''
      });
    }

    return logs;
  }

  async isGlassmorphismApplied(): Promise<boolean> {
    const stage = await this.page.$(this.selectors.stageColumn);
    if (!stage) return false;

    const styles = await stage.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        backdropFilter: computed.backdropFilter,
        background: computed.background
      };
    });

    return styles.backdropFilter.includes('blur');
  }

  async isNeonEffectPresent(): Promise<boolean> {
    const neonElements = await this.page.$$(this.selectors.neonText);
    if (neonElements.length === 0) return false;

    const textShadow = await neonElements[0].evaluate((el) => {
      return window.getComputedStyle(el).textShadow;
    });

    return textShadow !== 'none' && textShadow.length > 0;
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({
      path: `reports/screenshots/${name}.png`,
      fullPage: true
    });
  }
}
```

### 2. E2E Test Example

```typescript
// tests/e2e/live-agents/view-agents.spec.ts
import { test, expect } from '@playwright/test';
import { LiveAgentsPage } from '../../../src/page-objects/live-agents-page';

test.describe('Live Agents Page - US-001', () => {
  let liveAgentsPage: LiveAgentsPage;

  test.beforeEach(async ({ page }) => {
    liveAgentsPage = new LiveAgentsPage(page);
    await liveAgentsPage.navigate();
  });

  test('Should display Mission Control header with task info', async () => {
    // Arrange
    const taskId = await createTestTask(); // Helper function

    // Act
    await liveAgentsPage.selectTask(taskId);
    await liveAgentsPage.waitForMissionControlHeader();

    // Assert
    const displayedId = await liveAgentsPage.getMissionId();
    expect(displayedId).toContain(taskId.substring(0, 12));

    // Visual verification
    await liveAgentsPage.takeScreenshot('mission-control-header');
  });

  test('Should display agent animation or fallback', async ({ page }) => {
    // Arrange
    const taskId = await createTestTask();
    await liveAgentsPage.selectTask(taskId);

    // Act
    const animationDisplayed = await liveAgentsPage.isAnimationDisplayed();

    // Assert
    expect(animationDisplayed).toBeTruthy();

    // Verify animation state matches current phase
    const currentPhase = await liveAgentsPage.getCurrentPhase();
    expect(['ANALYZE', 'PLAN', 'EXECUTE', 'VALIDATE', 'COMMIT', 'REFLECT', 'FAIL'])
      .toContain(currentPhase);
  });

  test('Should display 3-column layout with glassmorphism', async () => {
    // Arrange
    const taskId = await createTestTask();
    await liveAgentsPage.selectTask(taskId);

    // Act
    const hasGlassmorphism = await liveAgentsPage.isGlassmorphismApplied();

    // Assert
    expect(hasGlassmorphism).toBeTruthy();
  });

  test('Should display terminal with color-coded logs', async () => {
    // Arrange
    const taskId = await createTestTask();
    await liveAgentsPage.selectTask(taskId);

    // Act
    const logs = await liveAgentsPage.getTerminalLogs();

    // Assert
    expect(logs.length).toBeGreaterThan(0);
    expect(logs.length).toBeLessThanOrEqual(20);

    // Verify log structure
    logs.forEach(log => {
      expect(log.timestamp).toMatch(/\d{2}:\d{2}:\d{2}\.\d{3}/);
      expect(log.agent).toBeTruthy();
      expect(log.message).toBeTruthy();
    });
  });

  test('Should apply neon text effects', async () => {
    // Arrange
    const taskId = await createTestTask();
    await liveAgentsPage.selectTask(taskId);

    // Act
    const hasNeonEffect = await liveAgentsPage.isNeonEffectPresent();

    // Assert
    expect(hasNeonEffect).toBeTruthy();
  });

  test('EDGE CASE: Should handle Lottie CDN failure gracefully', async ({ page, context }) => {
    // Arrange - Block Lottie CDN
    await context.route('**/lottie.host/**', route => route.abort());

    const taskId = await createTestTask();
    await liveAgentsPage.selectTask(taskId);

    // Act
    await page.waitForTimeout(3000); // Wait for fallback

    // Assert - Fallback emoji should be displayed
    const fallback = await page.$('.agent-fallback');
    expect(fallback).toBeTruthy();

    const emoji = await page.$('.agent-emoji');
    expect(emoji).toBeTruthy();
  });

  test('EDGE CASE: Should handle no active tasks scenario', async ({ page }) => {
    // Arrange - Clear all active tasks
    await clearActiveTasks();

    // Act
    await liveAgentsPage.navigate();

    // Assert
    const infoMessage = await page.textContent('.stInfo');
    expect(infoMessage).toContain('No active tasks running currently');
  });

  test('EDGE CASE: Should handle database connection failure', async ({ page, context }) => {
    // Arrange - Block database queries
    await context.route('**/api/tasks**', route => route.abort());

    // Act
    await liveAgentsPage.navigate();

    // Assert
    const errorMessage = await page.textContent('.stError');
    expect(errorMessage).toContain('Connection error');
  });

  test('PERFORMANCE: Page should load within 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await liveAgentsPage.navigate();
    const taskId = await createTestTask();
    await liveAgentsPage.selectTask(taskId);
    await liveAgentsPage.waitForMissionControlHeader();

    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('ACCESSIBILITY: Page should have no a11y violations', async ({ page }) => {
    await liveAgentsPage.navigate();

    const taskId = await createTestTask();
    await liveAgentsPage.selectTask(taskId);

    // Inject axe-core
    await injectAxe(page);
    const results = await checkA11y(page);

    expect(results.violations).toHaveLength(0);
  });
});

// Helper functions
async function createTestTask(): Promise<string> {
  // API call to create test task
  const response = await fetch('http://localhost:8000/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description: 'QA Test Task',
      priority: 3
    })
  });
  const data = await response.json();
  return data.task_id;
}

async function clearActiveTasks() {
  // Database cleanup
}

async function injectAxe(page: Page) {
  await page.addScriptTag({
    url: 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js'
  });
}

async function checkA11y(page: Page) {
  return await page.evaluate(() => {
    return (window as any).axe.run();
  });
}
```

### 3. API Test Example

```typescript
// tests/api/tasks/create-task.spec.ts
import axios from 'axios';
import { expect } from '@jest/globals';

const API_BASE_URL = 'http://localhost:8000';

describe('Tasks API - US-002', () => {
  let createdTaskId: string;

  afterEach(async () => {
    // Cleanup
    if (createdTaskId) {
      await axios.post(`${API_BASE_URL}/api/tasks/${createdTaskId}/cancel`);
    }
  });

  test('POST /api/tasks - Should create new task with valid data', async () => {
    // Arrange
    const payload = {
      description: 'Test task from QA automation',
      priority: 3
    };

    // Act
    const response = await axios.post(`${API_BASE_URL}/api/tasks`, payload);
    createdTaskId = response.data.task_id;

    // Assert
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('task_id');
    expect(response.data.task_id).toMatch(/^[a-f0-9-]{36}$/); // UUID format
    expect(response.data.status).toBe('pending');
  });

  test('POST /api/tasks - Should validate required fields', async () => {
    // Arrange
    const payload = {
      priority: 3
      // description missing
    };

    // Act & Assert
    await expect(
      axios.post(`${API_BASE_URL}/api/tasks`, payload)
    ).rejects.toMatchObject({
      response: {
        status: 422 // Unprocessable Entity
      }
    });
  });

  test('POST /api/tasks - Should handle priority validation', async () => {
    // Arrange
    const payload = {
      description: 'Test',
      priority: 10 // Invalid (max is 5)
    };

    // Act & Assert
    await expect(
      axios.post(`${API_BASE_URL}/api/tasks`, payload)
    ).rejects.toMatchObject({
      response: {
        status: 422
      }
    });
  });

  test('GET /api/tasks - Should return list of tasks', async () => {
    // Arrange
    await axios.post(`${API_BASE_URL}/api/tasks`, {
      description: 'Test task 1',
      priority: 2
    });

    // Act
    const response = await axios.get(`${API_BASE_URL}/api/tasks`);

    // Assert
    expect(response.status).toBe(200);
    expect(Array.isArray(response.data.tasks)).toBeTruthy();
    expect(response.data.tasks.length).toBeGreaterThan(0);
  });

  test('PERFORMANCE: API should respond within 500ms', async () => {
    const startTime = Date.now();

    await axios.post(`${API_BASE_URL}/api/tasks`, {
      description: 'Performance test',
      priority: 3
    });

    const responseTime = Date.now() - startTime;

    expect(responseTime).toBeLessThan(500);
  });
});
```

### 4. Visual Regression Test

```typescript
// tests/visual/live-agents.spec.ts
import { test, expect } from '@playwright/test';
import { toMatchImageSnapshot } from 'jest-image-snapshot';

expect.extend({ toMatchImageSnapshot });

test.describe('Visual Regression - Live Agents', () => {
  test('Should match baseline screenshot', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Live Agents');

    // Wait for animations to settle
    await page.waitForTimeout(2000);

    // Take screenshot
    const screenshot = await page.screenshot({ fullPage: true });

    // Compare with baseline
    expect(screenshot).toMatchImageSnapshot({
      failureThreshold: 0.01,
      failureThresholdType: 'percent'
    });
  });

  test('Should detect CSS changes in Mission Control header', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Live Agents');

    const header = await page.$('.mission-control-header');
    const screenshot = await header?.screenshot();

    expect(screenshot).toMatchImageSnapshot({
      customSnapshotIdentifier: 'mission-control-header',
      failureThreshold: 0.005
    });
  });

  test('Should verify glassmorphism effect visually', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Live Agents');

    const glassCard = await page.$('.glass-card');
    const screenshot = await glassCard?.screenshot();

    expect(screenshot).toMatchImageSnapshot({
      customSnapshotIdentifier: 'glassmorphism-card'
    });
  });
});
```

## Orchestrator Agent Implementation

```typescript
// src/agents/orchestrator.ts
export class QAOrchestrator {
  private config: QAConfig;
  private agents: Map<string, QAAgent>;
  private progressMatrix: ProgressMatrix;

  constructor(config: QAConfig) {
    this.config = config;
    this.agents = new Map();
    this.progressMatrix = new ProgressMatrix();

    this.initializeAgents();
  }

  private initializeAgents() {
    // Register all QA agents
    this.agents.set('test_architect', new TestArchitect(this.config));
    this.agents.set('user_story_analyst', new UserStoryAnalyst(this.config));
    this.agents.set('e2e_test_engineer', new E2ETestEngineer(this.config));
    this.agents.set('api_test_engineer', new APITestEngineer(this.config));
    this.agents.set('visual_regression_tester', new VisualRegressionTester(this.config));
    this.agents.set('performance_tester', new PerformanceTester(this.config));
    this.agents.set('security_tester', new SecurityTester(this.config));
    this.agents.set('accessibility_tester', new AccessibilityTester(this.config));
    this.agents.set('test_reporter', new TestReporter(this.config));
  }

  async executeQAPhase(phase: 'analysis' | 'test_creation' | 'execution' | 'reporting') {
    console.log(`🚀 Starting QA Phase: ${phase}`);

    switch (phase) {
      case 'analysis':
        await this.runAnalysisPhase();
        break;
      case 'test_creation':
        await this.runTestCreationPhase();
        break;
      case 'execution':
        await this.runExecutionPhase();
        break;
      case 'reporting':
        await this.runReportingPhase();
        break;
    }
  }

  private async runAnalysisPhase() {
    // Step 1: Test Architect analyzes requirements
    const architect = this.agents.get('test_architect') as TestArchitect;
    const testStrategy = await architect.createTestStrategy();

    // Step 2: User Story Analyst generates all stories
    const analyst = this.agents.get('user_story_analyst') as UserStoryAnalyst;
    const userStories = await analyst.generateUserStories();

    // Update progress matrix
    this.progressMatrix.initialize(userStories);

    console.log(`✅ Analysis complete: ${userStories.length} user stories generated`);
  }

  private async runTestCreationPhase() {
    const stories = this.progressMatrix.getUserStories();

    // Parallel test creation by multiple agents
    await Promise.all([
      this.createE2ETests(stories),
      this.createAPITests(stories),
      this.createVisualTests(stories),
      this.createPerformanceTests(stories),
      this.createSecurityTests(stories),
      this.createAccessibilityTests(stories)
    ]);

    console.log('✅ Test creation complete');
  }

  private async createE2ETests(stories: UserStory[]) {
    const engineer = this.agents.get('e2e_test_engineer') as E2ETestEngineer;

    for (const story of stories.filter(s => s.priority === 'P0' || s.priority === 'P1')) {
      await engineer.createTest(story);
      this.progressMatrix.updateStory(story.id, { e2e_test_created: true });
    }
  }

  private async runExecutionPhase() {
    console.log('🧪 Executing all tests...');

    // Execute tests in order
    const results = {
      e2e: await this.executeTests('e2e'),
      api: await this.executeTests('api'),
      visual: await this.executeTests('visual'),
      performance: await this.executeTests('performance'),
      security: await this.executeTests('security'),
      accessibility: await this.executeTests('accessibility')
    };

    // Update progress matrix
    this.progressMatrix.updateExecutionResults(results);

    console.log('✅ Test execution complete');
  }

  private async executeTests(type: string): Promise<TestResults> {
    // Run tests using appropriate test runner
    const command = `npm run test:${type}`;
    const output = await exec(command);

    return this.parseTestResults(output, type);
  }

  private async runReportingPhase() {
    const reporter = this.agents.get('test_reporter') as TestReporter;

    await reporter.generateReports({
      matrix: this.progressMatrix.export(),
      htmlReport: true,
      slackNotification: this.config.reporting.slack_notifications,
      dashboardUpdate: true
    });

    console.log('✅ Reports generated');
  }

  async getProgressMatrix(): Promise<ProgressMatrixData> {
    return this.progressMatrix.export();
  }

  async getAgentStatus(role: string): Promise<AgentStatus> {
    const agent = this.agents.get(role);
    return agent ? agent.getStatus() : { status: 'not_found' };
  }
}
```

## Интеграция с xteam-agents

### Добавление QA Agent в систему

```python
# src/xteam_agents/agents/qa_orchestrator.py
from typing import Dict, List, Optional
from dataclasses import dataclass
import subprocess
import json

@dataclass
class QAExecutionConfig:
    phase: str  # 'analysis' | 'test_creation' | 'execution' | 'reporting'
    target: str  # 'dashboard' | 'api' | 'full'
    parallel: bool = True

class QAOrchestratorAgent:
    """QA Orchestrator интегрированный в xteam-agents"""

    def __init__(self, memory_manager, llm_provider):
        self.memory = memory_manager
        self.llm = llm_provider
        self.qa_project_path = "./qa-automation"

    async def execute_qa_phase(self, config: QAExecutionConfig) -> Dict:
        """Execute QA testing phase"""

        # Store intent in episodic memory
        await self.memory.episodic.write({
            "event": "qa_phase_started",
            "phase": config.phase,
            "target": config.target
        })

        # Execute TypeScript orchestrator
        result = await self._run_ts_orchestrator(config)

        # Store results in semantic memory (validated knowledge)
        if result["status"] == "success":
            await self.memory.semantic.write({
                "type": "qa_execution_result",
                "phase": config.phase,
                "metrics": result["metrics"],
                "validated": True
            })

        return result

    async def _run_ts_orchestrator(self, config: QAExecutionConfig) -> Dict:
        """Run TypeScript QA Orchestrator"""

        cmd = [
            "npm", "run", "qa:orchestrate",
            "--",
            f"--phase={config.phase}",
            f"--target={config.target}"
        ]

        try:
            process = subprocess.run(
                cmd,
                cwd=self.qa_project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if process.returncode == 0:
                return {
                    "status": "success",
                    "output": process.stdout,
                    "metrics": self._parse_metrics(process.stdout)
                }
            else:
                return {
                    "status": "failed",
                    "error": process.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "QA execution exceeded timeout"
            }

    async def get_progress_matrix(self) -> Dict:
        """Retrieve current progress matrix"""

        matrix_path = f"{self.qa_project_path}/reports/progress_matrix.json"

        try:
            with open(matrix_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"error": "Progress matrix not found"}

    def _parse_metrics(self, output: str) -> Dict:
        """Parse test execution metrics from output"""
        # Extract JSON metrics from output
        try:
            lines = output.split('\n')
            for line in lines:
                if line.startswith('METRICS:'):
                    return json.loads(line.replace('METRICS:', ''))
        except:
            pass

        return {}
```

## Continuous Integration

```yaml
# .github/workflows/qa-automation.yml
name: QA Automation

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  qa-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd qa-automation
          npm install

      - name: Run QA Analysis Phase
        run: |
          npm run qa:orchestrate -- --phase=analysis --target=dashboard

      - name: Upload User Stories
        uses: actions/upload-artifact@v3
        with:
          name: user-stories
          path: qa-automation/reports/user_stories_complete.json

  qa-execution:
    needs: qa-analysis
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-type: [e2e, api, visual, performance, security, accessibility]

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: |
          npm run wait-for-services

      - name: Run ${{ matrix.test-type }} tests
        run: |
          cd qa-automation
          npm run test:${{ matrix.test-type }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results-${{ matrix.test-type }}
          path: qa-automation/reports/test-results/

  qa-reporting:
    needs: qa-execution
    runs-on: ubuntu-latest
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v3

      - name: Generate comprehensive report
        run: |
          npm run qa:orchestrate -- --phase=reporting

      - name: Upload Progress Matrix
        uses: actions/upload-artifact@v3
        with:
          name: progress-matrix
          path: qa-automation/reports/progress_matrix.json

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const matrix = JSON.parse(fs.readFileSync('qa-automation/reports/progress_matrix.json'));
            const comment = `## QA Automation Results

            **Coverage**: ${matrix.coverage_metrics.coverage_percentage}%
            **Tests Run**: ${matrix.test_execution_summary.total_tests_run}
            **Pass Rate**: ${matrix.test_execution_summary.pass_rate}%

            [View Full Report](${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

## Заключение

Эта comprehensive система QA тестирования обеспечивает:

1. ✅ **Полное покрытие user stories** - автоматическая генерация всех возможных сценариев
2. ✅ **Матрица отслеживания** - реал-тайм мониторинг прогресса по всем типам тестов
3. ✅ **Роле-ориентированная архитектура** - каждый агент специализируется на своей области
4. ✅ **Puppeteer интеграция** - E2E тесты для критических путей
5. ✅ **CI/CD интеграция** - автоматическое выполнение при каждом PR
6. ✅ **Comprehensive reporting** - детальные отчеты с метриками и recommendations

SOLO Builder может использовать этот документ как blueprint для создания полноценной QA automation системы.
