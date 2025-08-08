import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

class MCPManager:
    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.endpoints = {
            "slack": settings.SLACK_MCP_ENDPOINT,
            "whatsapp": settings.WHATSAPP_MCP_ENDPOINT,
            "webex": settings.WEBEX_MCP_ENDPOINT,
            "notion": settings.NOTION_MCP_ENDPOINT,
            "github": settings.GITHUB_MCP_ENDPOINT,
            "postgresql": settings.POSTGRESQL_MCP_ENDPOINT,
            "filesystem": settings.FILESYSTEM_MCP_ENDPOINT,
            "docker": settings.DOCKER_MCP_ENDPOINT,
            "redis": settings.REDIS_MCP_ENDPOINT,
            "tldv": settings.TLDV_MCP_ENDPOINT
        }
        self.is_initialized = False
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize MCP connections"""
        if self.is_initialized:
            return
            
        logger.info("🔗 Initializing MCP Manager...")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession()
        
        # Test connections to all MCP servers
        for service_name, endpoint in self.endpoints.items():
            try:
                async with self.session.get(f"{endpoint}/health") as response:
                    if response.status == 200:
                        self.connections[service_name] = {
                            "endpoint": endpoint,
                            "status": "connected",
                            "last_check": datetime.now()
                        }
                        logger.info(f"✅ {service_name} MCP connected")
                    else:
                        self.connections[service_name] = {
                            "endpoint": endpoint,
                            "status": "error",
                            "last_check": datetime.now()
                        }
                        logger.warning(f"⚠️ {service_name} MCP connection failed")
            except Exception as e:
                self.connections[service_name] = {
                    "endpoint": endpoint,
                    "status": "error",
                    "last_check": datetime.now(),
                    "error": str(e)
                }
                logger.warning(f"⚠️ {service_name} MCP connection error: {e}")
        
        self.is_initialized = True
        logger.info("✅ MCP Manager initialized")
    
    async def cleanup(self):
        """Cleanup MCP connections"""
        logger.info("🛑 Cleaning up MCP Manager...")
        
        if self.session:
            await self.session.close()
        
        self.connections.clear()
        self.is_initialized = False
        logger.info("✅ MCP Manager cleanup completed")
    
    async def send_message(self, service: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via MCP server"""
        if service not in self.connections:
            raise ValueError(f"Service {service} not available")
        
        if self.connections[service]["status"] != "connected":
            raise ConnectionError(f"Service {service} not connected")
        
        endpoint = self.connections[service]["endpoint"]
        
        try:
            async with self.session.post(f"{endpoint}/send", json=message_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Message sent via {service}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to send message via {service}: {error_text}")
                    raise Exception(f"Failed to send message: {error_text}")
        except Exception as e:
            logger.error(f"❌ Error sending message via {service}: {e}")
            raise
    
    async def get_messages(self, service: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get messages from MCP server"""
        if service not in self.connections:
            raise ValueError(f"Service {service} not available")
        
        if self.connections[service]["status"] != "connected":
            raise ConnectionError(f"Service {service} not connected")
        
        endpoint = self.connections[service]["endpoint"]
        
        try:
            params = filters or {}
            async with self.session.get(f"{endpoint}/messages", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Retrieved messages from {service}")
                    return result.get("messages", [])
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to get messages from {service}: {error_text}")
                    raise Exception(f"Failed to get messages: {error_text}")
        except Exception as e:
            logger.error(f"❌ Error getting messages from {service}: {e}")
            raise
    
    async def create_document(self, service: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create document via MCP server (Notion, etc.)"""
        if service not in self.connections:
            raise ValueError(f"Service {service} not available")
        
        if self.connections[service]["status"] != "connected":
            raise ConnectionError(f"Service {service} not connected")
        
        endpoint = self.connections[service]["endpoint"]
        
        try:
            async with self.session.post(f"{endpoint}/documents", json=document_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Document created via {service}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create document via {service}: {error_text}")
                    raise Exception(f"Failed to create document: {error_text}")
        except Exception as e:
            logger.error(f"❌ Error creating document via {service}: {e}")
            raise
    
    async def schedule_meeting(self, service: str, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule meeting via MCP server (Webex, etc.)"""
        if service not in self.connections:
            raise ValueError(f"Service {service} not available")
        
        if self.connections[service]["status"] != "connected":
            raise ConnectionError(f"Service {service} not connected")
        
        endpoint = self.connections[service]["endpoint"]
        
        try:
            async with self.session.post(f"{endpoint}/meetings", json=meeting_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Meeting scheduled via {service}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to schedule meeting via {service}: {error_text}")
                    raise Exception(f"Failed to schedule meeting: {error_text}")
        except Exception as e:
            logger.error(f"❌ Error scheduling meeting via {service}: {e}")
            raise
    
    async def create_repository(self, service: str, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create repository via MCP server (GitHub, etc.)"""
        if service not in self.connections:
            raise ValueError(f"Service {service} not available")
        
        if self.connections[service]["status"] != "connected":
            raise ConnectionError(f"Service {service} not connected")
        
        endpoint = self.connections[service]["endpoint"]
        
        try:
            async with self.session.post(f"{endpoint}/repositories", json=repo_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Repository created via {service}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to create repository via {service}: {error_text}")
                    raise Exception(f"Failed to create repository: {error_text}")
        except Exception as e:
            logger.error(f"❌ Error creating repository via {service}: {e}")
            raise
    
    async def execute_query(self, service: str, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query via MCP server (PostgreSQL, Redis, etc.)"""
        if service not in self.connections:
            raise ValueError(f"Service {service} not available")
        
        if self.connections[service]["status"] != "connected":
            raise ConnectionError(f"Service {service} not connected")
        
        endpoint = self.connections[service]["endpoint"]
        
        try:
            async with self.session.post(f"{endpoint}/query", json=query_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Query executed via {service}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to execute query via {service}: {error_text}")
                    raise Exception(f"Failed to execute query: {error_text}")
        except Exception as e:
            logger.error(f"❌ Error executing query via {service}: {e}")
            raise
    
    async def manage_container(self, service: str, container_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage containers via MCP server (Docker, etc.)"""
        if service not in self.connections:
            raise ValueError(f"Service {service} not available")
        
        if self.connections[service]["status"] != "connected":
            raise ConnectionError(f"Service {service} not connected")
        
        endpoint = self.connections[service]["endpoint"]
        
        try:
            async with self.session.post(f"{endpoint}/containers", json=container_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Container managed via {service}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to manage container via {service}: {error_text}")
                    raise Exception(f"Failed to manage container: {error_text}")
        except Exception as e:
            logger.error(f"❌ Error managing container via {service}: {e}")
            raise
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all MCP connections"""
        return {
            "initialized": self.is_initialized,
            "connections": self.connections
        }
    
    def get_available_services(self) -> List[str]:
        """Get list of available MCP services"""
        return [service for service, conn in self.connections.items() 
                if conn["status"] == "connected"] 