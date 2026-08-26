"""Application settings and configuration management."""

import os
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
    google_genai_use_vertexai: bool = True
    google_cloud_project: str = ""
    google_cloud_region: str = "us-central1"
    google_cloud_location: str = "us-central1"
    adk_model: str = "gemini-2.5-flash"
    adk_environment: str = "development"
    log_level: str = "INFO"

    # Agent-to-Agent (A2A) Server Configuration
    a2a_server_host: str = "0.0.0.0"
    a2a_server_port: int = 8080
    a2a_server_base_url: str = "http://127.0.0.1:8080"

    # Remote A2A Agent Endpoints
    remote_weather_agent_url: str = "http://127.0.0.1:8080/.well-known/agent-card.json"
    remote_todoist_agent_url: str = "http://127.0.0.1:8080/.well-known/agent-card.json"
    adk_suppress_a2a_experimental_feature_warnings: bool = True

    # Todoist App OAuth2 Configuration
    todoist_client_id: str = "f1d3a4ec08fb4b60a61679156e2edd92"
    todoist_client_secret: str = "f1d3a4ec08fb4b60a61679156e2edd92"
    todoist_redirect_uri: str = "https://vertexaisearch.cloud.google.com/oauth-redirect"
    todoist_api_token: str = ""
    todoist_auth_url: str = "https://todoist.com/oauth/authorize"
    todoist_token_url: str = "https://todoist.com/oauth/access_token"
    todoist_scopes: str = "data:read_write,task:add"
    todoist_api_base_url: str = "https://api.todoist.com/api/v1"

    def setup_google_credentials(self) -> None:
        """Configures GenAI / ADK to use Vertex AI via Service Account / ADC when no API key is set."""
        if not self.google_api_key or self.google_genai_use_vertexai:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
            os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "true"
            if self.google_cloud_project:
                os.environ["GOOGLE_CLOUD_PROJECT"] = self.google_cloud_project
            if self.google_cloud_location or self.google_cloud_region:
                loc = self.google_cloud_location or self.google_cloud_region
                os.environ["GOOGLE_CLOUD_LOCATION"] = loc
                os.environ["VERTEX_AI_LOCATION"] = loc


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    settings = Settings()
    settings.setup_google_credentials()
    return settings
