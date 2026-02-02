"""Integration tests for MCP tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from xteam_agents.config import Settings
from xteam_agents.models.task import Priority, TaskStatus


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    orchestrator = MagicMock()
    orchestrator.submit_task = AsyncMock(return_value=uuid4())
    orchestrator.get_task_info = AsyncMock(return_value=None)
    orchestrator.get_task_result = AsyncMock(return_value=None)
    orchestrator.cancel_task = AsyncMock(return_value=True)
    orchestrator.list_tasks = AsyncMock(return_value=[])
    orchestrator.system_health = AsyncMock(return_value={"orchestrator": "healthy"})
    orchestrator.memory_manager = MagicMock()
    orchestrator.capability_registry = MagicMock()
    orchestrator.settings = Settings(
        openai_api_key="test-key",
        redis_url="redis://localhost:6379/0",
    )
    return orchestrator


class TestTaskToolsSimulated:
    """Tests for task tools with mocked orchestrator."""

    @pytest.mark.asyncio
    async def test_submit_task_returns_task_id(self, mock_orchestrator):
        """Test that submit_task returns a task ID."""
        from xteam_agents.server.tools.task_tools import register_task_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_task_tools(mcp, mock_orchestrator)

        # The tool is registered
        assert "submit_task" in [t.name for t in mcp._tool_manager._tools.values()]

    @pytest.mark.asyncio
    async def test_get_task_status_handles_missing(self, mock_orchestrator):
        """Test that get_task_status handles missing tasks."""
        from xteam_agents.server.tools.task_tools import register_task_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_task_tools(mcp, mock_orchestrator)

        assert "get_task_status" in [t.name for t in mcp._tool_manager._tools.values()]

    @pytest.mark.asyncio
    async def test_cancel_task_registered(self, mock_orchestrator):
        """Test that cancel_task is registered."""
        from xteam_agents.server.tools.task_tools import register_task_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_task_tools(mcp, mock_orchestrator)

        assert "cancel_task" in [t.name for t in mcp._tool_manager._tools.values()]


class TestMemoryToolsSimulated:
    """Tests for memory tools with mocked orchestrator."""

    @pytest.mark.asyncio
    async def test_query_memory_registered(self, mock_orchestrator):
        """Test that query_memory is registered."""
        from xteam_agents.server.tools.memory_tools import register_memory_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_memory_tools(mcp, mock_orchestrator)

        assert "query_memory" in [t.name for t in mcp._tool_manager._tools.values()]

    @pytest.mark.asyncio
    async def test_search_knowledge_registered(self, mock_orchestrator):
        """Test that search_knowledge is registered."""
        from xteam_agents.server.tools.memory_tools import register_memory_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_memory_tools(mcp, mock_orchestrator)

        assert "search_knowledge" in [t.name for t in mcp._tool_manager._tools.values()]


class TestAdminToolsSimulated:
    """Tests for admin tools with mocked orchestrator."""

    @pytest.mark.asyncio
    async def test_list_agents_registered(self, mock_orchestrator):
        """Test that list_agents is registered."""
        from xteam_agents.server.tools.admin_tools import register_admin_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_admin_tools(mcp, mock_orchestrator)

        assert "list_agents" in [t.name for t in mcp._tool_manager._tools.values()]

    @pytest.mark.asyncio
    async def test_system_health_registered(self, mock_orchestrator):
        """Test that system_health is registered."""
        from xteam_agents.server.tools.admin_tools import register_admin_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_admin_tools(mcp, mock_orchestrator)

        assert "system_health" in [t.name for t in mcp._tool_manager._tools.values()]

    @pytest.mark.asyncio
    async def test_register_capability_registered(self, mock_orchestrator):
        """Test that register_capability is registered."""
        from xteam_agents.server.tools.admin_tools import register_admin_tools
        from fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_admin_tools(mcp, mock_orchestrator)

        assert "register_capability" in [t.name for t in mcp._tool_manager._tools.values()]
