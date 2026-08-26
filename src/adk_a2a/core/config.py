"""Application settings and configuration management."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini / ADK Configuration
    google_api_key: str = ""
    adk_model: str = "gemini-2.5-flash"
    adk_environment: str = "development"
    log_level: str = "INFO"

    # Agent-to-Agent (A2A) Server Configuration
    a2a_server_host: str = "0.0.0.0"
    a2a_server_port: int = 8080
    a2a_server_base_url: str = "http://127.0.0.1:8080"

    # Remote A2A Agent Endpoints
    remote_weather_agent_url: str = "http://127.0.0.1:8080/.well-known/agent-card.json"
    adk_suppress_a2a_experimental_feature_warnings: bool = True


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()
