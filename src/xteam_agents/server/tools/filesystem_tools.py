"""MCP filesystem tools."""

from typing import Any
import os
import shutil
from pathlib import Path
from fastmcp import FastMCP

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from xteam_agents.orchestrator import TaskOrchestrator

WORKSPACE_ROOT = Path("/app/workspace")

def _validate_path(path_str: str) -> Path:
    """Validate that path is within workspace."""
    # Resolve to absolute path
    path = (WORKSPACE_ROOT / path_str).resolve()
    
    # Check if it starts with workspace root
    if not str(path).startswith(str(WORKSPACE_ROOT.resolve())):
        raise ValueError(f"Access denied. Path must be within {WORKSPACE_ROOT}")
    
    return path

def register_filesystem_tools(mcp: FastMCP, orchestrator: "TaskOrchestrator") -> None:
    """Register filesystem tools with the MCP server."""

    @mcp.tool()
    async def list_directory(path: str = ".") -> dict[str, Any]:
        """
        List files and directories in the workspace.
        
        Args:
            path: Relative path to list (default: root workspace).
            
        Returns:
            Dictionary with list of entries.
        """
        try:
            target_path = _validate_path(path)
            
            if not target_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            if not target_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            entries = []
            for entry in os.scandir(target_path):
                entries.append({
                    "name": entry.name,
                    "type": "directory" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else None,
                })
                
            return {
                "path": path,
                "entries": sorted(entries, key=lambda x: (x["type"] != "directory", x["name"])),
                "total": len(entries)
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def read_file(path: str) -> dict[str, Any]:
        """
        Read content of a file.
        
        Args:
            path: Relative path to file.
            
        Returns:
            Dictionary with file content.
        """
        try:
            target_path = _validate_path(path)
            
            if not target_path.exists():
                return {"error": f"File does not exist: {path}"}
            
            if not target_path.is_file():
                return {"error": f"Path is not a file: {path}"}
                
            # Check size (limit to 1MB for safety)
            if target_path.stat().st_size > 1024 * 1024:
                return {"error": "File too large (>1MB)."}
                
            content = target_path.read_text(encoding="utf-8")
            return {
                "path": path,
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    async def write_file(path: str, content: str) -> dict[str, Any]:
        """
        Write content to a file (overwrites).
        
        Args:
            path: Relative path to file.
            content: Content to write.
            
        Returns:
            Success message.
        """
        try:
            target_path = _validate_path(path)
            
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            target_path.write_text(content, encoding="utf-8")
            
            return {
                "path": path,
                "status": "success",
                "size": len(content)
            }
        except Exception as e:
            return {"error": str(e)}
