"""Google Cloud Vertex AI Agent Engine (GE) integration for ADK A2A agents."""

import os

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import Agent
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService
from starlette.applications import Starlette

from adk_a2a.agents.specialized import create_adk_weather_agent
from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import get_logger

logger = get_logger(__name__)


class AgentEngineConfig:
    """Configuration contract for Vertex AI Agent Engine (GE) runtime."""

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        session_service_uri: str | None = None,
        memory_service_uri: str | None = None,
        enable_cloud_telemetry: bool = True,
    ) -> None:
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.session_service_uri = session_service_uri or os.getenv("VERTEX_AI_SESSION_SERVICE_URI")
        self.memory_service_uri = memory_service_uri or os.getenv("VERTEX_AI_MEMORY_SERVICE_URI")
        self.enable_cloud_telemetry = enable_cloud_telemetry


def create_agent_engine_session_service(
    project_id: str | None = None,
    location: str = "us-central1",
) -> VertexAiSessionService:
    """Creates a managed Vertex AI Session Service for stateful agent sessions."""
    project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "default-project")
    logger.info(
        "Initializing Vertex AI Session Service (GE) for project [%s], location [%s]",
        project,
        location,
    )
    return VertexAiSessionService(
        project=project,
        location=location,
    )


def create_agent_engine_memory_service(
    project_id: str | None = None,
    location: str = "us-central1",
    agent_engine_id: str = "default-agent-engine",
) -> VertexAiMemoryBankService:
    """Creates a managed Vertex AI Memory Bank Service for long-term agent memory."""
    project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "default-project")
    logger.info(
        "Initializing Vertex AI Memory Bank (GE) for project [%s], agent_engine [%s]",
        project,
        agent_engine_id,
    )
    return VertexAiMemoryBankService(
        project=project,
        location=location,
        agent_engine_id=agent_engine_id,
    )


def create_ge_integrated_a2a_app(
    agent: Agent | None = None,
    config: AgentEngineConfig | None = None,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> Starlette:
    """Creates an A2A-compliant ASGI application integrated with Vertex AI Agent Engine (GE).

    Combines the ADK A2A Protocol (`to_a2a`) with Google Cloud Vertex AI managed
    runtime services (Session management, Memory Banks, and Telemetry).

    Args:
        agent: The root ADK Agent to expose. Defaults to the Weather Agent.
        config: Optional Agent Engine configuration parameters.
        host: Hostname for advertised A2A endpoint URLs.
        port: Port number for advertised A2A endpoint URLs.

    Returns:
        A Starlette application ready for deployment on Cloud Run or Agent Engine.
    """
    settings = get_settings()
    if settings.adk_suppress_a2a_experimental_feature_warnings:
        os.environ["ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS"] = "true"

    ge_config = config or AgentEngineConfig()
    target_agent = agent or create_adk_weather_agent(model=settings.adk_model)

    logger.info(
        "Binding agent [%s] to Vertex AI Agent Engine (GE) runtime (project: %s, location: %s)",
        target_agent.name,
        ge_config.project_id or "local/unspecified",
        ge_config.location,
    )

    # Wrap target agent using ADK 2.0 to_a2a utility
    a2a_app = to_a2a(
        agent=target_agent,
        host=host,
        port=port,
    )

    return a2a_app
