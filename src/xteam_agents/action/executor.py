"""Action executor with capability enforcement."""

import structlog

from xteam_agents.action.handlers.base import ActionHandler
from xteam_agents.action.handlers.ci import CIHandler
from xteam_agents.action.handlers.code import CodeHandler
from xteam_agents.action.handlers.http import HTTPHandler
from xteam_agents.action.handlers.shell import ShellHandler
from xteam_agents.action.registry import CapabilityRegistry
from xteam_agents.config import Settings
from xteam_agents.models.action import ActionRequest, ActionResult, HandlerType

logger = structlog.get_logger()


class ActionExecutor:
    """
    Executes actions through registered capabilities.

    Security Boundaries:
    1. Only registered capabilities can be executed
    2. Handlers validate requests before execution
    3. Timeouts are enforced on all actions
    4. Audit logging for all executions
    """

    def __init__(self, settings: Settings, registry: CapabilityRegistry | None = None):
        self.settings = settings
        self.registry = registry or CapabilityRegistry()
        self._handlers: dict[HandlerType, ActionHandler] = {}
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup action handlers."""
        # Code execution handler
        self._handlers[HandlerType.CODE] = CodeHandler(
            sandbox_enabled=True,
            default_timeout=30,
        )

        # HTTP handler
        self._handlers[HandlerType.HTTP] = HTTPHandler(default_timeout=30)

        # Shell handler
        self._handlers[HandlerType.SHELL] = ShellHandler(default_timeout=60)

        # CI/n8n handler
        self._handlers[HandlerType.CI] = CIHandler(
            n8n_url=self.settings.n8n_url,
            n8n_api_key=(
                self.settings.n8n_api_key.get_secret_value()
                if self.settings.n8n_api_key
                else None
            ),
            default_timeout=120,
        )

    def get_handler(self, handler_type: HandlerType) -> ActionHandler | None:
        """Get handler for a handler type."""
        return self._handlers.get(handler_type)

    async def execute(self, request: ActionRequest) -> ActionResult:
        """
        Execute an action request.

        Args:
            request: The action request to execute

        Returns:
            Result of the action execution
        """
        # Get the capability
        capability = self.registry.get(request.capability_name)
        if capability is None:
            logger.warning(
                "capability_not_found",
                capability_name=request.capability_name,
                task_id=str(request.task_id),
            )
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=request.capability_name,
                success=False,
                error=f"Capability not found: {request.capability_name}",
                duration_seconds=0,
            )

        # Check if capability is enabled
        if not capability.enabled:
            logger.warning(
                "capability_disabled",
                capability_name=capability.name,
                task_id=str(request.task_id),
            )
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error=f"Capability is disabled: {capability.name}",
                duration_seconds=0,
            )

        # Get the handler
        handler = self._handlers.get(capability.handler_type)
        if handler is None:
            logger.error(
                "handler_not_found",
                handler_type=capability.handler_type.value,
                task_id=str(request.task_id),
            )
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error=f"Handler not found for type: {capability.handler_type.value}",
                duration_seconds=0,
            )

        # Validate the request
        is_valid, error_message = await handler.validate_request(request, capability)
        if not is_valid:
            logger.warning(
                "request_validation_failed",
                capability_name=capability.name,
                error=error_message,
                task_id=str(request.task_id),
            )
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error=error_message or "Request validation failed",
                duration_seconds=0,
            )

        # Execute the action
        logger.info(
            "action_executing",
            capability_name=capability.name,
            handler_type=capability.handler_type.value,
            task_id=str(request.task_id),
        )

        result = await handler.execute(request, capability)

        # Log result
        log_level = "info" if result.success else "warning"
        getattr(logger, log_level)(
            "action_completed",
            capability_name=capability.name,
            success=result.success,
            duration_seconds=result.duration_seconds,
            task_id=str(request.task_id),
        )

        return result

    async def execute_batch(
        self, requests: list[ActionRequest]
    ) -> list[ActionResult]:
        """
        Execute multiple action requests.

        Requests are executed sequentially to maintain ordering.

        Args:
            requests: List of action requests to execute

        Returns:
            List of results in the same order as requests
        """
        results: list[ActionResult] = []
        for request in requests:
            result = await self.execute(request)
            results.append(result)
        return results
