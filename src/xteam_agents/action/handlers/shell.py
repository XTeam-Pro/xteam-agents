"""Shell command handler."""

import asyncio
import time

import structlog

from xteam_agents.action.handlers.base import ActionHandler
from xteam_agents.models.action import (
    ActionRequest,
    ActionResult,
    Capability,
    HandlerType,
)

logger = structlog.get_logger()


class ShellHandler(ActionHandler):
    """
    Executes shell commands.

    Supports command execution with timeout and working directory.
    Commands are executed through a shell for flexibility.
    """

    # Commands that are blocked for security
    BLOCKED_COMMANDS = {
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=/dev/zero",
        ":(){:|:&};:",  # Fork bomb
    }

    def __init__(self, default_timeout: int = 60, allowed_commands: list[str] | None = None):
        self.default_timeout = default_timeout
        self.allowed_commands = allowed_commands

    def can_handle(self, capability: Capability) -> bool:
        """Check if this handler can execute the capability."""
        return capability.handler_type == HandlerType.SHELL

    async def validate_request(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> tuple[bool, str | None]:
        """Validate shell command request."""
        command = request.parameters.get("command")
        if not command:
            return False, "Command parameter is required"

        # Check for blocked commands
        command_lower = command.lower().strip()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command_lower:
                return False, f"Command blocked for security reasons: {blocked}"

        # Check against allowlist if configured
        if self.allowed_commands:
            base_command = command.split()[0] if command.split() else ""
            if base_command not in self.allowed_commands:
                return False, f"Command not in allowlist: {base_command}"

        return True, None

    async def execute(
        self,
        request: ActionRequest,
        capability: Capability,
    ) -> ActionResult:
        """Execute shell command."""
        start_time = time.time()

        command = request.parameters.get("command", "")
        cwd = request.parameters.get("cwd")
        env = request.parameters.get("env", {})
        timeout = request.timeout_seconds or capability.timeout_seconds or self.default_timeout

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env if env else None,
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
                    error=f"Command timed out after {timeout} seconds",
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

        except Exception as e:
            logger.error(
                "shell_execution_error",
                error=str(e),
                command=command[:100],  # Truncate for logging
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
