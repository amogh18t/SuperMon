import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from pydantic import BaseModel

from app.core.config import settings
from app.services.mcp_manager import MCPManager

logger = logging.getLogger(__name__)

class Requirement(BaseModel):
    id: str
    title: str
    description: str
    category: str  # functional, non-functional, technical, business
    priority: str  # low, medium, high, critical
    source: str  # slack, webex, whatsapp, ui
    confidence: float  # 0.0 to 1.0
    extracted_at: datetime
    metadata: Dict[str, Any] = {}

class RequirementsAgent:
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
        self.gemini_model = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the Requirements Agent"""
        if self.is_initialized:
            return
            
        logger.info("🔍 Initializing Requirements Agent...")
        
        # Initialize Gemini
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("✅ Gemini model initialized")
        else:
            logger.warning("⚠️ Gemini API key not configured")
        
        self.is_initialized = True
        logger.info("✅ Requirements Agent initialized")
    
    async def cleanup(self):
        """Cleanup the Requirements Agent"""
        logger.info("🛑 Cleaning up Requirements Agent...")
        self.is_initialized = False
        logger.info("✅ Requirements Agent cleanup completed")
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a requirements analysis task"""
        if not self.is_initialized:
            raise RuntimeError("Requirements Agent not initialized")
        
        task_type = task_data.get("analysis_type", "requirements_extraction")
        
        if task_type == "requirements_extraction":
            return await self._extract_requirements(task_data)
        elif task_type == "requirements_validation":
            return await self._validate_requirements(task_data)
        elif task_type == "requirements_prioritization":
            return await self._prioritize_requirements(task_data)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _extract_requirements(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requirements from conversations"""
        conversations = task_data.get("conversations", [])
        project_id = task_data.get("project_id")
        
        logger.info(f"🔍 Extracting requirements from {len(conversations)} conversations")
        
        all_requirements = []
        
        for conversation in conversations:
            requirements = await self._analyze_conversation(conversation)
            all_requirements.extend(requirements)
        
        # Deduplicate and merge requirements
        merged_requirements = await self._merge_requirements(all_requirements)
        
        # Generate summary
        summary = await self._generate_requirements_summary(merged_requirements)
        
        return {
            "project_id": project_id,
            "requirements": [req.dict() for req in merged_requirements],
            "summary": summary,
            "total_count": len(merged_requirements),
            "categories": self._categorize_requirements(merged_requirements),
            "extracted_at": datetime.now().isoformat()
        }
    
    async def _analyze_conversation(self, conversation: Dict[str, Any]) -> List[Requirement]:
        """Analyze a single conversation for requirements"""
        if not self.gemini_model:
            logger.warning("⚠️ Gemini model not available, using basic extraction")
            return self._basic_requirement_extraction(conversation)
        
        try:
            # Prepare conversation text
            conversation_text = self._format_conversation(conversation)
            
            # Create prompt for requirements extraction
            prompt = f"""
            Analyze the following conversation and extract software requirements. 
            Focus on functional requirements, non-functional requirements, technical specifications, and business needs.
            
            Conversation:
            {conversation_text}
            
            Extract requirements in the following JSON format:
            {{
                "requirements": [
                    {{
                        "title": "Requirement title",
                        "description": "Detailed description",
                        "category": "functional|non-functional|technical|business",
                        "priority": "low|medium|high|critical",
                        "confidence": 0.0-1.0,
                        "source": "conversation",
                        "metadata": {{}}
                    }}
                ]
            }}
            
            Be specific and actionable. Focus on requirements that can be implemented.
            """
            
            # Generate response using Gemini
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            # Parse response
            try:
                result = json.loads(response.text)
                requirements = []
                
                for req_data in result.get("requirements", []):
                    requirement = Requirement(
                        id=f"req_{datetime.now().timestamp()}_{len(requirements)}",
                        title=req_data["title"],
                        description=req_data["description"],
                        category=req_data["category"],
                        priority=req_data["priority"],
                        source=req_data["source"],
                        confidence=req_data["confidence"],
                        extracted_at=datetime.now(),
                        metadata=req_data.get("metadata", {})
                    )
                    requirements.append(requirement)
                
                logger.info(f"✅ Extracted {len(requirements)} requirements from conversation")
                return requirements
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse Gemini response: {e}")
                return self._basic_requirement_extraction(conversation)
                
        except Exception as e:
            logger.error(f"❌ Error analyzing conversation: {e}")
            return self._basic_requirement_extraction(conversation)
    
    def _basic_requirement_extraction(self, conversation: Dict[str, Any]) -> List[Requirement]:
        """Basic requirement extraction when AI is not available"""
        requirements = []
        
        # Extract key phrases that might indicate requirements
        text = conversation.get("content", "").lower()
        
        requirement_keywords = [
            "need", "require", "must", "should", "want", "expect",
            "feature", "functionality", "capability", "system",
            "user", "admin", "interface", "dashboard", "report"
        ]
        
        sentences = text.split(".")
        for sentence in sentences:
            if any(keyword in sentence for keyword in requirement_keywords):
                requirement = Requirement(
                    id=f"req_{datetime.now().timestamp()}_{len(requirements)}",
                    title=f"Requirement from conversation",
                    description=sentence.strip(),
                    category="functional",
                    priority="medium",
                    source="conversation",
                    confidence=0.5,
                    extracted_at=datetime.now()
                )
                requirements.append(requirement)
        
        return requirements
    
    def _format_conversation(self, conversation: Dict[str, Any]) -> str:
        """Format conversation for analysis"""
        formatted = []
        
        # Add conversation metadata
        if "channel" in conversation:
            formatted.append(f"Channel: {conversation['channel']}")
        if "participants" in conversation:
            formatted.append(f"Participants: {', '.join(conversation['participants'])}")
        
        # Add messages
        messages = conversation.get("messages", [])
        for message in messages:
            sender = message.get("sender", "Unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            formatted.append(f"[{timestamp}] {sender}: {content}")
        
        return "\n".join(formatted)
    
    async def _merge_requirements(self, requirements: List[Requirement]) -> List[Requirement]:
        """Merge similar requirements"""
        if not self.gemini_model:
            return requirements
        
        try:
            # Group requirements by category
            categories = {}
            for req in requirements:
                if req.category not in categories:
                    categories[req.category] = []
                categories[req.category].append(req)
            
            merged_requirements = []
            
            for category, reqs in categories.items():
                if len(reqs) <= 1:
                    merged_requirements.extend(reqs)
                    continue
                
                # Create prompt for merging
                req_texts = [f"- {req.title}: {req.description}" for req in reqs]
                req_text = "\n".join(req_texts)
                
                prompt = f"""
                Merge the following {category} requirements into consolidated requirements:
                
                {req_text}
                
                Return merged requirements in JSON format:
                {{
                    "merged_requirements": [
                        {{
                            "title": "Merged title",
                            "description": "Comprehensive description",
                            "priority": "highest_priority_among_merged",
                            "confidence": "average_confidence"
                        }}
                    ]
                }}
                """
                
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    prompt
                )
                
                try:
                    result = json.loads(response.text)
                    for req_data in result.get("merged_requirements", []):
                        merged_req = Requirement(
                            id=f"merged_{datetime.now().timestamp()}_{len(merged_requirements)}",
                            title=req_data["title"],
                            description=req_data["description"],
                            category=category,
                            priority=req_data["priority"],
                            source="merged",
                            confidence=req_data["confidence"],
                            extracted_at=datetime.now()
                        )
                        merged_requirements.append(merged_req)
                        
                except json.JSONDecodeError:
                    # If merging fails, keep original requirements
                    merged_requirements.extend(reqs)
            
            return merged_requirements
            
        except Exception as e:
            logger.error(f"❌ Error merging requirements: {e}")
            return requirements
    
    async def _generate_requirements_summary(self, requirements: List[Requirement]) -> str:
        """Generate a summary of all requirements"""
        if not self.gemini_model:
            return f"Extracted {len(requirements)} requirements across different categories."
        
        try:
            req_summary = []
            for req in requirements:
                req_summary.append(f"- {req.title} ({req.category}, {req.priority})")
            
            req_text = "\n".join(req_summary)
            
            prompt = f"""
            Generate a comprehensive summary of the following software requirements:
            
            {req_text}
            
            Provide a structured summary including:
            1. Overview of the project scope
            2. Key functional requirements
            3. Non-functional requirements
            4. Technical considerations
            5. Business value
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")
            return f"Extracted {len(requirements)} requirements across different categories."
    
    def _categorize_requirements(self, requirements: List[Requirement]) -> Dict[str, int]:
        """Categorize requirements by type"""
        categories = {}
        for req in requirements:
            categories[req.category] = categories.get(req.category, 0) + 1
        return categories
    
    async def _validate_requirements(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate requirements for completeness and clarity"""
        requirements = task_data.get("requirements", [])
        
        validation_results = []
        for req in requirements:
            validation = {
                "requirement_id": req.get("id"),
                "is_complete": len(req.get("description", "")) > 10,
                "is_specific": "specific" in req.get("description", "").lower(),
                "has_acceptance_criteria": "when" in req.get("description", "").lower() or "then" in req.get("description", "").lower(),
                "suggestions": []
            }
            
            if not validation["is_complete"]:
                validation["suggestions"].append("Add more detailed description")
            if not validation["is_specific"]:
                validation["suggestions"].append("Make requirement more specific")
            if not validation["has_acceptance_criteria"]:
                validation["suggestions"].append("Add acceptance criteria")
            
            validation_results.append(validation)
        
        return {
            "validation_results": validation_results,
            "total_requirements": len(requirements),
            "validated_at": datetime.now().isoformat()
        }
    
    async def _prioritize_requirements(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize requirements based on business value and technical feasibility"""
        requirements = task_data.get("requirements", [])
        
        if not self.gemini_model:
            return {"requirements": requirements, "prioritized_at": datetime.now().isoformat()}
        
        try:
            req_texts = []
            for req in requirements:
                req_texts.append(f"- {req.get('title')}: {req.get('description')} (Priority: {req.get('priority')})")
            
            req_text = "\n".join(req_texts)
            
            prompt = f"""
            Prioritize the following requirements based on business value, technical feasibility, and dependencies:
            
            {req_text}
            
            Return prioritized requirements with updated priorities and reasoning:
            {{
                "prioritized_requirements": [
                    {{
                        "id": "requirement_id",
                        "new_priority": "critical|high|medium|low",
                        "reasoning": "Explanation for priority change",
                        "dependencies": ["list", "of", "dependencies"],
                        "business_value": "high|medium|low",
                        "technical_complexity": "high|medium|low"
                    }}
                ]
            }}
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            
            try:
                result = json.loads(response.text)
                return {
                    "prioritized_requirements": result.get("prioritized_requirements", []),
                    "prioritized_at": datetime.now().isoformat()
                }
            except json.JSONDecodeError:
                return {"requirements": requirements, "prioritized_at": datetime.now().isoformat()}
                
        except Exception as e:
            logger.error(f"❌ Error prioritizing requirements: {e}")
            return {"requirements": requirements, "prioritized_at": datetime.now().isoformat()} 