"""
Unit tests for Research Team

Тесты базовой функциональности исследовательской команды.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from xteam_agents.agents.research_team import (
    ResearchState,
    ResearchTaskType,
    ResearchComplexity,
    ResearchPhase,
    ResearchArtifact,
    ResearchFinding,
)
from xteam_agents.agents.research_team.research_base import ResearchAgent, ResearchCritic
from xteam_agents.agents.research_team.nodes.scientists.chief_scientist import (
    ChiefScientist,
    ChiefScientistCritic,
)
from xteam_agents.llm.provider import LLMProvider
from xteam_agents.memory.manager import MemoryManager


class TestResearchState:
    """Тесты для ResearchState"""

    def test_research_state_initialization(self):
        """Тест создания базового состояния"""
        state = ResearchState(
            task_id="test_001",
            task_type=ResearchTaskType.DATASET_DESIGN,
            complexity=ResearchComplexity.STANDARD,
            research_question="Test research question",
        )

        assert state.task_id == "test_001"
        assert state.task_type == ResearchTaskType.DATASET_DESIGN
        assert state.complexity == ResearchComplexity.STANDARD
        assert state.current_phase == ResearchPhase.INITIALIZATION
        assert len(state.artifacts) == 0
        assert len(state.findings) == 0

    def test_research_artifact_creation(self):
        """Тест создания артефакта"""
        artifact = ResearchArtifact(
            artifact_type="dataset_design",
            title="Test Dataset",
            description="Test description",
            content={"schema": "test"},
            created_by="Data Scientist",
        )

        assert artifact.artifact_type == "dataset_design"
        assert artifact.title == "Test Dataset"
        assert artifact.validated is False
        assert artifact.validation_score is None

    def test_research_finding_creation(self):
        """Тест создания научной находки"""
        finding = ResearchFinding(
            finding_id="finding_001",
            title="Test Finding",
            description="Test description",
            evidence=["Evidence 1", "Evidence 2"],
            confidence=0.85,
            implications=["Implication 1"],
            recommendations=["Recommendation 1"],
            discovered_by="ML Researcher",
        )

        assert finding.finding_id == "finding_001"
        assert finding.confidence == 0.85
        assert len(finding.evidence) == 2


class TestResearchAgentBase:
    """Тесты для базового класса ResearchAgent"""

    @pytest.fixture
    def mock_llm_provider(self):
        """Mock LLM provider"""
        provider = Mock(spec=LLMProvider)
        provider.generate = AsyncMock(return_value={"content": "Test response"})
        return provider

    @pytest.fixture
    def mock_memory_manager(self):
        """Mock Memory manager"""
        manager = Mock(spec=MemoryManager)
        manager.search_semantic = AsyncMock(return_value=[])
        return manager

    @pytest.mark.asyncio
    async def test_research_agent_initialization(self, mock_llm_provider, mock_memory_manager):
        """Тест инициализации агента"""
        agent = ChiefScientist(mock_llm_provider, mock_memory_manager)

        assert agent.agent_name == "Chief Scientist"
        assert agent.role == "Главный ученый и координатор научных исследований"
        assert len(agent.expertise) > 0
        assert len(agent.research_methods) > 0

    @pytest.mark.asyncio
    async def test_query_knowledge_base(self, mock_llm_provider, mock_memory_manager):
        """Тест запроса к базе знаний"""
        agent = ChiefScientist(mock_llm_provider, mock_memory_manager)

        mock_memory_manager.search_semantic = AsyncMock(
            return_value=[{"text": "Test knowledge"}]
        )

        results = await agent.query_knowledge_base("test query")

        assert len(results) == 1
        assert results[0]["text"] == "Test knowledge"
        mock_memory_manager.search_semantic.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_artifact(self, mock_llm_provider, mock_memory_manager):
        """Тест создания артефакта агентом"""
        agent = ChiefScientist(mock_llm_provider, mock_memory_manager)

        state = ResearchState(
            task_id="test_001",
            task_type=ResearchTaskType.FUNDAMENTAL_RESEARCH,
            complexity=ResearchComplexity.STANDARD,
            research_question="Test question",
        )

        artifact = await agent.create_artifact(
            state=state,
            artifact_type="test_artifact",
            title="Test Artifact",
            description="Test description",
            content={"data": "test"},
        )

        assert artifact.artifact_type == "test_artifact"
        assert artifact.title == "Test Artifact"
        assert artifact.created_by == "Chief Scientist"
        assert artifact.validated is False

    @pytest.mark.asyncio
    async def test_store_finding(self, mock_llm_provider, mock_memory_manager):
        """Тест сохранения научной находки"""
        agent = ChiefScientist(mock_llm_provider, mock_memory_manager)

        state = ResearchState(
            task_id="test_001",
            task_type=ResearchTaskType.FUNDAMENTAL_RESEARCH,
            complexity=ResearchComplexity.STANDARD,
            research_question="Test question",
        )

        finding = await agent.store_finding(
            state=state,
            title="Test Finding",
            description="Test description",
            evidence=["Evidence 1"],
            confidence=0.9,
            implications=["Implication 1"],
            recommendations=["Recommendation 1"],
        )

        assert finding.title == "Test Finding"
        assert finding.confidence == 0.9
        assert finding.discovered_by == "Chief Scientist"


class TestResearchCritic:
    """Тесты для базового класса ResearchCritic"""

    @pytest.fixture
    def mock_llm_provider(self):
        provider = Mock(spec=LLMProvider)
        provider.generate = AsyncMock(
            return_value={"content": "Quality: 8/10\nVerdict: APPROVED"}
        )
        return provider

    @pytest.fixture
    def mock_memory_manager(self):
        return Mock(spec=MemoryManager)

    @pytest.mark.asyncio
    async def test_critic_initialization(self, mock_llm_provider, mock_memory_manager):
        """Тест инициализации критика"""
        critic = ChiefScientistCritic(mock_llm_provider, mock_memory_manager)

        assert critic.critic_name == "Chief Scientist Critic"
        assert len(critic.review_focus) > 0
        assert len(critic.quality_criteria) > 0

    @pytest.mark.asyncio
    async def test_generate_review(self, mock_llm_provider, mock_memory_manager):
        """Тест генерации рецензии"""
        critic = ChiefScientistCritic(mock_llm_provider, mock_memory_manager)

        review = await critic.generate_review(
            content="Test research content",
            focus_areas=["Methodology", "Validity"],
        )

        assert "review_text" in review
        assert "reviewer" in review
        assert review["reviewer"] == "Chief Scientist Critic"
        mock_llm_provider.generate.assert_called_once()


class TestResearchTaskTypes:
    """Тесты для типов задач и сложности"""

    def test_all_task_types_available(self):
        """Проверка доступности всех типов задач"""
        task_types = [
            ResearchTaskType.FUNDAMENTAL_RESEARCH,
            ResearchTaskType.DATASET_DESIGN,
            ResearchTaskType.MODEL_ARCHITECTURE,
            ResearchTaskType.CURRICULUM_DESIGN,
            ResearchTaskType.LEARNING_ANALYTICS,
            ResearchTaskType.A_B_TESTING,
        ]

        for task_type in task_types:
            assert isinstance(task_type, ResearchTaskType)

    def test_all_complexity_levels_available(self):
        """Проверка доступности всех уровней сложности"""
        complexity_levels = [
            ResearchComplexity.EXPLORATORY,
            ResearchComplexity.STANDARD,
            ResearchComplexity.COMPLEX,
            ResearchComplexity.CRITICAL,
        ]

        for complexity in complexity_levels:
            assert isinstance(complexity, ResearchComplexity)

    def test_all_research_phases_available(self):
        """Проверка доступности всех фаз исследования"""
        phases = [
            ResearchPhase.INITIALIZATION,
            ResearchPhase.LITERATURE_REVIEW,
            ResearchPhase.METHODOLOGY_DESIGN,
            ResearchPhase.DATA_PREPARATION,
            ResearchPhase.IMPLEMENTATION,
            ResearchPhase.EXPERIMENTATION,
            ResearchPhase.ANALYSIS,
            ResearchPhase.VALIDATION,
            ResearchPhase.DOCUMENTATION,
            ResearchPhase.DELIVERY,
        ]

        for phase in phases:
            assert isinstance(phase, ResearchPhase)


@pytest.mark.integration
class TestResearchTeamIntegration:
    """Интеграционные тесты (требуют LLM и memory backends)"""

    @pytest.mark.skip(reason="Requires real LLM and memory backends")
    @pytest.mark.asyncio
    async def test_full_research_workflow(self):
        """Тест полного workflow исследования"""
        # TODO: Implement with real backends
        pass

    @pytest.mark.skip(reason="Requires real LLM")
    @pytest.mark.asyncio
    async def test_chief_scientist_conduct_research(self):
        """Тест работы Chief Scientist с реальным LLM"""
        # TODO: Implement with real LLM
        pass
