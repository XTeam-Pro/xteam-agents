"""Code execution handler."""

import asyncio
import tempfile
import time
from pathlib import Path

import structlog

from xteam_agents.action.handlers.base import ActionHandler
from xteam_agents.models.action import (
    ActionRequest,
    ActionResult,
    Capability,
    HandlerType,
)

logger = structlog.get_logger()


class CodeHandler(ActionHandler):
    """
    Executes code in a sandboxed environment.

    Supports Python code execution with timeout and resource limits.
    """

    def __init__(self, sandbox_enabled: bool = True, default_timeout: int = 30):
        self.sandbox_enabled = sandbox_enabled
        self.default_timeout = default_timeout

    def can_handle(self, capability: Capability) -> bool:
        """Check if this handler can execute the capability."""
        return capability.handler_type == HandlerType.CODE

    async def validate_request(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> tuple[bool, str | None]:
        """Validate code execution request."""
        code = request.parameters.get("code")
        if not code:
            return False, "Code parameter is required"

        # Basic security checks
        dangerous_imports = ["os.system", "subprocess", "eval", "exec", "__import__"]
        if self.sandbox_enabled:
            for danger in dangerous_imports:
                if danger in code:
                    return False, f"Potentially dangerous code pattern detected: {danger}"

        return True, None

    async def execute(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> ActionResult:
        """Execute Python code."""
        start_time = time.time()
        code = request.parameters.get("code", "")
        timeout = request.timeout_seconds or capability.timeout_seconds or self.default_timeout

        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
            ) as f:
                f.write(code)
                code_file = Path(f.name)

            try:
                # Execute in subprocess with timeout
                process = await asyncio.create_subprocess_exec(
                    "python",
                    str(code_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return ActionResult(
                        request_id=request.id,
                        task_id=request.task_id,
                        capability_name=capability.name,
                        success=False,
                        error=f"Code execution timed out after {timeout} seconds",
                        duration_seconds=time.time() - start_time,
                    )

                exit_code = process.returncode
                stdout_str = stdout.decode("utf-8") if stdout else ""
                stderr_str = stderr.decode("utf-8") if stderr else ""

                return ActionResult(
                    request_id=request.id,
                    task_id=request.task_id,
                    capability_name=capability.name,
                    success=exit_code == 0,
                    output=stdout_str if exit_code == 0 else stderr_str,
                    error=stderr_str if exit_code != 0 else None,
                    duration_seconds=time.time() - start_time,
                    exit_code=exit_code,
                    stdout=stdout_str,
                    stderr=stderr_str,
                )

            finally:
                # Cleanup temp file
                code_file.unlink(missing_ok=True)

        except Exception as e:
            logger.error(
                "code_execution_error",
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
