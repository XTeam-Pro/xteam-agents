"""Base action handler interface."""

from abc import ABC, abstractmethod

from xteam_agents.models.action import ActionRequest, ActionResult, Capability


class ActionHandler(ABC):
    """
    Abstract base class for action handlers.

    Action handlers execute specific types of actions
    (code, HTTP, shell, CI/CD).
    """

    @abstractmethod
    async def execute(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> ActionResult:
        """
        Execute an action.

        Args:
            request: The action request
            capability: The capability configuration

        Returns:
            Result of the action execution
        """
        pass

    @abstractmethod
    def can_handle(self, capability: Capability) -> bool:
        """
        Check if this handler can execute the given capability.

        Args:
            capability: The capability to check

        Returns:
            True if this handler can execute the capability
        """
        pass

    async def validate_request(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> tuple[bool, str | None]:
        """
        Validate a request before execution.

        Args:
            request: The action request
            capability: The capability configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None
