"""HTTP request handler."""

import time
from typing import Any

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


class HTTPHandler(ActionHandler):
    """
    Executes HTTP requests.

    Supports GET, POST, PUT, PATCH, DELETE methods with
    configurable headers, body, and timeout.
    """

    ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout

    def can_handle(self, capability: Capability) -> bool:
        """Check if this handler can execute the capability."""
        return capability.handler_type == HandlerType.HTTP

    async def validate_request(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> tuple[bool, str | None]:
        """Validate HTTP request."""
        url = request.parameters.get("url")
        if not url:
            return False, "URL parameter is required"

        method = request.parameters.get("method", "GET").upper()
        if method not in self.ALLOWED_METHODS:
            return False, f"Invalid HTTP method: {method}"

        # Check allowed contexts if specified
        if capability.allowed_contexts:
            # Could implement URL allowlist checking here
            pass

        return True, None

    async def execute(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> ActionResult:
        """Execute HTTP request."""
        start_time = time.time()

        url = request.parameters.get("url", "")
        method = request.parameters.get("method", "GET").upper()
        headers = request.parameters.get("headers", {})
        body = request.parameters.get("body")
        json_body = request.parameters.get("json")
        timeout = request.timeout_seconds or capability.timeout_seconds or self.default_timeout

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                kwargs: dict[str, Any] = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                }

                if json_body is not None:
                    kwargs["json"] = json_body
                elif body is not None:
                    kwargs["content"] = body

                response = await client.request(**kwargs)

                return ActionResult(
                    request_id=request.id,
                    task_id=request.task_id,
                    capability_name=capability.name,
                    success=response.is_success,
                    output=response.text,
                    duration_seconds=time.time() - start_time,
                    status_code=response.status_code,
                    response_body=response.text,
                    response_headers=dict(response.headers),
                )

        except httpx.TimeoutException:
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error=f"HTTP request timed out after {timeout} seconds",
                duration_seconds=time.time() - start_time,
            )

        except httpx.RequestError as e:
            logger.error(
                "http_request_error",
                error=str(e),
                url=url,
                task_id=str(request.task_id),
            )
            return ActionResult(
                request_id=request.id,
                task_id=request.task_id,
                capability_name=capability.name,
                success=False,
                error=f"HTTP request failed: {str(e)}",
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            logger.error(
                "http_handler_error",
                error=str(e),
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
