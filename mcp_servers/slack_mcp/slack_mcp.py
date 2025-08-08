"""Slack MCP Server for SuperMon platform."""

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
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.async_client import AsyncSocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

logger = logging.getLogger(__name__)


class SlackMessage(BaseModel):
    """Slack message model."""
    channel: str = Field(..., description="Channel ID or name")
    text: str = Field(..., description="Message text")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp for replies")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Message attachments")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Message blocks")


class SlackChannel(BaseModel):
    """Slack channel model."""
    id: str = Field(..., description="Channel ID")
    name: str = Field(..., description="Channel name")
    is_private: bool = Field(False, description="Is private channel")
    is_archived: bool = Field(False, description="Is archived")
    member_count: int = Field(0, description="Member count")


class SlackUser(BaseModel):
    """Slack user model."""
    id: str = Field(..., description="User ID")
    name: str = Field(..., description="Username")
    real_name: Optional[str] = Field(None, description="Real name")
    email: Optional[str] = Field(None, description="Email address")
    is_bot: bool = Field(False, description="Is bot user")


class SlackConversation(BaseModel):
    """Slack conversation model."""
    channel_id: str = Field(..., description="Channel ID")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Messages")
    participants: List[str] = Field(default_factory=list, description="Participant IDs")
    start_time: datetime = Field(..., description="Conversation start time")
    end_time: Optional[datetime] = Field(None, description="Conversation end time")


