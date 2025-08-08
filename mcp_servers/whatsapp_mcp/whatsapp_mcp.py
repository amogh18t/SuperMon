"""WhatsApp MCP Server for SuperMon platform."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import base64
import mimetypes

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import aiofiles

logger = logging.getLogger(__name__)


class WhatsAppMessage(BaseModel):
    """WhatsApp message model."""
    to: str = Field(..., description="Recipient phone number")
    text: str = Field(..., description="Message text")
    media_url: Optional[str] = Field(None, description="Media URL")
    media_type: Optional[str] = Field(None, description="Media type (image, video, audio, document)")
    reply_to: Optional[str] = Field(None, description="Message ID to reply to")
    template_name: Optional[str] = Field(None, description="Template name for template messages")
    template_params: Optional[Dict[str, Any]] = Field(None, description="Template parameters")


class WhatsAppContact(BaseModel):
    """WhatsApp contact model."""
    phone_number: str = Field(..., description="Phone number")
    name: Optional[str] = Field(None, description="Contact name")
    email: Optional[str] = Field(None, description="Email address")
    company: Optional[str] = Field(None, description="Company name")
    status: str = Field(default="active", description="Contact status")


class WhatsAppConversation(BaseModel):
    """WhatsApp conversation model."""
    phone_number: str = Field(..., description="Phone number")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Messages")
    start_time: datetime = Field(..., description="Conversation start time")
    end_time: Optional[datetime] = Field(None, description="Conversation end time")
    status: str = Field(default="active", description="Conversation status")


class WhatsAppMCPResponse(BaseModel):
    """Standard MCP response model."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class WhatsAppMCPServer:
    """WhatsApp MCP Server implementation."""
    
    def __init__(self):
        """Initialize WhatsApp MCP Server."""
        self.app = FastAPI(title="WhatsApp MCP Server", version="1.0.0")
        self.api_key: Optional[str] = None
        self.phone_number_id: Optional[str] = None
        self.base_url: str = "https://graph.facebook.com/v18.0"
        self.contacts: Dict[str, WhatsAppContact] = {}
        self.conversations: Dict[str, WhatsAppConversation] = {}
        self.message_queue: List[Dict[str, Any]] = []
        
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
            """Initialize WhatsApp client on startup."""
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
                "service": "WhatsApp MCP Server",
                "connected": self.api_key is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/send-message")
        async def send_message(message: WhatsAppMessage):
            """Send a WhatsApp message."""
            try:
                result = await self._send_message(message)
                return WhatsAppMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/send-template")
        async def send_template(
            to: str,
            template_name: str,
            template_params: Dict[str, Any]
        ):
            """Send a template message."""
            try:
                result = await self._send_template(to, template_name, template_params)
                return WhatsAppMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error sending template: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/send-media")
        async def send_media(
            to: str,
            media_url: str,
            media_type: str,
            caption: Optional[str] = None
        ):
            """Send a media message."""
            try:
                result = await self._send_media(to, media_url, media_type, caption)
                return WhatsAppMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error sending media: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-messages/{phone_number}")
        async def get_messages(
            phone_number: str,
            limit: int = 100,
            since: Optional[str] = None
        ):
            """Get messages from a conversation."""
            try:
                messages = await self._get_messages(phone_number, limit, since)
                return WhatsAppMCPResponse(
                    success=True,
                    data={"messages": messages},
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting messages: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/contacts")
        async def get_contacts():
            """Get all contacts."""
            try:
                contacts = list(self.contacts.values())
                return WhatsAppMCPResponse(
                    success=True,
                    data={"contacts": [asdict(contact) for contact in contacts]},
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting contacts: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/add-contact")
        async def add_contact(contact: WhatsAppContact):
            """Add a new contact."""
            try:
                result = await self._add_contact(contact)
                return WhatsAppMCPResponse(
                    success=True,
                    data=asdict(result),
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error adding contact: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/start-conversation")
        async def start_conversation(phone_number: str):
            """Start tracking a conversation."""
            try:
                conversation = await self._start_conversation(phone_number)
                return WhatsAppMCPResponse(
                    success=True,
                    data=asdict(conversation),
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error starting conversation: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/end-conversation/{phone_number}")
        async def end_conversation(phone_number: str):
            """End tracking a conversation."""
            try:
                conversation = await self._end_conversation(phone_number)
                return WhatsAppMCPResponse(
                    success=True,
                    data=asdict(conversation),
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error ending conversation: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/conversations")
        async def get_conversations():
            """Get all tracked conversations."""
            try:
                conversations = list(self.conversations.values())
                return WhatsAppMCPResponse(
                    success=True,
                    data={"conversations": [asdict(conv) for conv in conversations]},
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting conversations: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/upload-media")
        async def upload_media(file: UploadFile = File(...)):
            """Upload media file."""
            try:
                result = await self._upload_media(file)
                return WhatsAppMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error uploading media: {e}")
                return WhatsAppMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
    
    async def _initialize_client(self):
        """Initialize WhatsApp client."""
        self.api_key = os.getenv("WHATSAPP_API_KEY")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        
        if not self.api_key or not self.phone_number_id:
            logger.warning("WhatsApp API credentials not found in environment")
            return
        
        try:
            # Test connection
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{self.phone_number_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                logger.info("WhatsApp API connection established")
        
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp client: {e}")
            self.api_key = None
            self.phone_number_id = None
    
    async def _cleanup(self):
        """Cleanup resources."""
        # Process any remaining messages in queue
        if self.message_queue:
            logger.info(f"Processing {len(self.message_queue)} queued messages")
            for message in self.message_queue:
                try:
                    await self._send_message_internal(message)
                except Exception as e:
                    logger.error(f"Failed to send queued message: {e}")
    
    async def _send_message(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Send a WhatsApp message."""
        if not self.api_key or not self.phone_number_id:
            raise Exception("WhatsApp API not initialized")
        
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": message.to,
                "type": "text",
                "text": {"body": message.text}
            }
            
            if message.reply_to:
                payload["context"] = {"message_id": message.reply_to}
            
            result = await self._send_message_internal(payload)
            
            # Update conversation if tracking
            if message.to in self.conversations:
                self.conversations[message.to].messages.append({
                    "id": result["messages"][0]["id"],
                    "text": message.text,
                    "direction": "outbound",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            raise
    
    async def _send_template(
        self,
        to: str,
        template_name: str,
        template_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a template message."""
        if not self.api_key or not self.phone_number_id:
            raise Exception("WhatsApp API not initialized")
        
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": []
                }
            }
            
            # Add parameters if provided
            if template_params:
                components = []
                for key, value in template_params.items():
                    components.append({
                        "type": "text",
                        "text": {"body": str(value)}
                    })
                payload["template"]["components"] = components
            
            result = await self._send_message_internal(payload)
            
            # Update conversation if tracking
            if to in self.conversations:
                self.conversations[to].messages.append({
                    "id": result["messages"][0]["id"],
                    "template": template_name,
                    "direction": "outbound",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            raise
    
    async def _send_media(
        self,
        to: str,
        media_url: str,
        media_type: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a media message."""
        if not self.api_key or not self.phone_number_id:
            raise Exception("WhatsApp API not initialized")
        
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                media_type: {"link": media_url}
            }
            
            if caption:
                payload[media_type]["caption"] = caption
            
            result = await self._send_message_internal(payload)
            
            # Update conversation if tracking
            if to in self.conversations:
                self.conversations[to].messages.append({
                    "id": result["messages"][0]["id"],
                    "media_type": media_type,
                    "media_url": media_url,
                    "direction": "outbound",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error sending media message: {e}")
            raise
    
    async def _send_message_internal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to WhatsApp API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{self.phone_number_id}/messages",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def _get_messages(
        self,
        phone_number: str,
        limit: int = 100,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation."""
        # This would typically involve webhook handling or API polling
        # For now, return messages from tracked conversations
        if phone_number in self.conversations:
            return self.conversations[phone_number].messages
        return []
    
    async def _add_contact(self, contact: WhatsAppContact) -> WhatsAppContact:
        """Add a new contact."""
        self.contacts[contact.phone_number] = contact
        logger.info(f"Added contact: {contact.phone_number}")
        return contact
    
    async def _start_conversation(self, phone_number: str) -> WhatsAppConversation:
        """Start tracking a conversation."""
        conversation = WhatsAppConversation(
            phone_number=phone_number,
            start_time=datetime.utcnow()
        )
        
        self.conversations[phone_number] = conversation
        logger.info(f"Started tracking conversation: {phone_number}")
        
        return conversation
    
    async def _end_conversation(self, phone_number: str) -> WhatsAppConversation:
        """End tracking a conversation."""
        if phone_number not in self.conversations:
            raise Exception(f"Conversation {phone_number} not found")
        
        conversation = self.conversations[phone_number]
        conversation.end_time = datetime.utcnow()
        conversation.status = "ended"
        
        logger.info(f"Ended tracking conversation: {phone_number}")
        return conversation
    
    async def _upload_media(self, file: UploadFile) -> Dict[str, Any]:
        """Upload media file to WhatsApp."""
        if not self.api_key or not self.phone_number_id:
            raise Exception("WhatsApp API not initialized")
        
        try:
            # Read file content
            content = await file.read()
            
            # Determine media type
            media_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            
            # Upload to WhatsApp
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/media",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": media_type
                    },
                    data=content
                )
                response.raise_for_status()
                result = response.json()
            
            return {
                "id": result["id"],
                "url": result.get("url"),
                "media_type": media_type,
                "filename": file.filename
            }
        
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            raise


# Create server instance
whatsapp_server = WhatsAppMCPServer()
app = whatsapp_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 