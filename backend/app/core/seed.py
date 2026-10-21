"""Initial database seeding for SuperMon."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.project import (
    Epic,
    EpicStatus,
    Meeting,
    Priority,
    Project,
    ProjectStatus,
    UserStory,
    UserStoryStatus,
)

logger = logging.getLogger(__name__)


def seed_initial_data(db: Session):
    """Seed initial projects, epics, user stories, and meetings if database is empty."""
    try:
        project_count = db.query(Project).count()
        if project_count > 0:
            logger.info(
                f"Database already has {project_count} projects, skipping seed."
            )
            return

        logger.info("🌱 Seeding initial SuperMon SDLC demo data...")

        # 1. Project 1: SuperMon Autonomous SDLC Core
        proj1 = Project(
            name="SuperMon Autonomous SDLC Core",
            description="End-to-end multi-agent software engineering platform with MCP orchestration.",
            status=ProjectStatus.IN_PROGRESS,
            priority=Priority.CRITICAL,
            github_repo_url="https://github.com/amogh18t/SuperMon",
            slack_channel_id="#eng-supermon",
            budget=5000000,
            team_size=5,
            start_date=datetime.utcnow(),
        )
        db.add(proj1)
        db.flush()

        # Epics for Project 1
        epic1 = Epic(
            project_id=proj1.id,
            name="Multi-Agent Orchestration Engine",
            description="Implement handoff protocol between Requirements, Planning, Dev, Testing, and Comms agents.",
            status=EpicStatus.IN_PROGRESS,
            priority=Priority.CRITICAL,
            estimated_hours=80,
            actual_hours=64,
        )
        epic2 = Epic(
            project_id=proj1.id,
            name="MCP Server Mesh & Resilience",
            description="Zero-downtime connection pooling for PostgreSQL, Redis, GitHub, Notion, Slack, and WhatsApp.",
            status=EpicStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            estimated_hours=60,
            actual_hours=36,
        )
        db.add_all([epic1, epic2])
        db.flush()

        # Stories for Epic 1
        s1 = UserStory(
            epic_id=epic1.id,
            title="Natural Language to Structured PRD Parser",
            description="As a Product Owner, I want raw meeting notes converted into structured epics automatically.",
            status=UserStoryStatus.DONE,
            priority=Priority.CRITICAL,
            story_points=5,
            estimated_hours=15,
            acceptance_criteria={
                "items": ["Extracts functional requirements", "Syncs to Notion MCP"]
            },
        )
        s2 = UserStory(
            epic_id=epic1.id,
            title="Automated Sprint Capacity & Story Point Estimator",
            description="Calculate velocity and assign story points using historical GitHub commit metrics.",
            status=UserStoryStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            story_points=8,
            estimated_hours=24,
            acceptance_criteria={
                "items": ["Assigns Fibonacci points", "Balances dependency graph"]
            },
        )
        s3 = UserStory(
            epic_id=epic1.id,
            title="Autonomous PR Generation & Code Review Hook",
            description="Generate feature branches and submit PRs via GitHub MCP server.",
            status=UserStoryStatus.REVIEW,
            priority=Priority.CRITICAL,
            story_points=13,
            estimated_hours=40,
            acceptance_criteria={
                "items": ["Passes ruff/flake8 lint", "Creates GitHub PR"]
            },
        )

        # Stories for Epic 2
        s4 = UserStory(
            epic_id=epic2.id,
            title="Redis Pub/Sub State Bus for Agent Locks",
            description="Prevent race conditions when multiple agents update the same User Story.",
            status=UserStoryStatus.TODO,
            priority=Priority.HIGH,
            story_points=5,
            estimated_hours=12,
            acceptance_criteria={
                "items": ["Sub-5ms lock acquisition", "Auto-TTL recovery"]
            },
        )
        s5 = UserStory(
            epic_id=epic2.id,
            title="Pytest Regression Suite Auto-Generator",
            description="Generate unit and integration tests for all FastAPI endpoints.",
            status=UserStoryStatus.TODO,
            priority=Priority.MEDIUM,
            story_points=8,
            estimated_hours=20,
            acceptance_criteria={"items": [">85% coverage", "Runs on pre-commit"]},
        )
        db.add_all([s1, s2, s3, s4, s5])

        # 2. Project 2: FinOps Real-Time Telemetry Pipeline
        proj2 = Project(
            name="FinOps Real-Time Telemetry Pipeline",
            description="High-throughput event streaming and anomaly detection microservice.",
            status=ProjectStatus.PLANNING,
            priority=Priority.HIGH,
            github_repo_url="https://github.com/amogh18t/finops-stream",
            budget=3000000,
            team_size=3,
            start_date=datetime.utcnow(),
        )
        db.add(proj2)
        db.flush()

        epic3 = Epic(
            project_id=proj2.id,
            name="Ingestion & Schema Registry",
            description="Validate incoming telemetry payloads and store aggregates in PostgreSQL.",
            status=EpicStatus.BACKLOG,
            priority=Priority.HIGH,
            estimated_hours=50,
        )
        db.add(epic3)
        db.flush()

        s6 = UserStory(
            epic_id=epic3.id,
            title="PostgreSQL Timescale Partitioning Setup",
            description="Optimize table indexing for high-frequency write workloads.",
            status=UserStoryStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            story_points=5,
            acceptance_criteria={"items": ["Partition by day", "Index on tenant_id"]},
        )
        db.add(s6)

        # 3. Meetings
        m1 = Meeting(
            project_id=proj1.id,
            title="Sprint 14 Architecture & Agent Handoff Sync",
            description="Aligned on low-latency state locking using Redis MCP and finalized acceptance criteria.",
            meeting_type="architecture",
            scheduled_at=datetime.utcnow(),
            duration_minutes=45,
            summary=(
                "Aligned on low-latency state locking using Redis MCP and finalized "
                "acceptance criteria for autonomous execution."
            ),
            action_items=[
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
        )
        m2 = Meeting(
            project_id=proj1.id,
            title="Daily Autonomous Standup Digest",
            description=(
                "Completed 18 story points across 3 epics. Zero regression failures "
                "detected in pre-commit hooks."
            ),
            meeting_type="standup",
            scheduled_at=datetime.utcnow(),
            duration_minutes=30,
            summary=(
                "Completed 18 story points across 3 epics. Zero regression failures "
                "detected in pre-commit hooks."
            ),

            action_items=[
                {
                    "id": "ai-4",
                    "text": "Generate schema migration script for meeting telemetry table",
                    "converted": False,
                    "assignee": "Development Agent",
                }
            ],
        )
        db.add_all([m1, m2])

        db.commit()
        logger.info(
            "✅ Database seeded successfully with initial projects, epics, stories, and meetings!"
        )

    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to seed initial data (non-fatal): {e}")
