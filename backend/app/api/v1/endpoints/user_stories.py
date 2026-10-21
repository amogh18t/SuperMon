from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Priority
from app.models.project import UserStory as UserStoryModel
from app.models.project import UserStoryStatus

router = APIRouter()


class UserStoryBase(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = []
    priority: str = "High"
    status: str = "Ready"
    points: Optional[int] = 5


class UserStoryCreate(UserStoryBase):
    epic_id: int


class UserStoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    points: Optional[int] = None


class UserStory(UserStoryBase):
    id: int
    epic_id: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserStory])
async def read_user_stories(
    epic_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all user stories from database."""
    query = db.query(UserStoryModel)
    if epic_id is not None:
        query = query.filter(UserStoryModel.epic_id == epic_id)
    stories = query.offset(skip).limit(limit).all()

    result = []
    for s in stories:
        st_val = s.status.value if hasattr(s.status, "value") else str(s.status)
        pri_val = s.priority.value if hasattr(s.priority, "value") else str(s.priority)
        ac = (
            s.acceptance_criteria.get("items", [])
            if isinstance(s.acceptance_criteria, dict)
            else (
                s.acceptance_criteria if isinstance(s.acceptance_criteria, list) else []
            )
        )
        result.append(
            UserStory(
                id=s.id,
                epic_id=s.epic_id,
                title=s.title,
                description=s.description or "",
                acceptance_criteria=ac,
                priority=pri_val.capitalize() if pri_val else "High",
                status=st_val,
                points=s.story_points or 5,
            )
        )
    return result


@router.post("/", response_model=UserStory, status_code=status.HTTP_201_CREATED)
async def create_user_story(user_story: UserStoryCreate, db: Session = Depends(get_db)):
    """Create a new user story in the database."""
    try:
        new_story = UserStoryModel(
            epic_id=user_story.epic_id,
            title=user_story.title,
            description=user_story.description,
            status=UserStoryStatus.TODO,
            priority=Priority.HIGH,
            story_points=user_story.points or 5,
            acceptance_criteria={"items": user_story.acceptance_criteria or []},
        )
        db.add(new_story)
        db.commit()
        db.refresh(new_story)

        return UserStory(
            id=new_story.id,
            epic_id=new_story.epic_id,
            title=new_story.title,
            description=new_story.description or "",
            acceptance_criteria=user_story.acceptance_criteria or [],
            priority="High",
            status="Ready",
            points=new_story.story_points,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create story: {str(e)}")


@router.put("/{user_story_id}")
async def update_user_story(
    user_story_id: int, story_update: UserStoryUpdate, db: Session = Depends(get_db)
):
    """Update a user story status or details."""
    story = db.query(UserStoryModel).filter(UserStoryModel.id == user_story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="User story not found")

    if story_update.title is not None:
        story.title = story_update.title
    if story_update.description is not None:
        story.description = story_update.description
    if story_update.points is not None:
        story.story_points = story_update.points
    if story_update.status is not None:
        status_map = {
            "backlog": UserStoryStatus.TODO,
            "ready": UserStoryStatus.TODO,
            "in progress": UserStoryStatus.IN_PROGRESS,
            "testing": UserStoryStatus.REVIEW,
            "done": UserStoryStatus.DONE,
        }
        mapped = status_map.get(
            story_update.status.lower(), UserStoryStatus.IN_PROGRESS
        )
        story.status = mapped
        if mapped == UserStoryStatus.DONE:
            story.completed_at = datetime.utcnow()

    story.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(story)

    return {
        "success": True,
        "id": story.id,
        "title": story.title,
        "status": getattr(story.status, "value", str(story.status)),
    }


@router.delete("/{user_story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_story(user_story_id: int, db: Session = Depends(get_db)):
    """Delete a user story"""
    story = db.query(UserStoryModel).filter(UserStoryModel.id == user_story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="User story not found")
    db.delete(story)
    db.commit()
    return None
