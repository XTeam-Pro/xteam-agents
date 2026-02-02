"""Capability registry for managing available actions."""

from typing import Any
from uuid import UUID

import structlog

from xteam_agents.models.action import Capability, HandlerType

logger = structlog.get_logger()


class CapabilityRegistry:
    """
    Registry for managing action capabilities.

    Capabilities must be registered before they can be executed.
    This provides a security boundary - only registered capabilities
    can be invoked by agents.
    """

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}
        self._setup_default_capabilities()

    def _setup_default_capabilities(self) -> None:
        """Setup default capabilities."""
        # Code execution
        self.register(
            Capability(
                name="execute_python",
                description="Execute Python code in a sandboxed environment",
                handler_type=HandlerType.CODE,
                config={"sandbox": True},
                timeout_seconds=30,
            )
        )

        # HTTP requests
        self.register(
            Capability(
                name="http_get",
                description="Make HTTP GET requests",
                handler_type=HandlerType.HTTP,
                config={"method": "GET"},
                timeout_seconds=30,
            )
        )

        self.register(
            Capability(
                name="http_post",
                description="Make HTTP POST requests",
                handler_type=HandlerType.HTTP,
                config={"method": "POST"},
                timeout_seconds=30,
            )
        )

        # Shell commands (restricted)
        self.register(
            Capability(
                name="shell_execute",
                description="Execute shell commands",
                handler_type=HandlerType.SHELL,
                requires_approval=True,
                timeout_seconds=60,
            )
        )

        # CI/CD integration
        self.register(
            Capability(
                name="trigger_workflow",
                description="Trigger a CI/CD workflow",
                handler_type=HandlerType.CI,
                config={"action": "trigger"},
                timeout_seconds=120,
            )
        )

        self.register(
            Capability(
                name="check_workflow_status",
                description="Check status of a CI/CD workflow execution",
                handler_type=HandlerType.CI,
                config={"action": "status"},
                timeout_seconds=30,
            )
        )

    def register(self, capability: Capability) -> Capability:
        """
        Register a new capability.

        Args:
            capability: The capability to register

        Returns:
            The registered capability

        Raises:
            ValueError: If capability with same name already exists
        """
        if capability.name in self._capabilities:
            logger.warning(
                "capability_overwrite",
                name=capability.name,
            )

        self._capabilities[capability.name] = capability
        logger.info(
            "capability_registered",
            name=capability.name,
            handler_type=capability.handler_type.value,
        )

        return capability

    def unregister(self, name: str) -> bool:
        """
        Unregister a capability.

        Args:
            name: Name of the capability to unregister

        Returns:
            True if capability was unregistered, False if not found
        """
        if name in self._capabilities:
            del self._capabilities[name]
            logger.info("capability_unregistered", name=name)
            return True
        return False

    def get(self, name: str) -> Capability | None:
        """
        Get a capability by name.

        Args:
            name: Name of the capability

        Returns:
            The capability if found, None otherwise
        """
        return self._capabilities.get(name)

    def get_by_id(self, capability_id: UUID) -> Capability | None:
        """
        Get a capability by ID.

        Args:
            capability_id: UUID of the capability

        Returns:
            The capability if found, None otherwise
        """
        for capability in self._capabilities.values():
            if capability.id == capability_id:
                return capability
        return None

    def list_capabilities(self) -> list[Capability]:
        """
        List all registered capabilities.

        Returns:
            List of all capabilities
        """
        return list(self._capabilities.values())

    def list_by_type(self, handler_type: HandlerType) -> list[Capability]:
        """
        List capabilities by handler type.

        Args:
            handler_type: The handler type to filter by

        Returns:
            List of capabilities with the specified handler type
        """
        return [
            c for c in self._capabilities.values()
            if c.handler_type == handler_type
        ]

    def list_enabled(self) -> list[Capability]:
        """
        List only enabled capabilities.

        Returns:
            List of enabled capabilities
        """
        return [c for c in self._capabilities.values() if c.enabled]

    def enable(self, name: str) -> bool:
        """Enable a capability."""
        capability = self._capabilities.get(name)
        if capability:
            self._capabilities[name] = capability.model_copy(update={"enabled": True})
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a capability."""
        capability = self._capabilities.get(name)
        if capability:
            self._capabilities[name] = capability.model_copy(update={"enabled": False})
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """
        Export registry as dictionary.

        Returns:
            Dictionary representation of all capabilities
        """
        return {
            name: cap.model_dump(mode="json")
            for name, cap in self._capabilities.items()
        }
