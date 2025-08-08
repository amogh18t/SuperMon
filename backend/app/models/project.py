from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime
from typing import Optional

class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class EpicStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class UserStoryStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    
    # Project metadata
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime)
    budget = Column(Integer)  # in cents
    team_size = Column(Integer)
    
    # External IDs
    notion_page_id = Column(String(255))
    github_repo_url = Column(String(500))
    slack_channel_id = Column(String(255))
    
    # AI generated content
    requirements_summary = Column(Text)
    technical_specs = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    epics = relationship("Epic", back_populates="project", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="project", cascade="all, delete-orphan")
    stakeholders = relationship("Stakeholder", back_populates="project", cascade="all, delete-orphan")

class Epic(Base):
    __tablename__ = "epics"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(EpicStatus), default=EpicStatus.BACKLOG)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    
    # Epic metadata
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    due_date = Column(DateTime)
    
    # External IDs
    notion_page_id = Column(String(255))
    github_milestone_id = Column(String(255))
    
    # AI generated content
    acceptance_criteria = Column(JSON)
    technical_requirements = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="epics")
    user_stories = relationship("UserStory", back_populates="epic", cascade="all, delete-orphan")

class UserStory(Base):
    __tablename__ = "user_stories"
    
    id = Column(Integer, primary_key=True, index=True)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(UserStoryStatus), default=UserStoryStatus.TODO)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    
    # Story points and time tracking
    story_points = Column(Integer)
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    
    # External IDs
    notion_page_id = Column(String(255))
    github_issue_id = Column(String(255))
    slack_thread_id = Column(String(255))
    
    # AI generated content
    acceptance_criteria = Column(JSON)
    technical_notes = Column(Text)
    test_cases = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    epic = relationship("Epic", back_populates="user_stories")
    tasks = relationship("Task", back_populates="user_story", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_story_id = Column(Integer, ForeignKey("user_stories.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(UserStoryStatus), default=UserStoryStatus.TODO)
    
    # Time tracking
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    
    # External IDs
    notion_page_id = Column(String(255))
    github_issue_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    user_story = relationship("UserStory", back_populates="tasks")

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Meeting details
    meeting_type = Column(String(100))  # requirements, planning, review, etc.
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # External IDs
    webex_meeting_id = Column(String(255))
    slack_channel_id = Column(String(255))
    notion_page_id = Column(String(255))
    
    # Meeting outcomes
    summary = Column(Text)
    action_items = Column(JSON)
    decisions = Column(JSON)
    
    # Recording
    recording_url = Column(String(500))
    transcription = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="meetings")
    participants = relationship("MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan")

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(100))  # stakeholder, developer, manager, etc.
    
    # External IDs
    slack_user_id = Column(String(255))
    webex_user_id = Column(String(255))
    
    # Attendance
    confirmed = Column(Boolean, default=False)
    attended = Column(Boolean)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    meeting = relationship("Meeting", back_populates="participants")

class Stakeholder(Base):
    __tablename__ = "stakeholders"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(100))  # product owner, business analyst, etc.
    
    # Communication preferences
    preferred_channel = Column(String(50))  # slack, whatsapp, email
    notification_frequency = Column(String(50))  # daily, weekly, on-demand
    
    # External IDs
    slack_user_id = Column(String(255))
    whatsapp_number = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="stakeholders")

class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    channel = Column(String(50))  # slack, whatsapp, webex, email
    message_type = Column(String(50))  # message, notification, summary
    
    # Message content
    sender = Column(String(255))
    recipient = Column(String(255))
    content = Column(Text)
    
    # External IDs
    external_message_id = Column(String(255))
    thread_id = Column(String(255))
    
    # AI processing
    sentiment = Column(String(50))  # positive, negative, neutral
    requirements_extracted = Column(JSON)
    action_items = Column(JSON)
    
    # Timestamps
    sent_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime)
    
    # Relationships
    project_id = Column(Integer, ForeignKey("projects.id")) 