class SlackMCPResponse(BaseModel):
    """Standard MCP response model."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class SlackMCPServer:
    """Slack MCP Server implementation."""
    
    def __init__(self):
        """Initialize Slack MCP Server."""
        self.app = FastAPI(title="Slack MCP Server", version="1.0.0")
        self.client: Optional[AsyncWebClient] = None
        self.socket_client: Optional[AsyncSocketModeClient] = None
        self.bot_token: Optional[str] = None
        self.app_token: Optional[str] = None
        self.channels_cache: Dict[str, SlackChannel] = {}
        self.users_cache: Dict[str, SlackUser] = {}
        self.conversations: Dict[str, SlackConversation] = {}
        
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
            """Initialize Slack client on startup."""
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
                "service": "Slack MCP Server",
                "connected": self.client is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/send-message")
        async def send_message(message: SlackMessage):
            """Send a message to a Slack channel."""
            try:
                result = await self._send_message(message)
                return SlackMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-messages/{channel_id}")
        async def get_messages(
            channel_id: str,
            limit: int = 100,
            oldest: Optional[str] = None,
            latest: Optional[str] = None
        ):
            """Get messages from a channel."""
            try:
                messages = await self._get_messages(channel_id, limit, oldest, latest)
                return SlackMCPResponse(
                    success=True,
                    data={"messages": messages},
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting messages: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/channels")
        async def get_channels():
            """Get all channels."""
            try:
                channels = await self._get_channels()
                return SlackMCPResponse(
                    success=True,
                    data={"channels": [asdict(channel) for channel in channels]},
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting channels: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/users")
        async def get_users():
            """Get all users."""
            try:
                users = await self._get_users()
                return SlackMCPResponse(
                    success=True,
                    data={"users": [asdict(user) for user in users]},
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting users: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-channel")
        async def create_channel(name: str, is_private: bool = False):
            """Create a new channel."""
            try:
                channel = await self._create_channel(name, is_private)
                return SlackMCPResponse(
                    success=True,
                    data=asdict(channel),
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating channel: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/invite-users")
        async def invite_users(channel_id: str, user_ids: List[str]):
            """Invite users to a channel."""
            try:
                result = await self._invite_users(channel_id, user_ids)
                return SlackMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error inviting users: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/start-conversation")
        async def start_conversation(channel_id: str):
            """Start tracking a conversation."""
            try:
                conversation = await self._start_conversation(channel_id)
                return SlackMCPResponse(
                    success=True,
                    data=asdict(conversation),
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error starting conversation: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/end-conversation/{conversation_id}")
        async def end_conversation(conversation_id: str):
            """End tracking a conversation."""
            try:
                conversation = await self._end_conversation(conversation_id)
                return SlackMCPResponse(
                    success=True,
                    data=asdict(conversation),
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error ending conversation: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/conversations")
        async def get_conversations():
            """Get all tracked conversations."""
            try:
                conversations = list(self.conversations.values())
                return SlackMCPResponse(
                    success=True,
                    data={"conversations": [asdict(conv) for conv in conversations]},
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting conversations: {e}")
                return SlackMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
    
    async def _initialize_client(self):
        """Initialize Slack client."""
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        
        if not self.bot_token:
            logger.warning("SLACK_BOT_TOKEN not found in environment")
            return
        
        try:
            self.client = AsyncWebClient(token=self.bot_token)
            
            # Test connection
            auth_test = await self.client.auth_test()
            logger.info(f"Connected to Slack workspace: {auth_test['team']}")
            
            # Initialize socket mode if app token is available
            if self.app_token:
                self.socket_client = AsyncSocketModeClient(
                    app_token=self.app_token,
                    web_client=self.client
                )
                await self.socket_client.start()
                logger.info("Socket mode client started")
            
            # Load initial data
            await self._load_channels()
            await self._load_users()
            
        except Exception as e:
            logger.error(f"Failed to initialize Slack client: {e}")
            self.client = None
    
    async def _cleanup(self):
        """Cleanup resources."""
        if self.socket_client:
            await self.socket_client.close()
        if self.client:
            await self.client.close()
    
    async def _send_message(self, message: SlackMessage) -> Dict[str, Any]:
        """Send a message to Slack."""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = await self.client.chat_postMessage(
                channel=message.channel,
                text=message.text,
                thread_ts=message.thread_ts,
                attachments=message.attachments,
                blocks=message.blocks
            )
            
            # Update conversation if tracking
            conversation_id = f"{message.channel}_{datetime.utcnow().strftime('%Y%m%d')}"
            if conversation_id in self.conversations:
                self.conversations[conversation_id].messages.append({
                    "ts": response["ts"],
                    "text": message.text,
                    "user": "bot",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return {
                "ts": response["ts"],
                "channel": response["channel"],
                "text": response["text"]
            }
        
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise Exception(f"Failed to send message: {e.response['error']}")
    
    async def _get_messages(
        self,
        channel_id: str,
        limit: int = 100,
        oldest: Optional[str] = None,
        latest: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a channel."""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = await self.client.conversations_history(
                channel=channel_id,
                limit=limit,
                oldest=oldest,
                latest=latest
            )
            
            messages = []
            for msg in response["messages"]:
                messages.append({
                    "ts": msg["ts"],
                    "text": msg.get("text", ""),
                    "user": msg.get("user", ""),
                    "timestamp": datetime.fromtimestamp(float(msg["ts"])).isoformat(),
                    "thread_ts": msg.get("thread_ts"),
                    "attachments": msg.get("attachments", []),
                    "blocks": msg.get("blocks", [])
                })
            
            return messages
        
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise Exception(f"Failed to get messages: {e.response['error']}")
    
    async def _get_channels(self) -> List[SlackChannel]:
        """Get all channels."""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = await self.client.conversations_list(
                types="public_channel,private_channel"
            )
            
            channels = []
            for channel_data in response["channels"]:
                channel = SlackChannel(
                    id=channel_data["id"],
                    name=channel_data["name"],
                    is_private=channel_data.get("is_private", False),
                    is_archived=channel_data.get("is_archived", False),
                    member_count=channel_data.get("num_members", 0)
                )
                channels.append(channel)
                self.channels_cache[channel.id] = channel
            
            return channels
        
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise Exception(f"Failed to get channels: {e.response['error']}")
    
    async def _get_users(self) -> List[SlackUser]:
        """Get all users."""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = await self.client.users_list()
            
            users = []
            for user_data in response["users"]:
                if not user_data.get("deleted", False):
                    user = SlackUser(
                        id=user_data["id"],
                        name=user_data["name"],
                        real_name=user_data.get("real_name"),
                        email=user_data.get("profile", {}).get("email"),
                        is_bot=user_data.get("is_bot", False)
                    )
                    users.append(user)
                    self.users_cache[user.id] = user
            
            return users
        
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise Exception(f"Failed to get users: {e.response['error']}")
    
    async def _create_channel(self, name: str, is_private: bool = False) -> SlackChannel:
        """Create a new channel."""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = await self.client.conversations_create(
                name=name,
                is_private=is_private
            )
            
            channel = SlackChannel(
                id=response["channel"]["id"],
                name=response["channel"]["name"],
                is_private=response["channel"].get("is_private", False),
                is_archived=False,
                member_count=response["channel"].get("num_members", 0)
            )
            
            self.channels_cache[channel.id] = channel
            return channel
        
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise Exception(f"Failed to create channel: {e.response['error']}")
    
    async def _invite_users(self, channel_id: str, user_ids: List[str]) -> Dict[str, Any]:
        """Invite users to a channel."""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = await self.client.conversations_invite(
                channel=channel_id,
                users=",".join(user_ids)
            )
            
            return {
                "channel_id": channel_id,
                "invited_users": user_ids,
                "ok": response["ok"]
            }
        
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise Exception(f"Failed to invite users: {e.response['error']}")
    
    async def _load_channels(self):
        """Load channels into cache."""
        try:
            await self._get_channels()
            logger.info(f"Loaded {len(self.channels_cache)} channels")
        except Exception as e:
            logger.error(f"Failed to load channels: {e}")
    
    async def _load_users(self):
        """Load users into cache."""
        try:
            await self._get_users()
            logger.info(f"Loaded {len(self.users_cache)} users")
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
    
    async def _start_conversation(self, channel_id: str) -> SlackConversation:
        """Start tracking a conversation."""
        conversation_id = f"{channel_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        conversation = SlackConversation(
            channel_id=channel_id,
            start_time=datetime.utcnow(),
            participants=[]
        )
        
        self.conversations[conversation_id] = conversation
        logger.info(f"Started tracking conversation: {conversation_id}")
        
        return conversation
    
    async def _end_conversation(self, conversation_id: str) -> SlackConversation:
        """End tracking a conversation."""
        if conversation_id not in self.conversations:
            raise Exception(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        conversation.end_time = datetime.utcnow()
        
        logger.info(f"Ended tracking conversation: {conversation_id}")
        return conversation


# Create server instance
slack_server = SlackMCPServer()
app = slack_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 