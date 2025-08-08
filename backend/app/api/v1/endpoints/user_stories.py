from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class UserStoryBase(BaseModel):
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str
    status: str
    points: int


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
        orm_mode = True


@router.get("/", response_model=List[UserStory])
async def read_user_stories(skip: int = 0, limit: int = 100):
    """Get all user stories"""
    # Placeholder implementation
    user_stories = [
        {
            "id": 1,
            "title": "User Story 1",
            "description": "As a user, I want to log in with my credentials",
            "acceptance_criteria": ["Valid credentials allow login", "Invalid credentials show error"],
            "priority": "high",
            "status": "todo",
            "points": 3,
            "epic_id": 1
        },
        {
            "id": 2,
            "title": "User Story 2",
            "description": "As a user, I want to reset my password",
            "acceptance_criteria": ["Email sent with reset link", "New password can be set"],
            "priority": "medium",
            "status": "todo",
            "points": 2,
            "epic_id": 1
        }
    ]
    return user_stories


@router.post("/", response_model=UserStory, status_code=status.HTTP_201_CREATED)
async def create_user_story(user_story: UserStoryCreate):
    """Create a new user story"""
    # Placeholder implementation
    return {
        "id": 3,
        **user_story.dict()
    }


@router.get("/{user_story_id}", response_model=UserStory)
async def read_user_story(user_story_id: int):
    """Get a specific user story by ID"""
    # Placeholder implementation
    if user_story_id == 1:
        return {
            "id": 1,
            "title": "User Story 1",
            "description": "As a user, I want to log in with my credentials",
            "acceptance_criteria": ["Valid credentials allow login", "Invalid credentials show error"],
            "priority": "high",
            "status": "todo",
            "points": 3,
            "epic_id": 1
        }
    raise HTTPException(status_code=404, detail="User story not found")


@router.put("/{user_story_id}", response_model=UserStory)
async def update_user_story(user_story_id: int, user_story: UserStoryUpdate):
    """Update a user story"""
    # Placeholder implementation
    if user_story_id == 1:
        return {
            "id": 1,
            "title": user_story.title or "User Story 1",
            "description": user_story.description or "As a user, I want to log in with my credentials",
            "acceptance_criteria": user_story.acceptance_criteria or ["Valid credentials allow login", "Invalid credentials show error"],
            "priority": user_story.priority or "high",
            "status": user_story.status or "todo",
            "points": user_story.points or 3,
            "epic_id": 1
        }
    raise HTTPException(status_code=404, detail="User story not found")


@router.delete("/{user_story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_story(user_story_id: int):
    """Delete a user story"""
    # Placeholder implementation
    return None