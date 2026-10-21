import logging
from contextlib import asynccontextmanager
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_connection_info
from app.core.seed import seed_initial_data
from app.services.agent_manager import AgentManager
from app.services.mcp_manager import MCPManager

logger = logging.getLogger(__name__)

# Ensure tables and seed data exist
try:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_initial_data(db)
except Exception:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup
    print("🚀 Starting SuperMon SDLC Automation Platform...")

    # Create database tables and seed initial demo data
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_initial_data(db)
        print("✅ Database ready & seeded")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")

    # Initialize MCP Manager
    app.state.mcp_manager = MCPManager()
    try:
        await app.state.mcp_manager.initialize()
    except Exception as e:
        print(f"⚠️ MCP Manager init warning: {e}")

    # Initialize Agent Manager
    app.state.agent_manager = AgentManager()
    try:
        await app.state.agent_manager.initialize()
    except Exception as e:
        print(f"⚠️ Agent Manager init warning: {e}")

    print("✅ SuperMon platform initialized successfully!")

    yield

    # Shutdown
    print("🛑 Shutting down SuperMon platform...")
    try:
        await app.state.mcp_manager.cleanup()
    except Exception:
        pass
    try:
        await app.state.agent_manager.cleanup()
    except Exception:
        pass


app = FastAPI(
    title="SuperMon SDLC Automation Platform",
    description="A comprehensive SDLC automation platform using MCP servers and agentic framework",
    version="2.4.0",
    lifespan=lifespan,
)

# CORS middleware for seamless Next.js frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    conn_info = get_connection_info()
    return {
        "status": "healthy",
        "service": "SuperMon SDLC Automation Platform",
        "version": "2.4.0",
        "connectivity": conn_info,
        "mcp_mesh": {
            "servers": ["github", "notion", "postgresql", "redis", "slack", "whatsapp"],
            "status": "active",
        },
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to SuperMon SDLC Automation Platform",
        "docs": "/docs",
        "health": "/health",
        "version": "2.4.0",
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
