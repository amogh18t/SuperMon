from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.project import ProjectStatus, Priority

class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    priority: Priority = Field(Priority.MEDIUM, description="Project priority")
    budget: Optional[int] = Field(None, description="Project budget in cents")
    team_size: Optional[int] = Field(None, description="Expected team size")
    initialize_workflow: bool = Field(False, description="Whether to initialize SDLC workflow")
    initial_conversations: Optional[List[Dict[str, Any]]] = Field(None, description="Initial conversations for requirements")
    requirements: Optional[List[Dict[str, Any]]] = Field(None, description="Initial requirements")

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    status: Optional[ProjectStatus] = Field(None, description="Project status")
    priority: Optional[Priority] = Field(None, description="Project priority")
    budget: Optional[int] = Field(None, description="Project budget in cents")
    team_size: Optional[int] = Field(None, description="Expected team size")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    requirements_summary: Optional[str] = Field(None, description="Requirements summary")
    technical_specs: Optional[Dict[str, Any]] = Field(None, description="Technical specifications")

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    priority: Priority
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    budget: Optional[int]
    team_size: Optional[int]
    requirements_summary: Optional[str]
    technical_specs: Optional[Dict[str, Any]]
    notion_page_id: Optional[str]
    github_repo_url: Optional[str]
    slack_channel_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectWorkflowRequest(BaseModel):
    workflow_data: Dict[str, Any] = Field(..., description="Workflow configuration data")

class ProjectWorkflowResponse(BaseModel):
    project_id: int
    workflow_results: Dict[str, Any]
    executed_at: str

class EpicCreate(BaseModel):
    project_id: int = Field(..., description="Parent project ID")
    name: str = Field(..., description="Epic name")
    description: Optional[str] = Field(None, description="Epic description")
    priority: Priority = Field(Priority.MEDIUM, description="Epic priority")
    estimated_hours: Optional[int] = Field(None, description="Estimated hours")
    due_date: Optional[datetime] = Field(None, description="Due date")

class EpicUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Epic name")
    description: Optional[str] = Field(None, description="Epic description")
    priority: Optional[Priority] = Field(None, description="Epic priority")
    estimated_hours: Optional[int] = Field(None, description="Estimated hours")
    actual_hours: Optional[int] = Field(None, description="Actual hours")
    due_date: Optional[datetime] = Field(None, description="Due date")

class EpicResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    status: str
    priority: Priority
    estimated_hours: Optional[int]
    actual_hours: Optional[int]
    due_date: Optional[datetime]
    acceptance_criteria: Optional[Dict[str, Any]]
    technical_requirements: Optional[Dict[str, Any]]
    notion_page_id: Optional[str]
    github_milestone_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserStoryCreate(BaseModel):
    epic_id: int = Field(..., description="Parent epic ID")
    title: str = Field(..., description="User story title")
    description: Optional[str] = Field(None, description="User story description")
    priority: Priority = Field(Priority.MEDIUM, description="User story priority")
    story_points: Optional[int] = Field(None, description="Story points")
    estimated_hours: Optional[int] = Field(None, description="Estimated hours")

class UserStoryUpdate(BaseModel):
    title: Optional[str] = Field(None, description="User story title")
    description: Optional[str] = Field(None, description="User story description")
    status: Optional[str] = Field(None, description="User story status")
    priority: Optional[Priority] = Field(None, description="User story priority")
    story_points: Optional[int] = Field(None, description="Story points")
    estimated_hours: Optional[int] = Field(None, description="Estimated hours")
    actual_hours: Optional[int] = Field(None, description="Actual hours")
    acceptance_criteria: Optional[Dict[str, Any]] = Field(None, description="Acceptance criteria")
    technical_notes: Optional[str] = Field(None, description="Technical notes")
    test_cases: Optional[Dict[str, Any]] = Field(None, description="Test cases")

class UserStoryResponse(BaseModel):
    id: int
    epic_id: int
    title: str
    description: Optional[str]
    status: str
    priority: Priority
    story_points: Optional[int]
    estimated_hours: Optional[int]
    actual_hours: Optional[int]
    acceptance_criteria: Optional[Dict[str, Any]]
    technical_notes: Optional[str]
    test_cases: Optional[Dict[str, Any]]
    notion_page_id: Optional[str]
    github_issue_id: Optional[str]
    slack_thread_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class MeetingCreate(BaseModel):
    project_id: int = Field(..., description="Project ID")
    title: str = Field(..., description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    meeting_type: str = Field(..., description="Meeting type")
    scheduled_at: datetime = Field(..., description="Scheduled time")
    duration_minutes: int = Field(60, description="Duration in minutes")
    participants: List[Dict[str, Any]] = Field([], description="Meeting participants")

class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    meeting_type: Optional[str] = Field(None, description="Meeting type")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled time")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    summary: Optional[str] = Field(None, description="Meeting summary")
    action_items: Optional[Dict[str, Any]] = Field(None, description="Action items")
    decisions: Optional[Dict[str, Any]] = Field(None, description="Decisions made")

class MeetingResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    meeting_type: str
    scheduled_at: datetime
    duration_minutes: int
    summary: Optional[str]
    action_items: Optional[Dict[str, Any]]
    decisions: Optional[Dict[str, Any]]
    recording_url: Optional[str]
    transcription: Optional[str]
    webex_meeting_id: Optional[str]
    slack_channel_id: Optional[str]
    notion_page_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StakeholderCreate(BaseModel):
    project_id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Stakeholder name")
    email: Optional[str] = Field(None, description="Email address")
    role: str = Field(..., description="Stakeholder role")
    preferred_channel: str = Field("slack", description="Preferred communication channel")
    notification_frequency: str = Field("weekly", description="Notification frequency")

class StakeholderUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Stakeholder name")
    email: Optional[str] = Field(None, description="Email address")
    role: Optional[str] = Field(None, description="Stakeholder role")
    preferred_channel: Optional[str] = Field(None, description="Preferred communication channel")
    notification_frequency: Optional[str] = Field(None, description="Notification frequency")

class StakeholderResponse(BaseModel):
    id: int
    project_id: int
    name: str
    email: Optional[str]
    role: str
    preferred_channel: str
    notification_frequency: str
    slack_user_id: Optional[str]
    whatsapp_number: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 