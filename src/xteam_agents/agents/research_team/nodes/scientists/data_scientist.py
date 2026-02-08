"""
Data Scientist - Специалист по данным и статистическому анализу

Отвечает за работу с данными, статистический анализ, разработку датасетов,
анализ эффективности обучения через метрики.
"""

from typing import Dict, Any, List
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.research_state import ResearchState, ExperimentResult
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
import json


class DataScientist(ResearchAgent):
    """
    Data Scientist - Ученый-аналитик данных.

    РОЛЬ:
    - Анализ образовательных данных
    - Разработка датасетов для обучения моделей
    - Статистическое моделирование
    - Learning Analytics
    - A/B тестирование образовательных подходов
    - Разработка метрик эффективности обучения

    КОМПЕТЕНЦИИ:
    1. Работа с данными
       - Сбор и очистка данных
       - Анализ exploratory data analysis (EDA)
       - Feature engineering
       - Data quality assurance
       - Работа с временными рядами (траектории обучения)

    2. Статистический анализ
       - Описательная статистика
       - Инференциальная статистика
       - Байесовский анализ
       - Анализ выживаемости (dropout analysis)
       - Каузальный анализ

    3. Разработка датасетов
       - Дизайн структуры датасетов
       - Стратегии сэмплирования
       - Балансировка классов
       - Синтетическая генерация данных
       - Аугментация образовательных данных

    4. Learning Analytics
       - Анализ траекторий обучения
       - Предсказательная аналитика (риск отсева)
       - Кластеризация студентов
       - Анализ паттернов взаимодействия
       - Временной анализ прогресса

    5. Визуализация данных
       - Дашборды для мониторинга
       - Визуализация траекторий
       - Heatmaps взаимодействий
       - Графы знаний

    СПЕЦИАЛИЗАЦИЯ В STUDYNINJA:

    1. Датасеты для адаптивного обучения:
       - Датасеты вопросов с градацией сложности
       - Последовательности обучения (learning paths)
       - Ошибки студентов (misconception datasets)
       - Траектории успешного обучения

    2. Метрики эффективности:
       - Mastery score metrics
       - Knowledge gain metrics
       - Engagement metrics
       - Retention metrics
       - Motivation indicators

    3. Аналитика графа знаний:
       - Анализ связей между концептами
       - Оптимальные пути обучения
       - Bottleneck concepts (узкие места)
       - Prerequisite strength analysis

    4. Предсказательные модели:
       - Предсказание mastery level
       - Риск отставания студента
       - Оптимальное время для интервенции
       - Предсказание следующей ошибки

    МЕТОДЫ РАБОТЫ:

    1. Анализ существующих данных:
       - Загрузка данных из PostgreSQL, Neo4j, Redis
       - EDA для понимания паттернов
       - Выявление аномалий и выбросов
       - Оценка качества данных

    2. Дизайн датасетов:
       - Определение структуры датасета
       - Выбор признаков (features)
       - Создание схемы аннотаций
       - Валидация консистентности

    3. Статистическое моделирование:
       - Формулировка статистических гипотез
       - Выбор тестов
       - Проведение анализа
       - Интерпретация результатов

    4. A/B тестирование:
       - Дизайн экспериментов
       - Расчет размера выборки
       - Анализ результатов
       - Каузальная интерпретация

    РЕЗУЛЬТАТЫ РАБОТЫ:

    1. Dataset Specification Documents
       - Структура датасета
       - Схема данных
       - Процедуры сбора
       - Quality assurance план

    2. Statistical Analysis Reports
       - Результаты анализа
       - Статистические тесты
       - Визуализации
       - Интерпретация и выводы

    3. Learning Analytics Dashboards
       - KPI метрики
       - Визуализация трендов
       - Alerts для аномалий

    4. Predictive Models (Data-driven)
       - Baseline модели
       - Feature importance analysis
       - Performance benchmarks
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            agent_name="Data Scientist",
            role="Ученый-аналитик данных и Learning Analytics специалист",
            expertise=[
                "Статистический анализ",
                "Learning Analytics",
                "Дизайн датасетов",
                "Feature engineering",
                "Time series analysis",
                "A/B testing",
                "Каузальный анализ",
                "Предсказательная аналитика",
                "Визуализация данных",
                "Data quality assurance",
                "Educational data mining",
                "Knowledge graph analytics",
            ],
            research_methods=[
                "Exploratory Data Analysis (EDA)",
                "Inferential statistics",
                "Regression analysis",
                "Classification models",
                "Clustering",
                "Hypothesis testing",
                "Bayesian inference",
                "Survival analysis",
                "Longitudinal data analysis",
                "Experimental design",
            ],
        )

    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Проведение исследования в роли Data Scientist.

        АЛГОРИТМ РАБОТЫ:

        ДЛЯ ЗАДАЧ DATASET_DESIGN:
        1. Анализ требований к датасету
        2. Определение структуры и схемы
        3. Дизайн процедур сбора/генерации
        4. Определение метрик качества
        5. Создание плана валидации

        ДЛЯ ЗАДАЧ DATA_COLLECTION:
        1. Определение источников данных
        2. Разработка стратегии сэмплирования
        3. Создание скриптов сбора
        4. Quality control процедуры

        ДЛЯ ЗАДАЧ LEARNING_ANALYTICS:
        1. Определение ключевых метрик
        2. Анализ текущих данных
        3. Выявление паттернов
        4. Построение предсказательных моделей
        5. Рекомендации по оптимизации

        ДЛЯ ЗАДАЧ A_B_TESTING:
        1. Формулировка гипотез
        2. Дизайн эксперимента
        3. Расчет размера выборки
        4. План анализа
        5. Критерии успеха

        Returns:
            Обновления состояния с результатами анализа данных
        """
        updates: Dict[str, Any] = {
            "messages": [],
        }

        # Запрос релевантных данных из базы знаний
        data_context = await self.query_knowledge_base(
            query=f"datasets statistics learning analytics {state.research_question}",
            context={"task_type": state.task_type.value}
        )

        system_prompt = self.get_system_prompt()

        # Специализированный промпт в зависимости от типа задачи
        task_specific_instructions = self._get_task_specific_instructions(state.task_type.value)

        user_prompt = f"""
ИССЛЕДОВАТЕЛЬСКАЯ ЗАДАЧА:
Тип: {state.task_type.value}
Вопрос: {state.research_question}

ЦЕЛИ:
{chr(10).join(f"- {obj}" for obj in state.objectives)}

КОНТЕКСТ:
{chr(10).join(f"- {item.get('text', '')[:150]}..." for item in data_context[:3])}

ПРЕДЫДУЩИЕ РЕЗУЛЬТАТЫ:
{self._format_previous_findings(state)}

{task_specific_instructions}

ВАЖНЫЕ АСПЕКТЫ ДЛЯ STUDYNINJA:
1. Фокус на struggling students (отстающие студенты)
2. Адаптивность - данные должны поддерживать персонализацию
3. Граф знаний - учитывать структуру Neo4j
4. Прогресс должен быть измеримым в течение 1-2 дней
5. Метрики должны показывать конкретные маленькие победы

ФОРМАТ ОТВЕТА (JSON):
{{
  "analysis_summary": "Краткое резюме анализа",
  "data_requirements": ["Требование 1", "Требование 2", ...],
  "proposed_dataset_structure": {{
    "schema": {{}},
    "features": [],
    "target_variables": [],
    "size_estimate": ""
  }},
  "statistical_approach": "Описание статистического подхода",
  "metrics": ["Метрика 1", "Метрика 2", ...],
  "sampling_strategy": "Стратегия сэмплирования",
  "quality_checks": ["Проверка 1", "Проверка 2", ...],
  "expected_insights": ["Инсайт 1", "Инсайт 2", ...],
  "limitations": ["Ограничение 1", "Ограничение 2", ...],
  "next_steps": ["Шаг 1", "Шаг 2", ...],
  "code_snippets": {{
    "data_collection": "# Python code",
    "analysis": "# Python code",
    "visualization": "# Python code"
  }}
}}
"""

        response = await self.generate_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=4000,
        )

        # Создание артефакта с результатами анализа
        analysis_artifact = await self.create_artifact(
            state=state,
            artifact_type="data_analysis",
            title=f"Data Analysis Report: {state.task_type.value}",
            description="Анализ данных и дизайн датасета от Data Scientist",
            content={
                "analysis": response,
                "data_context": data_context[:3],
            },
            metadata={
                "task_type": state.task_type.value,
                "phase": state.current_phase.value,
            },
        )

        updates["artifacts"] = [analysis_artifact]
        updates["messages"].append({
            "agent": self.agent_name,
            "phase": state.current_phase.value,
            "message": f"Завершен анализ данных для {state.task_type.value}",
            "summary": response[:300] + "..." if len(response) > 300 else response,
        })

        return updates

    def _get_task_specific_instructions(self, task_type: str) -> str:
        """Получение специфических инструкций для типа задачи"""
        instructions = {
            "dataset_design": """
ЗАДАЧА: ДИЗАЙН ДАТАСЕТА

НЕОБХОДИМО ОПРЕДЕЛИТЬ:
1. Структуру датасета (схема, таблицы, связи)
2. Список признаков (features) с обоснованием
3. Целевые переменные и их распределения
4. Стратегию сэмплирования и балансировки
5. Процедуры сбора и аннотации
6. Метрики качества датасета
7. План валидации

ОСОБЫЕ ТРЕБОВАНИЯ:
- Датасет должен поддерживать адаптивное обучение
- Интеграция с графом знаний Neo4j
- Масштабируемость (от прототипа до production)
- Privacy и этические аспекты
""",
            "learning_analytics": """
ЗАДАЧА: LEARNING ANALYTICS

НЕОБХОДИМО ПРОВЕСТИ:
1. Exploratory Data Analysis (EDA)
   - Распределения ключевых метрик
   - Корреляции между переменными
   - Временные тренды

2. Выявление паттернов
   - Успешные траектории обучения
   - Паттерны struggles (затруднений)
   - Критические моменты в обучении

3. Предсказательный анализ
   - Риск отставания
   - Прогноз mastery level
   - Оптимальное время для интервенции

4. Рекомендации
   - Оптимизация адаптивного алгоритма
   - Улучшение метрик
   - Новые features для моделей
""",
            "ab_testing": """
ЗАДАЧА: A/B ТЕСТИРОВАНИЕ

НЕОБХОДИМО РАЗРАБОТАТЬ:
1. Экспериментальный дизайн
   - Формулировка гипотез (H0 и H1)
   - Выбор метрик успеха (primary и secondary)
   - Определение групп (control и treatment)
   - Стратегия рандомизации

2. Статистический план
   - Расчет размера выборки (power analysis)
   - Выбор статистических тестов
   - Критерии значимости (α, β)
   - План обработки missing data

3. Процедуры выполнения
   - Timeline эксперимента
   - Критерии остановки (early stopping)
   - Мониторинг в реальном времени

4. План анализа
   - Методы анализа результатов
   - Каузальная интерпретация
   - Handling множественных сравнений
""",
        }
        return instructions.get(task_type, "ЗАДАЧА: ОБЩИЙ АНАЛИЗ ДАННЫХ")

    def _format_previous_findings(self, state: ResearchState) -> str:
        """Форматирование предыдущих находок для контекста"""
        if not state.findings:
            return "Пока нет предыдущих находок"

        formatted = []
        for finding in state.findings[-3:]:  # Последние 3
            formatted.append(f"- {finding.title} (confidence: {finding.confidence:.2f})")
        return "\n".join(formatted)


