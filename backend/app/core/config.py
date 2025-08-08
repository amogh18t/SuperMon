"""Configuration settings for the SuperMon SDLC Automation Platform."""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    # Application Settings
    APP_NAME: str = "SuperMon SDLC Automation Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost/supermon",
        description="PostgreSQL database connection string"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection string"
    )

    # AI Services
    GEMINI_API_KEY: Optional[str] = Field(
        default=None, description="Gemini 2.5 Pro API key"
    )
    GEMINI_ENDPOINT: Optional[str] = Field(
        default=None, description="Gemini API endpoint"
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None, description="OpenAI API key"
    )
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )

    # Communication Services
    SLACK_BOT_TOKEN: Optional[str] = Field(
        default=None, description="Slack bot token"
    )
    SLACK_SIGNING_SECRET: Optional[str] = Field(
        default=None, description="Slack signing secret"
    )
    SLACK_APP_TOKEN: Optional[str] = Field(
        default=None, description="Slack app token"
    )
    SLACK_CHANNEL_ID: Optional[str] = Field(
        default=None, description="Slack channel ID"
    )

    WHATSAPP_API_KEY: Optional[str] = Field(
        default=None, description="WhatsApp Business API key"
    )
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = Field(
        default=None, description="WhatsApp phone number ID"
    )

    WEBEX_ACCESS_TOKEN: Optional[str] = Field(
        default=None, description="Webex access token"
    )
    WEBEX_BOT_TOKEN: Optional[str] = Field(
        default=None, description="Webex bot token"
    )

    # Email Settings
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")

    # Mail MCP Settings
    MAILTRAP_HOST: Optional[str] = Field(default=None, description="Mailtrap host")
    MAILTRAP_PORT: Optional[str] = Field(default=None, description="Mailtrap port")
    MAILTRAP_USERNAME: Optional[str] = Field(default=None, description="Mailtrap username")
    MAILTRAP_PASSWORD: Optional[str] = Field(default=None, description="Mailtrap password")
    FROM_EMAIL: Optional[str] = Field(default=None, description="From email address")
    EMAIL_TO: Optional[str] = Field(default=None, description="To email address")
    MAIL_MCP_ENDPOINT: Optional[str] = Field(default=None, description="Mail MCP endpoint")

    # Project Management
    NOTION_API_KEY: Optional[str] = Field(
        default=None, description="Notion API key"
    )
    NOTION_DATABASE_ID: Optional[str] = Field(
        default=None, description="Notion database ID"
    )

    GITHUB_TOKEN: Optional[str] = Field(
        default=None, description="GitHub personal access token"
    )
    GITHUB_REPO: Optional[str] = Field(
        default=None, description="GitHub repository URL"
    )

    # MCP Server Endpoints
    SLACK_MCP_ENDPOINT: str = Field(
        default="http://localhost:8001", description="Slack MCP endpoint"
    )
    WHATSAPP_MCP_ENDPOINT: str = Field(
        default="http://localhost:8002", description="WhatsApp MCP endpoint"
    )
    WEBEX_MCP_ENDPOINT: str = Field(
        default="http://localhost:8003", description="Webex MCP endpoint"
    )
    NOTION_MCP_ENDPOINT: str = Field(
        default="http://localhost:8004", description="Notion MCP endpoint"
    )
    GITHUB_MCP_ENDPOINT: str = Field(
        default="http://localhost:8005", description="GitHub MCP endpoint"
    )
    POSTGRESQL_MCP_ENDPOINT: str = Field(
        default="http://localhost:8006", description="PostgreSQL MCP endpoint"
    )
    FILESYSTEM_MCP_ENDPOINT: str = Field(
        default="http://localhost:8007", description="File system MCP endpoint"
    )
    DOCKER_MCP_ENDPOINT: str = Field(
        default="http://localhost:8008", description="Docker MCP endpoint"
    )
    REDIS_MCP_ENDPOINT: str = Field(
        default="http://localhost:8009", description="Redis MCP endpoint"
    )
    TLDV_MCP_ENDPOINT: str = Field(
        default="http://localhost:8010", description="Tl;dv MCP endpoint"
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiration time in minutes"
    )

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )

    # Agent Settings
    MAX_AGENTS: int = Field(default=10, description="Maximum number of agents")
    AGENT_TIMEOUT: int = Field(default=300, description="Agent timeout in seconds")

    # Meeting Settings
    DEFAULT_MEETING_DURATION: int = Field(
        default=60, description="Default meeting duration in minutes"
    )
    MEETING_REMINDER_MINUTES: int = Field(
        default=15, description="Meeting reminder time in minutes"
    )

    # File Upload Settings
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024, description="Maximum file size in bytes"
    )
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")

    @validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must start with postgresql:// or postgres://")
        return v

    @validator("REDIS_URL")
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL format."""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with redis://")
        return v

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    class Config:
        env_file = "../.env"
        case_sensitive = True
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()


def validate_required_settings() -> List[str]:
    """Validate required settings and return list of missing ones."""
    required_settings = [
        "GEMINI_API_KEY",
        "SLACK_BOT_TOKEN",
        "NOTION_API_KEY",
        "GITHUB_TOKEN"
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not getattr(settings, setting):
            missing_settings.append(setting)
    
    return missing_settings


def check_settings() -> None:
    """Check and warn about missing required settings."""
    missing = validate_required_settings()
    if missing:
        print(f"⚠️  Warning: Missing required settings: {', '.join(missing)}")
        print("Please set these environment variables for full functionality.")


# Validate on import
check_settings() 