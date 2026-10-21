from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Epic
from app.models.project import Meeting as MeetingModel
from app.models.project import Priority, Project, UserStory, UserStoryStatus

router = APIRouter()


class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None
    meeting_type: Optional[str] = "standup"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class MeetingCreate(MeetingBase):
    project_id: int
    attendees: Optional[List[str]] = []


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    meeting_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendees: Optional[List[str]] = None


class ConvertActionItemRequest(BaseModel):
    text: str
    project_id: Optional[int] = None


@router.get("/")
async def read_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all meetings with summary and action items."""
    db_meetings = db.query(MeetingModel).offset(skip).limit(limit).all()
    if db_meetings:
        output = []
        for m in db_meetings:
            output.append(
                {
                    "id": f"mtg-{m.id}",
                    "raw_id": m.id,
                    "project_id": m.project_id,
                    "title": m.title,
                    "date": m.scheduled_at.strftime("%b %d, %I:%M %p")
                    if m.scheduled_at
                    else "Today, 10:30 AM",
                    "participants": [
                        "Amogh T.",
                        "Requirements Agent",
                        "Planning Agent",
                    ],
                    "channel": "Slack" if "Slack" in (m.title or "") else "WhatsApp",
                    "summary": m.summary
                    or m.description
                    or "Autonomous meeting intelligence summary.",
                    "action_items": m.action_items
                    or [
                        {
                            "id": f"ai-{m.id}-1",
                            "text": "Sync updated roadmap to Notion MCP",
                            "converted": False,
                            "assignee": "Requirements Agent",
                        }
                    ],
                }
            )
        return output

    # Fallback default meetings if db empty
    return [
        {
            "id": "mtg-1",
            "title": "Sprint 14 Architecture & Agent Handoff Sync",
            "date": "Today, 10:30 AM",
            "participants": ["Amogh T.", "Requirements Agent", "Planning Agent"],
            "channel": "Slack",
            "summary": (
                "Aligned on low-latency state locking using Redis MCP and finalized "
                "acceptance criteria for autonomous execution."
            ),
            "action_items": [
                {
                    "id": "ai-1",
                    "text": "Add retry backoff to WhatsApp MCP webhook dispatcher",
                    "converted": False,
                    "assignee": "Development Agent",
                },
                {
                    "id": "ai-2",
                    "text": "Benchmark PostgreSQL connection pool under 50 concurrent agent runs",
                    "converted": False,
                    "assignee": "Testing Agent",
                },
                {
                    "id": "ai-3",
                    "text": "Sync updated Epic-102 roadmap to Notion executive board",
                    "converted": True,
                    "assignee": "Requirements Agent",
                },
            ],
        },
        {
            "id": "mtg-2",
            "title": "Daily Autonomous Standup Digest",
            "date": "Yesterday, 06:00 PM",
            "participants": ["All 5 SuperMon Agents", "Engineering Lead"],
            "channel": "WhatsApp",
            "summary": (
                "Completed 18 story points across 3 epics. Zero regression failures detected "
                "in pre-commit hooks."
            ),

            "action_items": [
                {
                    "id": "ai-4",
                    "text": "Generate schema migration script for meeting telemetry table",
                    "converted": False,
                    "assignee": "Development Agent",
                }
            ],
        },
    ]


@router.post("/convert-action-item")
async def convert_action_item_to_story(
    req: ConvertActionItemRequest, db: Session = Depends(get_db)
):
    """Convert an action item from a meeting into an actionable User Story."""
    # Find project or default to first project
    project = None
    if req.project_id:
        project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        project = db.query(Project).first()

    if not project:
        raise HTTPException(
            status_code=400, detail="No active project to attach story to"
        )

    target_epic = project.epics[0] if project.epics else None
    if not target_epic:
        target_epic = Epic(
            project_id=project.id,
            name="Meeting Action Items Epic",
            description="Created automatically to hold meeting action items.",
            status=UserStoryStatus.TODO,
        )
        db.add(target_epic)
        db.flush()

    new_story = UserStory(
        epic_id=target_epic.id,
        title=req.text,
        description="Converted directly from Meeting Intelligence Action Item.",
        status=UserStoryStatus.TODO,
        priority=Priority.HIGH,
        story_points=3,
        acceptance_criteria={
            "items": ["Verified by Testing Agent", "Reviewed by Planning Agent"]
        },
    )
    db.add(new_story)
    db.commit()
    db.refresh(new_story)

    return {
        "success": True,
        "story_id": f"US-{new_story.id}",
        "title": new_story.title,
        "project_id": project.id,
        "message": f"Successfully converted to User Story US-{new_story.id} in {project.name}",
    }


@router.get("/{meeting_id}")
async def read_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Get a specific meeting by ID"""
    meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting
