"""MCP code execution tools (Sandboxed)."""

import os
from pathlib import Path
from typing import Any
import structlog
import docker
from docker.errors import ContainerError, ImageNotFound, APIError
from fastmcp import FastMCP

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from xteam_agents.orchestrator import TaskOrchestrator

logger = structlog.get_logger()

def register_code_tools(mcp: FastMCP, orchestrator: "TaskOrchestrator") -> None:
    """Register code execution tools with the MCP server."""

    @mcp.tool()
    async def index_repository(
        path: str = ".",
    ) -> dict[str, Any]:
        """
        Index a local repository into Qdrant for semantic search.
        
        Scans all files in the workspace path and creates embeddings.
        
        Args:
            path: Relative path to index.
            
        Returns:
            Indexing statistics.
        """
        try:
            from xteam_agents.server.tools.filesystem_tools import _validate_path
            target_path = _validate_path(path)
            
            if not target_path.exists():
                 return {"error": "Path does not exist"}
                 
            # Scan files
            # Limit to common code extensions
            extensions = {'.py', '.js', '.ts', '.md', '.json', '.yml', '.yaml', '.txt', '.html', '.css'}
            files_indexed = 0
            
            # We need to access memory manager to add knowledge
            # Since orchestrator has memory_manager
            if not orchestrator.memory_manager:
                return {"error": "Memory manager not initialized"}
                
            from xteam_agents.models.memory import MemoryScope, MemoryType
            
            # Walk directory
            for root, _, files in os.walk(target_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix in extensions:
                        try:
                            content = file_path.read_text(encoding='utf-8')
                            if not content.strip():
                                continue
                                
                            # Create knowledge entry
                            # We use a special prefix for code knowledge
                            rel_path = file_path.relative_to(target_path)
                            
                            # Add to semantic memory
                            await orchestrator.memory_manager.add_memory(
                                content=f"File: {rel_path}\n\n{content}",
                                scope=MemoryScope.PROJECT,
                                type=MemoryType.SEMANTIC,
                                metadata={
                                    "source": "codebase",
                                    "file_path": str(rel_path),
                                    "language": file_path.suffix[1:]
                                }
                            )
                            files_indexed += 1
                        except Exception as e:
                            logger.warning("index_file_failed", file=str(file_path), error=str(e))
                            
            return {
                "status": "success",
                "files_indexed": files_indexed,
                "path": str(path)
            }
            
        except Exception as e:
            return {"error": str(e)}
    @mcp.tool()
    async def execute_python(
        code: str,
        timeout_seconds: int = 30,
        install_packages: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute Python code in a sandboxed Docker container.
        
        The code runs in an isolated `python:3.11-slim` container.
        Network access is disabled by default for security.
        
        Args:
            code: The Python code to execute.
            timeout_seconds: Maximum execution time (default 30s).
            install_packages: List of pip packages to install before running (requires network).
            
        Returns:
            Dictionary with stdout, stderr, and exit_code.
        """
        try:
            client = docker.from_env()
        except Exception as e:
            return {"error": f"Failed to connect to Docker: {str(e)}"}

        container = None
        try:
            # Prepare command
            # If packages need to be installed, we need a shell script
            if install_packages:
                # If installing packages, we MUST enable network
                network_disabled = False
                pip_install = f"pip install {' '.join(install_packages)}"
                # We need to escape the code for shell
                # But a safer way is to write it to a file using printf or cat
                # Here we will try a multi-step command
                # Note: This is a bit fragile with complex code. 
                # A robust implementation would use a custom image or volume mount.
                # For this MVP, we'll try to execute directly.
                
                # Limitation: For complex dependencies, we should probably have a pre-built image
                # or use a longer running container.
                return {"error": "Dynamic package installation not yet supported in safe mode."}
            else:
                network_disabled = True
            
            logger.info("executing_code_sandbox", timeout=timeout_seconds)
            
            # Run container
            # We use python -c with the code directly. 
            # Note: Docker SDK handles argument escaping.
            container = client.containers.run(
                "python:3.11-slim",
                command=["python", "-c", code],
                mem_limit="512m",
                network_disabled=network_disabled,
                detach=True,
                remove=False, # We need to read logs then remove
                # Stop the container if it runs too long
            )
            
            try:
                result = container.wait(timeout=timeout_seconds)
                exit_code = result.get('StatusCode', -1)
                
                logs = container.logs(stdout=True, stderr=True)
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
                
                return {
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "status": "success" if exit_code == 0 else "failed"
                }
                
            except Exception as e:
                # Timeout or other error during wait
                container.kill()
                return {"error": f"Execution timed out or failed: {str(e)}"}
                
        except ImageNotFound:
             return {"error": "Docker image 'python:3.11-slim' not found. Please pull it first."}
        except APIError as e:
            return {"error": f"Docker API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
