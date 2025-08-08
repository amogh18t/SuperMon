from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class MeetingBase(BaseModel):
    title: str
    description: str
    meeting_type: str  # e.g., "standup", "planning", "retrospective"
    start_time: datetime
    end_time: datetime


class MeetingCreate(MeetingBase):
    project_id: int
    attendees: List[str]


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    meeting_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendees: Optional[List[str]] = None


class Meeting(MeetingBase):
    id: int
    project_id: int
    attendees: List[str]
    notes: Optional[str] = None
    recording_url: Optional[str] = None

    class Config:
        orm_mode = True


@router.get("/", response_model=List[Meeting])
async def read_meetings(skip: int = 0, limit: int = 100):
    """Get all meetings"""
    # Placeholder implementation
    meetings = [
        {
            "id": 1,
            "title": "Sprint Planning",
            "description": "Plan tasks for the upcoming sprint",
            "meeting_type": "planning",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "project_id": 1,
            "attendees": ["user1@example.com", "user2@example.com"],
            "notes": "Discussed priorities for the sprint",
            "recording_url": None
        },
        {
            "id": 2,
            "title": "Daily Standup",
            "description": "Daily team sync",
            "meeting_type": "standup",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "project_id": 1,
            "attendees": ["user1@example.com", "user2@example.com", "user3@example.com"],
            "notes": None,
            "recording_url": None
        }
    ]
    return meetings


@router.post("/", response_model=Meeting, status_code=status.HTTP_201_CREATED)
async def create_meeting(meeting: MeetingCreate):
    """Create a new meeting"""
    # Placeholder implementation
    return {
        "id": 3,
        **meeting.dict(),
        "notes": None,
        "recording_url": None
    }


@router.get("/{meeting_id}", response_model=Meeting)
async def read_meeting(meeting_id: int):
    """Get a specific meeting by ID"""
    # Placeholder implementation
    if meeting_id == 1:
        return {
            "id": 1,
            "title": "Sprint Planning",
            "description": "Plan tasks for the upcoming sprint",
            "meeting_type": "planning",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "project_id": 1,
            "attendees": ["user1@example.com", "user2@example.com"],
            "notes": "Discussed priorities for the sprint",
            "recording_url": None
        }
    raise HTTPException(status_code=404, detail="Meeting not found")


@router.put("/{meeting_id}", response_model=Meeting)
async def update_meeting(meeting_id: int, meeting: MeetingUpdate):
    """Update a meeting"""
    # Placeholder implementation
    if meeting_id == 1:
        return {
            "id": 1,
            "title": meeting.title or "Sprint Planning",
            "description": meeting.description or "Plan tasks for the upcoming sprint",
            "meeting_type": meeting.meeting_type or "planning",
            "start_time": meeting.start_time or datetime.now(),
            "end_time": meeting.end_time or datetime.now(),
            "project_id": 1,
            "attendees": meeting.attendees or ["user1@example.com", "user2@example.com"],
            "notes": "Discussed priorities for the sprint",
            "recording_url": None
        }
    raise HTTPException(status_code=404, detail="Meeting not found")


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(meeting_id: int):
    """Delete a meeting"""
    # Placeholder implementation
    return None