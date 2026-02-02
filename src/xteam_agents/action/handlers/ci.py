"""CI/n8n integration handler."""

import time

import httpx
import structlog

from xteam_agents.action.handlers.base import ActionHandler
from xteam_agents.models.action import (
    ActionRequest,
    ActionResult,
    Capability,
    HandlerType,
)

logger = structlog.get_logger()


class CIHandler(ActionHandler):
    """
    Handles CI/CD and n8n workflow integrations.

    Supports triggering workflows, checking status, and
    receiving webhook events.
    """

    def __init__(
        self,
        n8n_url: str | None = None,
        n8n_api_key: str | None = None,
        default_timeout: int = 120,
    ):
        self.n8n_url = n8n_url
        self.n8n_api_key = n8n_api_key
        self.default_timeout = default_timeout

    def can_handle(self, capability: Capability) -> bool:
        """Check if this handler can execute the capability."""
        return capability.handler_type == HandlerType.CI

    async def validate_request(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> tuple[bool, str | None]:
        """Validate CI request."""
        action = request.parameters.get("action")
        if not action:
            return False, "Action parameter is required (trigger, status, webhook)"

        if action not in ["trigger", "status", "webhook"]:
            return False, f"Invalid action: {action}"

        if action == "trigger":
            if not request.parameters.get("workflow_id"):
                return False, "workflow_id required for trigger action"

        if action == "status":
            if not request.parameters.get("execution_id"):
                return False, "execution_id required for status action"

        return True, None

    async def execute(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> ActionResult:
        """Execute CI action."""
        start_time = time.time()

        action = request.parameters.get("action", "")
        timeout = request.timeout_seconds or capability.timeout_seconds or self.default_timeout

        try:
            if action == "trigger":
                return await self._trigger_workflow(request, capability, timeout, start_time)
            elif action == "status":
                return await self._check_status(request, capability, timeout, start_time)
            elif action == "webhook":
                return await self._send_webhook(request, capability, timeout, start_time)
            else:
                return ActionResult(
                    request_id=request.id,
                    task_id=request.task_id,
                    capability_name=capability.name,
                    success=False,
                    error=f"Unknown action: {action}",
                    duration_seconds=time.time() - start_time,
                )

        except Exception as e:
            logger.error(
                "ci_handler_error",
                error=str(e),
                action=action,
                task_id=str(request.task_id),
            )
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def _trigger_workflow(
        self,
        request: ActionRequest,
        capability: Capability,
        timeout: int,
        start_time: float,
    ) -> ActionResult:
        """Trigger an n8n workflow."""
        if not self.n8n_url:
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error="n8n URL not configured",
                duration_seconds=time.time() - start_time,
            )

        workflow_id = request.parameters.get("workflow_id")
        payload = request.parameters.get("payload", {})

        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {}
            if self.n8n_api_key:
                headers["X-N8N-API-KEY"] = self.n8n_api_key

            # Trigger via webhook (common pattern)
            url = f"{self.n8n_url}/webhook/{workflow_id}"

            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )

            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=response.is_success,
                output=response.text,
                duration_seconds=time.time() - start_time,
                status_code=response.status_code,
                response_body=response.text,
            )

    async def _check_status(
        self,
        request: ActionRequest,
        capability: Capability,
        timeout: int,
        start_time: float,
    ) -> ActionResult:
        """Check workflow execution status."""
        if not self.n8n_url:
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error="n8n URL not configured",
                duration_seconds=time.time() - start_time,
            )

        execution_id = request.parameters.get("execution_id")

        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {}
            if self.n8n_api_key:
                headers["X-N8N-API-KEY"] = self.n8n_api_key

            url = f"{self.n8n_url}/api/v1/executions/{execution_id}"

            response = await client.get(url, headers=headers)

            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=response.is_success,
                output=response.text,
                duration_seconds=time.time() - start_time,
                status_code=response.status_code,
                response_body=response.text,
            )

    async def _send_webhook(
        self,
        request: ActionRequest,
        capability: Capability,
        timeout: int,
        start_time: float,
    ) -> ActionResult:
        """Send a webhook notification."""
        webhook_url = request.parameters.get("url")
        if not webhook_url:
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error="Webhook URL required",
                duration_seconds=time.time() - start_time,
            )

        payload = request.parameters.get("payload", {})
        headers = request.parameters.get("headers", {})

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers,
            )

            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=response.is_success,
                output=response.text,
                duration_seconds=time.time() - start_time,
                status_code=response.status_code,
                response_body=response.text,
            )
