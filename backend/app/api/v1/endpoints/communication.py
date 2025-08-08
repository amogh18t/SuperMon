from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from enum import Enum

router = APIRouter()


class ChannelType(str, Enum):
    SLACK = "slack"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEBEX = "webex"


class NotificationBase(BaseModel):
    channel: ChannelType
    recipients: List[str]
    subject: str
    message: str
    project_id: int


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    recipients: Optional[List[str]] = None
    subject: Optional[str] = None
    message: Optional[str] = None


class Notification(NotificationBase):
    id: str
    status: str
    sent_at: Optional[str] = None
    error: Optional[str] = None

    class Config:
        orm_mode = True


@router.get("/notifications/", response_model=List[Notification])
async def read_notifications(skip: int = 0, limit: int = 100):
    """Get all notifications"""
    # Placeholder implementation
    notifications = [
        {
            "id": "notif_1",
            "channel": "slack",
            "recipients": ["#general"],
            "subject": "Sprint Planning",
            "message": "Sprint planning meeting tomorrow at 10 AM",
            "project_id": 1,
            "status": "sent",
            "sent_at": "2023-11-15T10:00:00Z",
            "error": None
        },
        {
            "id": "notif_2",
            "channel": "email",
            "recipients": ["user1@example.com", "user2@example.com"],
            "subject": "Project Update",
            "message": "Weekly project update report",
            "project_id": 1,
            "status": "pending",
            "sent_at": None,
            "error": None
        }
    ]
    return notifications


@router.post("/notifications/", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(notification: NotificationCreate):
    """Create a new notification"""
    # Placeholder implementation
    return {
        "id": "notif_3",
        **notification.dict(),
        "status": "pending",
        "sent_at": None,
        "error": None
    }


@router.get("/notifications/{notification_id}", response_model=Notification)
async def read_notification(notification_id: str):
    """Get a specific notification by ID"""
    # Placeholder implementation
    if notification_id == "notif_1":
        return {
            "id": "notif_1",
            "channel": "slack",
            "recipients": ["#general"],
            "subject": "Sprint Planning",
            "message": "Sprint planning meeting tomorrow at 10 AM",
            "project_id": 1,
            "status": "sent",
            "sent_at": "2023-11-15T10:00:00Z",
            "error": None
        }
    raise HTTPException(status_code=404, detail="Notification not found")


@router.put("/notifications/{notification_id}", response_model=Notification)
async def update_notification(notification_id: str, notification: NotificationUpdate):
    """Update a notification"""
    # Placeholder implementation
    if notification_id == "notif_1":
        return {
            "id": "notif_1",
            "channel": "slack",
            "recipients": notification.recipients or ["#general"],
            "subject": notification.subject or "Sprint Planning",
            "message": notification.message or "Sprint planning meeting tomorrow at 10 AM",
            "project_id": 1,
            "status": "sent",
            "sent_at": "2023-11-15T10:00:00Z",
            "error": None
        }
    raise HTTPException(status_code=404, detail="Notification not found")


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: str):
    """Delete a notification"""
    # Placeholder implementation
    return None