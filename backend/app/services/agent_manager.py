import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.services.agents.requirements_agent import RequirementsAgent
from app.services.agents.planning_agent import PlanningAgent
from app.services.agents.development_agent import DevelopmentAgent
from app.services.agents.testing_agent import TestingAgent
from app.services.agents.communication_agent import CommunicationAgent
from app.services.mcp_manager import MCPManager

logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    REQUIREMENTS = "requirements"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    COMMUNICATION = "communication"

@dataclass
class AgentTask:
    id: str
    agent_type: AgentType
    project_id: int
    task_data: Dict[str, Any]
    priority: str = "medium"
    status: str = "pending"
    created_at: datetime = None
    completed_at: datetime = None
    result: Dict[str, Any] = None
    error: str = None

class AgentManager:
    def __init__(self):
        self.agents: Dict[AgentType, Any] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.mcp_manager: Optional[MCPManager] = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize all agents and MCP manager"""
        if self.is_initialized:
            return
            
        logger.info("🤖 Initializing Agent Manager...")
        
        # Initialize MCP Manager
        self.mcp_manager = MCPManager()
        await self.mcp_manager.initialize()
        
        # Initialize specialized agents
        self.agents[AgentType.REQUIREMENTS] = RequirementsAgent(self.mcp_manager)
        self.agents[AgentType.PLANNING] = PlanningAgent(self.mcp_manager)
        self.agents[AgentType.DEVELOPMENT] = DevelopmentAgent(self.mcp_manager)
        self.agents[AgentType.TESTING] = TestingAgent(self.mcp_manager)
        self.agents[AgentType.COMMUNICATION] = CommunicationAgent(self.mcp_manager)
        
        # Initialize each agent
        for agent_type, agent in self.agents.items():
            await agent.initialize()
            logger.info(f"✅ Initialized {agent_type.value} agent")
        
        self.is_initialized = True
        logger.info("✅ Agent Manager initialized successfully")
    
    async def cleanup(self):
        """Cleanup all agents and connections"""
        logger.info("🛑 Cleaning up Agent Manager...")
        
        for agent_type, agent in self.agents.items():
            await agent.cleanup()
            logger.info(f"✅ Cleaned up {agent_type.value} agent")
        
        if self.mcp_manager:
            await self.mcp_manager.cleanup()
        
        self.is_initialized = False
        logger.info("✅ Agent Manager cleanup completed")
    
    async def create_task(self, agent_type: AgentType, project_id: int, task_data: Dict[str, Any], priority: str = "medium") -> str:
        """Create a new agent task"""
        task_id = f"{agent_type.value}_{project_id}_{datetime.now().timestamp()}"
        
        task = AgentTask(
            id=task_id,
            agent_type=agent_type,
            project_id=project_id,
            task_data=task_data,
            priority=priority,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        logger.info(f"📋 Created task {task_id} for {agent_type.value} agent")
        
        return task_id
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a specific agent task"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        agent = self.agents.get(task.agent_type)
        
        if not agent:
            raise ValueError(f"Agent type {task.agent_type} not found")
        
        try:
            logger.info(f"🚀 Executing task {task_id} with {task.agent_type.value} agent")
            task.status = "running"
            
            result = await agent.execute_task(task.task_data)
            
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result
            
            logger.info(f"✅ Task {task_id} completed successfully")
            return result
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"❌ Task {task_id} failed: {e}")
            raise
    
    async def execute_workflow(self, project_id: int, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete SDLC workflow"""
        logger.info(f"🔄 Starting SDLC workflow for project {project_id}")
        
        workflow_results = {}
        
        # 1. Requirements Gathering
        if "requirements" in workflow_data:
            req_task_id = await self.create_task(
                AgentType.REQUIREMENTS,
                project_id,
                workflow_data["requirements"]
            )
            workflow_results["requirements"] = await self.execute_task(req_task_id)
        
        # 2. Planning and Epic Creation
        if "planning" in workflow_data:
            plan_task_id = await self.create_task(
                AgentType.PLANNING,
                project_id,
                workflow_data["planning"]
            )
            workflow_results["planning"] = await self.execute_task(plan_task_id)
        
        # 3. Development Planning
        if "development" in workflow_data:
            dev_task_id = await self.create_task(
                AgentType.DEVELOPMENT,
                project_id,
                workflow_data["development"]
            )
            workflow_results["development"] = await self.execute_task(dev_task_id)
        
        # 4. Testing Strategy
        if "testing" in workflow_data:
            test_task_id = await self.create_task(
                AgentType.TESTING,
                project_id,
                workflow_data["testing"]
            )
            workflow_results["testing"] = await self.execute_task(test_task_id)
        
        # 5. Communication Setup
        if "communication" in workflow_data:
            comm_task_id = await self.create_task(
                AgentType.COMMUNICATION,
                project_id,
                workflow_data["communication"]
            )
            workflow_results["communication"] = await self.execute_task(comm_task_id)
        
        logger.info(f"✅ SDLC workflow completed for project {project_id}")
        return workflow_results
    
    async def analyze_conversations(self, project_id: int, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversations and extract requirements"""
        logger.info(f"🔍 Analyzing conversations for project {project_id}")
        
        task_data = {
            "conversations": conversations,
            "project_id": project_id,
            "analysis_type": "requirements_extraction"
        }
        
        task_id = await self.create_task(AgentType.REQUIREMENTS, project_id, task_data)
        return await self.execute_task(task_id)
    
    async def generate_epics_and_stories(self, project_id: int, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate epics and user stories from requirements"""
        logger.info(f"📋 Generating epics and stories for project {project_id}")
        
        task_data = {
            "requirements": requirements,
            "project_id": project_id,
            "planning_type": "epic_story_generation"
        }
        
        task_id = await self.create_task(AgentType.PLANNING, project_id, task_data)
        return await self.execute_task(task_id)
    
    async def schedule_meetings(self, project_id: int, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule meetings and coordinate participants"""
        logger.info(f"📅 Scheduling meetings for project {project_id}")
        
        task_data = {
            "meeting_data": meeting_data,
            "project_id": project_id,
            "communication_type": "meeting_scheduling"
        }
        
        task_id = await self.create_task(AgentType.COMMUNICATION, project_id, task_data)
        return await self.execute_task(task_id)
    
    async def update_user_story_status(self, project_id: int, story_id: int, status: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user story status and generate new stories if needed"""
        logger.info(f"📝 Updating user story {story_id} status to {status}")
        
        task_data = {
            "story_id": story_id,
            "status": status,
            "completion_data": completion_data,
            "project_id": project_id,
            "update_type": "story_status_update"
        }
        
        task_id = await self.create_task(AgentType.PLANNING, project_id, task_data)
        return await self.execute_task(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "id": task.id,
            "agent_type": task.agent_type.value,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error,
            "result": task.result
        }
    
    def get_all_tasks(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all tasks or tasks for a specific project"""
        tasks = []
        
        for task in self.tasks.values():
            if project_id is None or task.project_id == project_id:
                tasks.append(self.get_task_status(task.id))
        
        return tasks 