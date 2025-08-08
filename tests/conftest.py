"""Pytest configuration and fixtures for SuperMon tests."""

import pytest
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db) -> Generator:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("app.core.database.redis_client") as mock:
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.set.return_value = True
        yield mock


@pytest.fixture
def mock_gemini():
    """Mock Gemini API."""
    with patch("app.services.agents.requirements_agent.genai") as mock:
        mock.GenerativeModel.return_value.generate_content.return_value.text = '{"requirements": []}'
        yield mock


@pytest.fixture
def sample_project_data() -> Dict[str, Any]:
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "priority": "medium",
        "budget": 1000000,
        "team_size": 5,
        "initialize_workflow": False
    }


@pytest.fixture
def sample_conversation_data() -> Dict[str, Any]:
    """Sample conversation data for testing."""
    return {
        "channel": "test-channel",
        "participants": ["user1", "user2"],
        "messages": [
            {
                "sender": "user1",
                "content": "We need a user authentication system",
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "sender": "user2",
                "content": "Yes, with OAuth2 support",
                "timestamp": "2024-01-01T10:01:00Z"
            }
        ]
    }


@pytest.fixture
def mock_mcp_manager():
    """Mock MCP Manager."""
    with patch("app.services.agent_manager.MCPManager") as mock:
        mock_instance = Mock()
        mock_instance.initialize.return_value = None
        mock_instance.cleanup.return_value = None
        mock_instance.send_message.return_value = {"status": "sent"}
        mock_instance.get_messages.return_value = []
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_agent_manager():
    """Mock Agent Manager."""
    with patch("app.services.agent_manager.AgentManager") as mock:
        mock_instance = Mock()
        mock_instance.initialize.return_value = None
        mock_instance.cleanup.return_value = None
        mock_instance.execute_task.return_value = {"status": "completed"}
        mock_instance.execute_workflow.return_value = {"workflow": "completed"}
        mock.return_value = mock_instance
        yield mock_instance 