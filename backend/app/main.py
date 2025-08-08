from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Optional

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.services.agent_manager import AgentManager
from app.services.mcp_manager import MCPManager

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting SuperMon SDLC Automation Platform...")
    
    # Initialize MCP Manager
    app.state.mcp_manager = MCPManager()
    await app.state.mcp_manager.initialize()
    
    # Initialize Agent Manager
    app.state.agent_manager = AgentManager()
    await app.state.agent_manager.initialize()
    
    print("✅ SuperMon platform initialized successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down SuperMon platform...")
    await app.state.mcp_manager.cleanup()
    await app.state.agent_manager.cleanup()

app = FastAPI(
    title="SuperMon SDLC Automation Platform",
    description="A comprehensive SDLC automation platform using MCP servers and agentic framework",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SuperMon SDLC Automation Platform",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to SuperMon SDLC Automation Platform",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 