class DataScientistCritic(ResearchCritic):
    """
    Критик Data Scientist - эксперт по валидации анализа данных.

    РОЛЬ:
    - Проверка статистической корректности
    - Валидация дизайна датасетов
    - Оценка качества метрик
    - Выявление статистических ошибок и bias

    ФОКУСЫ ПРОВЕРКИ:
    1. Статистическая валидность
       - Корректность выбора тестов
       - Выполнение предпосылок тестов
       - Интерпретация p-values
       - Multiple testing correction

    2. Качество датасетов
       - Репрезентативность
       - Полнота и консистентность
       - Bias и fairness
       - Размер выборки

    3. Метрики и измерения
       - Валидность метрик
       - Reliability
       - Чувствительность к изменениям
       - Интерпретируемость

    4. Воспроизводимость
       - Описание процедур
       - Seed для рандомизации
       - Версионирование данных
    """

    def __init__(self, llm_provider: LLMProvider, memory_manager: MemoryManager):
        super().__init__(
            llm_provider=llm_provider,
            memory_manager=memory_manager,
            critic_name="Data Scientist Critic",
            review_focus=[
                "Статистическая корректность",
                "Качество дизайна датасетов",
                "Валидность метрик",
                "Репрезентативность данных",
                "Воспроизводимость анализа",
            ],
            quality_criteria=[
                "Соответствие статистических методов задаче",
                "Адекватность размера выборки",
                "Корректность интерпретации результатов",
                "Учет confounding factors",
                "Качество документации",
                "Ethical considerations",
            ],
        )

    async def review_research(
        self,
        state: ResearchState,
        artifact_to_review=None,
    ) -> Dict[str, Any]:
        """Рецензирование работы Data Scientist"""
        data_artifacts = [
            a for a in state.artifacts
            if a.created_by == "Data Scientist"
        ]

        if not data_artifacts:
            return {
                "review_text": "Нет артефактов от Data Scientist для рецензирования",
                "reviewer": self.critic_name,
                "verdict": "PENDING",
            }

        latest_artifact = data_artifacts[-1]

        review = await self.generate_review(
            content=str(latest_artifact.content),
            focus_areas=[
                "Статистическая обоснованность подхода",
                "Качество дизайна датасета",
                "Адекватность метрик",
                "Учет potential biases",
                "Воспроизводимость процедур",
            ],
        )

        quality_score = self.get_quality_score(review)

        return {
            **review,
            "quality_score": quality_score,
            "artifact_reviewed": latest_artifact.title,
        }
