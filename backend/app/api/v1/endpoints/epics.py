from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class EpicBase(BaseModel):
    title: str
    description: str
    priority: str
    status: str


class EpicCreate(EpicBase):
    project_id: int


class EpicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class Epic(EpicBase):
    id: int
    project_id: int

    class Config:
        orm_mode = True


@router.get("/", response_model=List[Epic])
async def read_epics(skip: int = 0, limit: int = 100):
    """Get all epics"""
    # Placeholder implementation
    epics = [
        {
            "id": 1,
            "title": "Epic 1: User Authentication",
            "description": "Implement user authentication system",
            "priority": "high",
            "status": "todo",
            "project_id": 1
        },
        {
            "id": 2,
            "title": "Epic 2: Dashboard",
            "description": "Create main dashboard interface",
            "priority": "medium",
            "status": "todo",
            "project_id": 1
        }
    ]
    return epics


@router.post("/", response_model=Epic, status_code=status.HTTP_201_CREATED)
async def create_epic(epic: EpicCreate):
    """Create a new epic"""
    # Placeholder implementation
    return {
        "id": 3,
        **epic.dict()
    }


@router.get("/{epic_id}", response_model=Epic)
async def read_epic(epic_id: int):
    """Get a specific epic by ID"""
    # Placeholder implementation
    if epic_id == 1:
        return {
            "id": 1,
            "title": "Epic 1: User Authentication",
            "description": "Implement user authentication system",
            "priority": "high",
            "status": "todo",
            "project_id": 1
        }
    raise HTTPException(status_code=404, detail="Epic not found")


@router.put("/{epic_id}", response_model=Epic)
async def update_epic(epic_id: int, epic: EpicUpdate):
    """Update an epic"""
    # Placeholder implementation
    if epic_id == 1:
        return {
            "id": 1,
            "title": epic.title or "Epic 1: User Authentication",
            "description": epic.description or "Implement user authentication system",
            "priority": epic.priority or "high",
            "status": epic.status or "todo",
            "project_id": 1
        }
    raise HTTPException(status_code=404, detail="Epic not found")


@router.delete("/{epic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_epic(epic_id: int):
    """Delete an epic"""
    # Placeholder implementation
    return None