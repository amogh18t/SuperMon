"""Notion MCP Server for SuperMon platform."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from notion_client import AsyncClient as NotionClient

logger = logging.getLogger(__name__)


class NotionPage(BaseModel):
    """Notion page model."""
    title: str = Field(..., description="Page title")
    content: Optional[str] = Field(None, description="Page content")
    parent_id: Optional[str] = Field(None, description="Parent page/database ID")
    properties: Optional[Dict[str, Any]] = Field(None, description="Page properties")
    tags: Optional[List[str]] = Field(None, description="Page tags")


class NotionDatabase(BaseModel):
    """Notion database model."""
    title: str = Field(..., description="Database title")
    description: Optional[str] = Field(None, description="Database description")
    parent_id: Optional[str] = Field(None, description="Parent page ID")
    properties: Optional[Dict[str, Any]] = Field(None, description="Database properties")


class NotionBlock(BaseModel):
    """Notion block model."""
    type: str = Field(..., description="Block type")
    content: str = Field(..., description="Block content")
    properties: Optional[Dict[str, Any]] = Field(None, description="Block properties")


class NotionMCPResponse(BaseModel):
    """Standard MCP response model."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class NotionMCPServer:
    """Notion MCP Server implementation."""
    
    def __init__(self):
        """Initialize Notion MCP Server."""
        self.app = FastAPI(title="Notion MCP Server", version="1.0.0")
        self.client: Optional[NotionClient] = None
        self.api_key: Optional[str] = None
        self.databases_cache: Dict[str, Dict[str, Any]] = {}
        self.pages_cache: Dict[str, Dict[str, Any]] = {}
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize Notion client on startup."""
            await self._initialize_client()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown."""
            await self._cleanup()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "Notion MCP Server",
                "connected": self.client is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/create-page")
        async def create_page(page: NotionPage):
            """Create a new Notion page."""
            try:
                result = await self._create_page(page)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating page: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-database")
        async def create_database(database: NotionDatabase):
            """Create a new Notion database."""
            try:
                result = await self._create_database(database)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating database: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-page/{page_id}")
        async def get_page(page_id: str):
            """Get a Notion page."""
            try:
                result = await self._get_page(page_id)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting page: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-database/{database_id}")
        async def get_database(database_id: str):
            """Get a Notion database."""
            try:
                result = await self._get_database(database_id)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting database: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.put("/update-page/{page_id}")
        async def update_page(page_id: str, page: NotionPage):
            """Update a Notion page."""
            try:
                result = await self._update_page(page_id, page)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error updating page: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/add-block/{page_id}")
        async def add_block(page_id: str, block: NotionBlock):
            """Add a block to a page."""
            try:
                result = await self._add_block(page_id, block)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error adding block: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/search")
        async def search(query: str, filter_type: Optional[str] = None):
            """Search Notion pages and databases."""
            try:
                result = await self._search(query, filter_type)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error searching: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/databases")
        async def get_databases():
            """Get all databases."""
            try:
                result = await self._get_databases()
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting databases: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-project-docs")
        async def create_project_docs(
            project_name: str,
            description: str,
            team_members: List[str],
            timeline: str
        ):
            """Create project documentation structure."""
            try:
                result = await self._create_project_docs(project_name, description, team_members, timeline)
                return NotionMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating project docs: {e}")
                return NotionMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
    
    async def _initialize_client(self):
        """Initialize Notion client."""
        self.api_key = os.getenv("NOTION_API_KEY")
        
        if not self.api_key:
            logger.warning("NOTION_API_KEY not found in environment")
            return
        
        try:
            self.client = NotionClient(auth=self.api_key)
            
            # Test connection
            response = await self.client.users.me()
            logger.info(f"Connected to Notion as: {response['name']}")
            
            # Load initial data
            await self._load_databases()
            
        except Exception as e:
            logger.error(f"Failed to initialize Notion client: {e}")
            self.client = None
    
    async def _cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.close()
    
    async def _create_page(self, page: NotionPage) -> Dict[str, Any]:
        """Create a new Notion page."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            properties = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": page.title
                            }
                        }
                    ]
                }
            }
            
            if page.properties:
                properties.update(page.properties)
            
            parent = {}
            if page.parent_id:
                if page.parent_id.startswith("db_"):
                    parent = {"database_id": page.parent_id}
                else:
                    parent = {"page_id": page.parent_id}
            else:
                # Use default workspace
                parent = {"type": "workspace"}
            
            response = await self.client.pages.create(
                parent=parent,
                properties=properties
            )
            
            # Add content if provided
            if page.content:
                await self._add_content(response["id"], page.content)
            
            self.pages_cache[response["id"]] = response
            return response
        
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            raise
    
    async def _create_database(self, database: NotionDatabase) -> Dict[str, Any]:
        """Create a new Notion database."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            properties = {
                "Name": {
                    "title": {}
                }
            }
            
            if database.properties:
                properties.update(database.properties)
            
            parent = {}
            if database.parent_id:
                parent = {"page_id": database.parent_id}
            else:
                parent = {"type": "workspace"}
            
            response = await self.client.databases.create(
                parent=parent,
                title=[
                    {
                        "text": {
                            "content": database.title
                        }
                    }
                ],
                properties=properties
            )
            
            self.databases_cache[response["id"]] = response
            return response
        
        except Exception as e:
            logger.error(f"Error creating Notion database: {e}")
            raise
    
    async def _get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a Notion page."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            response = await self.client.pages.retrieve(page_id)
            return response
        
        except Exception as e:
            logger.error(f"Error getting Notion page: {e}")
            raise
    
    async def _get_database(self, database_id: str) -> Dict[str, Any]:
        """Get a Notion database."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            response = await self.client.databases.retrieve(database_id)
            return response
        
        except Exception as e:
            logger.error(f"Error getting Notion database: {e}")
            raise
    
    async def _update_page(self, page_id: str, page: NotionPage) -> Dict[str, Any]:
        """Update a Notion page."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            properties = {}
            if page.title:
                properties["title"] = {
                    "title": [
                        {
                            "text": {
                                "content": page.title
                            }
                        }
                    ]
                }
            
            if page.properties:
                properties.update(page.properties)
            
            response = await self.client.pages.update(
                page_id,
                properties=properties
            )
            
            self.pages_cache[page_id] = response
            return response
        
        except Exception as e:
            logger.error(f"Error updating Notion page: {e}")
            raise
    
    async def _add_block(self, page_id: str, block: NotionBlock) -> Dict[str, Any]:
        """Add a block to a page."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            block_data = {
                "type": block.type,
                block.type: {
                    "rich_text": [
                        {
                            "text": {
                                "content": block.content
                            }
                        }
                    ]
                }
            }
            
            if block.properties:
                block_data[block.type].update(block.properties)
            
            response = await self.client.blocks.children.append(
                page_id,
                children=[block_data]
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error adding block: {e}")
            raise
    
    async def _add_content(self, page_id: str, content: str) -> None:
        """Add content to a page."""
        try:
            # Split content into paragraphs
            paragraphs = content.split('\n\n')
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    block = NotionBlock(
                        type="paragraph",
                        content=paragraph.strip()
                    )
                    await self._add_block(page_id, block)
        
        except Exception as e:
            logger.error(f"Error adding content: {e}")
            raise
    
    async def _search(self, query: str, filter_type: Optional[str] = None) -> Dict[str, Any]:
        """Search Notion pages and databases."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            filter_data = {}
            if filter_type:
                filter_data = {"property": "object", "value": filter_type}
            
            response = await self.client.search(
                query=query,
                filter=filter_data if filter_data else None
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error searching Notion: {e}")
            raise
    
    async def _get_databases(self) -> Dict[str, Any]:
        """Get all databases."""
        if not self.client:
            raise Exception("Notion client not initialized")
        
        try:
            response = await self.client.search(
                filter={"property": "object", "value": "database"}
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting databases: {e}")
            raise
    
    async def _load_databases(self):
        """Load databases into cache."""
        try:
            response = await self._get_databases()
            for database in response["results"]:
                self.databases_cache[database["id"]] = database
            logger.info(f"Loaded {len(self.databases_cache)} databases")
        except Exception as e:
            logger.error(f"Failed to load databases: {e}")
    
    async def _create_project_docs(
        self,
        project_name: str,
        description: str,
        team_members: List[str],
        timeline: str
    ) -> Dict[str, Any]:
        """Create project documentation structure."""
        try:
            # Create main project page
            project_page = NotionPage(
                title=f"📋 {project_name}",
                content=f"""
# {project_name}

## Project Overview
{description}

## Team Members
{', '.join(team_members)}

## Timeline
{timeline}

## Project Status
🟡 In Progress

## Key Deliverables
- [ ] Requirements gathering
- [ ] Design phase
- [ ] Development phase
- [ ] Testing phase
- [ ] Deployment

## Notes
*Add project notes here*
                """.strip()
            )
            
            main_page = await self._create_page(project_page)
            
            # Create sub-pages for different sections
            sections = [
                ("Requirements", "📝 Requirements and specifications"),
                ("Design", "🎨 Design documents and mockups"),
                ("Development", "💻 Development progress and code"),
                ("Testing", "🧪 Testing plans and results"),
                ("Deployment", "🚀 Deployment and release notes"),
                ("Meeting Notes", "📝 Meeting notes and decisions")
            ]
            
            created_pages = [main_page]
            
            for section_name, section_title in sections:
                section_page = NotionPage(
                    title=section_title,
                    parent_id=main_page["id"],
                    content=f"# {section_name}\n\n*Add {section_name.lower()} content here*"
                )
                
                section_result = await self._create_page(section_page)
                created_pages.append(section_result)
            
            return {
                "main_page": main_page,
                "sections": created_pages[1:],
                "total_pages": len(created_pages)
            }
        
        except Exception as e:
            logger.error(f"Error creating project docs: {e}")
            raise


# Create server instance
notion_server = NotionMCPServer()
app = notion_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 