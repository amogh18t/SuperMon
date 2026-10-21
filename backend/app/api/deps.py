"""Shared dependencies for FastAPI endpoints."""

from fastapi import Request

from app.core.database import get_db
from app.services.agent_manager import AgentManager
from app.services.mcp_manager import MCPManager


def get_agent_manager(request: Request) -> AgentManager:
    """Retrieve initialized AgentManager from app.state."""
    manager = getattr(request.app.state, "agent_manager", None)
    if manager is None:
        manager = AgentManager()
    return manager


def get_mcp_manager(request: Request) -> MCPManager:
    """Retrieve initialized MCPManager from app.state."""
    manager = getattr(request.app.state, "mcp_manager", None)
    if manager is None:
        manager = MCPManager()
    return manager
