from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.project import Project, ProjectStatus, Priority
from app.services.agent_manager import AgentManager
from app.api.v1.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, 
    ProjectWorkflowRequest, ProjectWorkflowResponse
)

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    agent_manager: AgentManager = Depends()
):
    """Create a new project"""
    try:
        # Create project in database
        project = Project(
            name=project_data.name,
            description=project_data.description,
            status=ProjectStatus.PLANNING,
            priority=project_data.priority,
            start_date=datetime.now(),
            budget=project_data.budget,
            team_size=project_data.team_size
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Initialize project workflow if requested
        if project_data.initialize_workflow:
            workflow_data = {
                "requirements": {
                    "project_id": project.id,
                    "conversations": project_data.initial_conversations or []
                },
                "planning": {
                    "project_id": project.id,
                    "requirements": project_data.requirements or []
                }
            }
            
            workflow_results = await agent_manager.execute_workflow(project.id, workflow_data)
            
            # Update project with workflow results
            if "requirements" in workflow_results:
                project.requirements_summary = workflow_results["requirements"].get("summary", "")
            
            db.commit()
        
        return ProjectResponse.from_orm(project)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    status_filter: Optional[ProjectStatus] = None,
    priority_filter: Optional[Priority] = None,
    db: Session = Depends(get_db)
):
    """Get all projects with optional filtering"""
    query = db.query(Project)
    
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    if priority_filter:
        query = query.filter(Project.priority == priority_filter)
    
    projects = query.all()
    return [ProjectResponse.from_orm(project) for project in projects]

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse.from_orm(project)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update project fields
    for field, value in project_data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    project.updated_at = datetime.now()
    db.commit()
    db.refresh(project)
    
    return ProjectResponse.from_orm(project)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()

@router.post("/{project_id}/workflow", response_model=ProjectWorkflowResponse)
async def execute_project_workflow(
    project_id: int,
    workflow_request: ProjectWorkflowRequest,
    db: Session = Depends(get_db),
    agent_manager: AgentManager = Depends()
):
    """Execute a complete SDLC workflow for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        # Execute workflow
        workflow_results = await agent_manager.execute_workflow(project_id, workflow_request.workflow_data)
        
        # Update project status based on workflow results
        if workflow_results:
            project.status = ProjectStatus.IN_PROGRESS
            project.updated_at = datetime.now()
            db.commit()
        
        return ProjectWorkflowResponse(
            project_id=project_id,
            workflow_results=workflow_results,
            executed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )

@router.post("/{project_id}/analyze-conversations")
async def analyze_project_conversations(
    project_id: int,
    conversations: List[dict],
    db: Session = Depends(get_db),
    agent_manager: AgentManager = Depends()
):
    """Analyze conversations and extract requirements for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        # Analyze conversations
        analysis_results = await agent_manager.analyze_conversations(project_id, conversations)
        
        # Update project with requirements summary
        if "summary" in analysis_results:
            project.requirements_summary = analysis_results["summary"]
            project.updated_at = datetime.now()
            db.commit()
        
        return analysis_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation analysis failed: {str(e)}"
        )

@router.get("/{project_id}/status")
async def get_project_status(project_id: int, db: Session = Depends(get_db)):
    """Get detailed project status and metrics"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Calculate project metrics
    total_epics = len(project.epics)
    completed_epics = len([epic for epic in project.epics if epic.status.value == "done"])
    total_stories = sum(len(epic.user_stories) for epic in project.epics)
    completed_stories = sum(
        len([story for story in epic.user_stories if story.status.value == "done"])
        for epic in project.epics
    )
    
    progress_percentage = (completed_stories / total_stories * 100) if total_stories > 0 else 0
    
    return {
        "project_id": project_id,
        "name": project.name,
        "status": project.status.value,
        "progress_percentage": round(progress_percentage, 2),
        "total_epics": total_epics,
        "completed_epics": completed_epics,
        "total_stories": total_stories,
        "completed_stories": completed_stories,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None
    } 