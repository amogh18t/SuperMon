from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Epic as EpicModel
from app.models.project import EpicStatus, Priority

router = APIRouter()


class EpicBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "High"
    status: Optional[str] = "Planning"


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
        from_attributes = True


@router.get("/", response_model=List[Epic])
async def read_epics(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all epics from database."""
    query = db.query(EpicModel)
    if project_id is not None:
        query = query.filter(EpicModel.project_id == project_id)
    epics = query.offset(skip).limit(limit).all()

    if epics:
        return [
            Epic(
                id=e.id,
                project_id=e.project_id,
                title=e.name,
                description=e.description or "",
                priority=getattr(e.priority, "value", str(e.priority)).capitalize(),
                status=getattr(e.status, "value", str(e.status)).capitalize(),
            )
            for e in epics
        ]

    # Fallback
    return [
        Epic(
            id=1,
            project_id=1,
            title="Multi-Agent Orchestration Engine",
            description="Core engine",
            priority="Critical",
            status="In Progress",
        ),
        Epic(
            id=2,
            project_id=1,
            title="MCP Server Mesh & Resilience",
            description="MCP connection layer",
            priority="High",
            status="In Progress",
        ),
    ]


@router.post("/", response_model=Epic, status_code=status.HTTP_201_CREATED)
async def create_epic(epic: EpicCreate, db: Session = Depends(get_db)):
    """Create a new epic"""
    try:
        new_epic = EpicModel(
            project_id=epic.project_id,
            name=epic.title,
            description=epic.description,
            status=EpicStatus.BACKLOG,
            priority=Priority.HIGH,
        )
        db.add(new_epic)
        db.commit()
        db.refresh(new_epic)
        return Epic(
            id=new_epic.id,
            project_id=new_epic.project_id,
            title=new_epic.name,
            description=new_epic.description or "",
            priority="High",
            status="Planning",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create epic: {str(e)}")


@router.get("/{epic_id}", response_model=Epic)
async def read_epic(epic_id: int, db: Session = Depends(get_db)):
    """Get a specific epic by ID"""
    epic = db.query(EpicModel).filter(EpicModel.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    return Epic(
        id=epic.id,
        project_id=epic.project_id,
        title=epic.name,
        description=epic.description or "",
        priority=getattr(epic.priority, "value", str(epic.priority)).capitalize(),
        status=getattr(epic.status, "value", str(epic.status)).capitalize(),
    )


@router.put("/{epic_id}", response_model=Epic)
async def update_epic(
    epic_id: int, epic_update: EpicUpdate, db: Session = Depends(get_db)
):
    """Update an epic"""
    epic = db.query(EpicModel).filter(EpicModel.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    if epic_update.title is not None:
        epic.name = epic_update.title
    if epic_update.description is not None:
        epic.description = epic_update.description
    db.commit()
    db.refresh(epic)
    return Epic(
        id=epic.id,
        project_id=epic.project_id,
        title=epic.name,
        description=epic.description or "",
        priority=getattr(epic.priority, "value", str(epic.priority)).capitalize(),
        status=getattr(epic.status, "value", str(epic.status)).capitalize(),
    )


@router.delete("/{epic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_epic(epic_id: int, db: Session = Depends(get_db)):
    """Delete an epic"""
    epic = db.query(EpicModel).filter(EpicModel.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    db.delete(epic)
    db.commit()
    return None
