"""
Research Team Base Classes

Базовые классы для агентов исследовательской команды.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager
from xteam_agents.agents.research_team.research_state import (
    ResearchState,
    ResearchArtifact,
    ResearchFinding,
)


class ResearchAgent(ABC):
    """
    Базовый класс для исследовательского агента.

    Все исследовательские агенты наследуются от этого класса
    и реализуют метод conduct_research для выполнения своей роли.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        memory_manager: MemoryManager,
        agent_name: str,
        role: str,
        expertise: List[str],
        research_methods: List[str],
    ):
        """
        Инициализация исследовательского агента.

        Args:
            llm_provider: Провайдер LLM
            memory_manager: Менеджер памяти
            agent_name: Имя агента
            role: Роль в команде
            expertise: Области экспертизы
            research_methods: Методы исследования
        """
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
        self.agent_name = agent_name
        self.role = role
        self.expertise = expertise
        self.research_methods = research_methods

    @abstractmethod
    async def conduct_research(self, state: ResearchState) -> Dict[str, Any]:
        """
        Основной метод для проведения исследования.

        Args:
            state: Текущее состояние исследования

        Returns:
            Обновления состояния после исследования
        """
        pass

    async def query_knowledge_base(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Запрос к базе знаний для получения релевантной информации.

        Args:
            query: Поисковый запрос
            context: Дополнительный контекст

        Returns:
            Список релевантных документов/фактов
        """
        results = await self.memory_manager.search_semantic(
            query=query,
            limit=10,
            filters=context or {}
        )
        return results

    async def store_finding(
        self,
        state: ResearchState,
        title: str,
        description: str,
        evidence: List[str],
        confidence: float,
        implications: List[str],
        recommendations: List[str],
    ) -> ResearchFinding:
        """
        Сохранение научного открытия.

        Args:
            state: Состояние исследования
            title: Название находки
            description: Описание
            evidence: Доказательства
            confidence: Уровень уверенности
            implications: Последствия
            recommendations: Рекомендации

        Returns:
            Объект научного открытия
        """
        finding = ResearchFinding(
            finding_id=f"{state.task_id}_{self.agent_name}_{len(state.findings)}",
            title=title,
            description=description,
            evidence=evidence,
            confidence=confidence,
            implications=implications,
            recommendations=recommendations,
            discovered_by=self.agent_name,
            discovered_at=datetime.utcnow(),
        )
        return finding

    async def create_artifact(
        self,
        state: ResearchState,
        artifact_type: str,
        title: str,
        description: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ResearchArtifact:
        """
        Создание исследовательского артефакта.

        Args:
            state: Состояние исследования
            artifact_type: Тип артефакта
            title: Название
            description: Описание
            content: Содержимое
            metadata: Метаданные

        Returns:
            Объект артефакта
        """
        artifact = ResearchArtifact(
            artifact_type=artifact_type,
            title=title,
            description=description,
            content=content,
            metadata=metadata or {},
            created_by=self.agent_name,
            created_at=datetime.utcnow(),
            validated=False,
        )
        return artifact

    async def generate_with_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """
        Генерация текста с помощью LLM.

        Args:
            system_prompt: Системный промпт
            user_prompt: Пользовательский промпт
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Сгенерированный текст
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.llm_provider.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.get("content", "")

    def get_system_prompt(self) -> str:
        """
        Получение системного промпта для агента.

        Returns:
            Системный промпт с описанием роли и экспертизы
        """
        return f"""Вы - {self.agent_name}, {self.role} в научно-исследовательской команде StudyNinja.

РОЛЬ И ЭКСПЕРТИЗА:
{self.role}

ОБЛАСТИ ЭКСПЕРТИЗЫ:
{chr(10).join(f"- {exp}" for exp in self.expertise)}

МЕТОДЫ ИССЛЕДОВАНИЯ:
{chr(10).join(f"- {method}" for method in self.research_methods)}

ВАША ЗАДАЧА:
Проводить глубокие научные исследования, разрабатывать инновационные подходы и создавать
высококачественные образовательные материалы для экосистемы StudyNinja.

ПРИНЦИПЫ РАБОТЫ:
1. Научная строгость - все утверждения должны быть обоснованы
2. Инновационность - искать новые подходы и методы
3. Практическая применимость - результаты должны быть внедряемы
4. Междисциплинарность - использовать знания из разных областей
5. Качество данных - особое внимание к качеству датасетов
6. Этика - соблюдать этические принципы в исследованиях

ФОРМАТ РЕЗУЛЬТАТОВ:
- Четкие выводы с доказательствами
- Конкретные рекомендации для разработки
- Метрики для оценки эффективности
- Описание ограничений и рисков
"""


class ResearchCritic(ABC):
    """
    Базовый класс для критика исследований.

    Критики проводят peer review и обеспечивают качество исследований.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        memory_manager: MemoryManager,
        critic_name: str,
        review_focus: List[str],
        quality_criteria: List[str],
    ):
        """
        Инициализация критика.

        Args:
            llm_provider: Провайдер LLM
            memory_manager: Менеджер памяти
            critic_name: Имя критика
            review_focus: Фокусы рецензирования
            quality_criteria: Критерии качества
        """
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
        self.critic_name = critic_name
        self.review_focus = review_focus
        self.quality_criteria = quality_criteria

    @abstractmethod
    async def review_research(
        self,
        state: ResearchState,
        artifact_to_review: Optional[ResearchArtifact] = None,
    ) -> Dict[str, Any]:
        """
        Рецензирование исследования.

        Args:
            state: Состояние исследования
            artifact_to_review: Конкретный артефакт для рецензирования

        Returns:
            Результаты рецензии
        """
        pass

    async def generate_review(
        self,
        content: str,
        focus_areas: List[str],
    ) -> Dict[str, Any]:
        """
        Генерация рецензии с помощью LLM.

        Args:
            content: Контент для рецензирования
            focus_areas: Области фокуса

        Returns:
            Результаты рецензии
        """
        system_prompt = f"""Вы - {self.critic_name}, эксперт по рецензированию научных исследований.

ФОКУСЫ РЕЦЕНЗИРОВАНИЯ:
{chr(10).join(f"- {focus}" for focus in self.review_focus)}

КРИТЕРИИ КАЧЕСТВА:
{chr(10).join(f"- {criterion}" for criterion in self.quality_criteria)}

ЗАДАЧА:
Провести строгую, но конструктивную рецензию представленного материала.
Выявить сильные стороны, слабости, потенциальные проблемы и дать рекомендации по улучшению.

ФОРМАТ ОТВЕТА:
1. Общая оценка (0-10)
2. Сильные стороны (список)
3. Слабости и проблемы (список)
4. Конкретные рекомендации (список)
5. Критические замечания (если есть)
6. Вердикт: APPROVED / NEEDS_REVISION / REJECTED
"""

        user_prompt = f"""ОБЛАСТИ ФОКУСА:
{chr(10).join(f"- {area}" for area in focus_areas)}

МАТЕРИАЛ ДЛЯ РЕЦЕНЗИИ:
{content}

Проведите тщательную рецензию и предоставьте развернутый анализ."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.llm_provider.generate(
            messages=messages,
            temperature=0.3,  # Низкая температура для более строгой оценки
            max_tokens=3000,
        )

        # TODO: Парсинг структурированного ответа
        return {
            "review_text": response.get("content", ""),
            "reviewer": self.critic_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_quality_score(self, review: Dict[str, Any]) -> float:
        """
        Вычисление оценки качества из рецензии.

        Args:
            review: Рецензия

        Returns:
            Оценка качества (0-1)
        """
        # TODO: Реализовать парсинг оценки из текста рецензии
        return 0.8  # Placeholder
