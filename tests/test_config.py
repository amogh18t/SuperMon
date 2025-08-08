"""Tests for configuration settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, validate_required_settings, check_settings


class TestSettings:
    """Test cases for Settings class."""

    def test_default_settings(self):
        """Test that default settings are properly set."""
        settings = Settings()
        
        assert settings.APP_NAME == "SuperMon SDLC Automation Platform"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is False
        assert settings.DATABASE_URL == "postgresql://user:password@localhost/supermon"
        assert settings.REDIS_URL == "redis://localhost:6379"

    def test_database_url_validation(self):
        """Test database URL validation."""
        # Valid URLs
        valid_urls = [
            "postgresql://user:pass@localhost/db",
            "postgres://user:pass@localhost/db",
        ]
        
        for url in valid_urls:
            settings = Settings(DATABASE_URL=url)
            assert settings.DATABASE_URL == url

        # Invalid URLs
        invalid_urls = [
            "mysql://user:pass@localhost/db",
            "http://localhost/db",
            "invalid-url",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                Settings(DATABASE_URL=url)

    def test_redis_url_validation(self):
        """Test Redis URL validation."""
        # Valid URL
        settings = Settings(REDIS_URL="redis://localhost:6379")
        assert settings.REDIS_URL == "redis://localhost:6379"

        # Invalid URL
        with pytest.raises(ValidationError):
            Settings(REDIS_URL="http://localhost:6379")

    def test_secret_key_validation(self):
        """Test secret key validation."""
        # Valid key (32+ characters)
        valid_key = "a" * 32
        settings = Settings(SECRET_KEY=valid_key)
        assert settings.SECRET_KEY == valid_key

        # Invalid key (too short)
        with pytest.raises(ValidationError):
            Settings(SECRET_KEY="short")

    def test_optional_settings(self):
        """Test that optional settings can be None."""
        settings = Settings(
            GEMINI_API_KEY=None,
            SLACK_BOT_TOKEN=None,
            NOTION_API_KEY=None,
            GITHUB_TOKEN=None
        )
        
        assert settings.GEMINI_API_KEY is None
        assert settings.SLACK_BOT_TOKEN is None
        assert settings.NOTION_API_KEY is None
        assert settings.GITHUB_TOKEN is None

    def test_cors_origins(self):
        """Test CORS origins configuration."""
        custom_origins = ["http://example.com", "https://app.example.com"]
        settings = Settings(ALLOWED_ORIGINS=custom_origins)
        
        assert settings.ALLOWED_ORIGINS == custom_origins

    def test_agent_settings(self):
        """Test agent-related settings."""
        settings = Settings(MAX_AGENTS=20, AGENT_TIMEOUT=600)
        
        assert settings.MAX_AGENTS == 20
        assert settings.AGENT_TIMEOUT == 600

    def test_meeting_settings(self):
        """Test meeting-related settings."""
        settings = Settings(
            DEFAULT_MEETING_DURATION=90,
            MEETING_REMINDER_MINUTES=30
        )
        
        assert settings.DEFAULT_MEETING_DURATION == 90
        assert settings.MEETING_REMINDER_MINUTES == 30

    def test_file_upload_settings(self):
        """Test file upload settings."""
        settings = Settings(
            MAX_FILE_SIZE=20 * 1024 * 1024,  # 20MB
            UPLOAD_DIR="custom_uploads"
        )
        
        assert settings.MAX_FILE_SIZE == 20 * 1024 * 1024
        assert settings.UPLOAD_DIR == "custom_uploads"


class TestSettingsValidation:
    """Test cases for settings validation functions."""

    def test_validate_required_settings_all_present(self):
        """Test validation when all required settings are present."""
        with pytest.MonkeyPatch().context() as m:
            m.setenv("GEMINI_API_KEY", "test_key")
            m.setenv("SLACK_BOT_TOKEN", "test_token")
            m.setenv("NOTION_API_KEY", "test_notion")
            m.setenv("GITHUB_TOKEN", "test_github")
            
            missing = validate_required_settings()
            assert missing == []

    def test_validate_required_settings_missing(self):
        """Test validation when some required settings are missing."""
        with pytest.MonkeyPatch().context() as m:
            m.setenv("GEMINI_API_KEY", "test_key")
            # Missing other required settings
            
            missing = validate_required_settings()
            assert "SLACK_BOT_TOKEN" in missing
            assert "NOTION_API_KEY" in missing
            assert "GITHUB_TOKEN" in missing
            assert len(missing) == 3

    def test_check_settings_with_missing(self, capsys):
        """Test check_settings function with missing settings."""
        with pytest.MonkeyPatch().context() as m:
            m.setenv("GEMINI_API_KEY", "test_key")
            # Missing other required settings
            
            check_settings()
            captured = capsys.readouterr()
            
            assert "Warning: Missing required settings" in captured.out
            assert "SLACK_BOT_TOKEN" in captured.out
            assert "NOTION_API_KEY" in captured.out
            assert "GITHUB_TOKEN" in captured.out

    def test_check_settings_all_present(self, capsys):
        """Test check_settings function when all settings are present."""
        with pytest.MonkeyPatch().context() as m:
            m.setenv("GEMINI_API_KEY", "test_key")
            m.setenv("SLACK_BOT_TOKEN", "test_token")
            m.setenv("NOTION_API_KEY", "test_notion")
            m.setenv("GITHUB_TOKEN", "test_github")
            
            check_settings()
            captured = capsys.readouterr()
            
            assert "Warning: Missing required settings" not in captured.out


class TestSettingsIntegration:
    """Integration tests for settings."""

    def test_settings_from_env_file(self, tmp_path):
        """Test loading settings from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GEMINI_API_KEY=test_gemini_key
SLACK_BOT_TOKEN=test_slack_token
NOTION_API_KEY=test_notion_key
GITHUB_TOKEN=test_github_token
DATABASE_URL=postgresql://test:test@localhost/testdb
REDIS_URL=redis://localhost:6379
DEBUG=true
        """)
        
        # Temporarily change working directory to tmp_path
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            settings = Settings()
            assert settings.GEMINI_API_KEY == "test_gemini_key"
            assert settings.SLACK_BOT_TOKEN == "test_slack_token"
            assert settings.NOTION_API_KEY == "test_notion_key"
            assert settings.GITHUB_TOKEN == "test_github_token"
            assert settings.DATABASE_URL == "postgresql://test:test@localhost/testdb"
            assert settings.REDIS_URL == "redis://localhost:6379"
            assert settings.DEBUG is True
        finally:
            os.chdir(original_cwd)

    def test_settings_case_sensitive(self):
        """Test that settings are case sensitive."""
        settings = Settings()
        
        # These should be different
        assert settings.APP_NAME != settings.APP_NAME.lower()
        assert settings.APP_VERSION != settings.APP_VERSION.upper() 