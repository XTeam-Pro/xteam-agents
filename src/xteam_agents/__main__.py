"""Entry point for XTeam Agents MCP server."""

import asyncio
import sys

import structlog

from xteam_agents.config import LogLevel, get_settings
from xteam_agents.server.app import create_mcp_server


def configure_logging(log_level: LogLevel, log_json: bool) -> None:
    """Configure structured logging."""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set log level
    import logging

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.value),
        stream=sys.stdout,
    )


def main() -> None:
    """Main entry point."""
    settings = get_settings()

    # Configure logging
    configure_logging(settings.log_level, settings.log_json)

    logger = structlog.get_logger()
    logger.info(
        "xteam_agents_starting",
        llm_provider=settings.llm_provider.value,
        llm_model=settings.llm_model,
        port=settings.server_port,
    )

    # Create the MCP server
    mcp = create_mcp_server(settings)

    # Run the server
    try:
        mcp.run(
            transport="stdio",
        )
    except KeyboardInterrupt:
        logger.info("xteam_agents_interrupted")
    except Exception as e:
        logger.error("xteam_agents_error", error=str(e))
        sys.exit(1)


def run_http_server() -> None:
    """Run the server with HTTP transport (for development)."""
    import uvicorn

    settings = get_settings()

    # Configure logging
    configure_logging(settings.log_level, settings.log_json)

    logger = structlog.get_logger()
    logger.info(
        "xteam_agents_starting_http",
        host=settings.server_host,
        port=settings.server_port,
    )

    # Create the MCP server
    mcp = create_mcp_server(settings)

    # Note: FastMCP might not have get_asgi_app in all versions or it might be named differently.
    # If using fastmcp 0.2.0+, it usually runs itself.
    # However, for Docker we want to bind to 0.0.0.0.
    
    # If mcp has a run method that supports http, use that.
    # Otherwise check for asgi app.
    
    # For now, let's assume mcp object is a FastMCP instance.
    # If get_asgi_app is missing, we might need to use mcp._fastapi_app or similar if available,
    # or just use mcp.run(transport='sse') if supported.
    
    # Let's try to find the ASGI app
    if hasattr(mcp, "get_asgi_app"):
        app = mcp.get_asgi_app()
    elif hasattr(mcp, "_fastapi_app"):
        app = mcp._fastapi_app
    else:
        # Fallback or try to construct it if FastMCP structure is different
        # In some versions, FastMCP IS the app or has a mount method.
        # But let's check if we can just use mcp.run with sse transport which usually starts uvicorn.
        logger.info("using_mcp_run_sse")
        mcp.run(transport="sse", host=settings.server_host, port=settings.server_port)
        return

    # Run with uvicorn
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.value.lower(),
    )


if __name__ == "__main__":
    # Check for --http flag
    if "--http" in sys.argv:
        run_http_server()
    else:
        main()
