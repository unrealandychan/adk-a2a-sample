"""Agent Card descriptor builder according to A2A protocol specifications."""

from adk_a2a.core.config import get_settings
from adk_a2a.domain.models import AgentCard


def build_agent_card() -> AgentCard:
    """Builds the standardized Agent Card for discovery by remote orchestrators."""
    settings = get_settings()
    base_url = settings.a2a_server_base_url.rstrip("/")

    return AgentCard(
        name="adk_weather_and_compute_service",
        description="A2A-compliant micro-agent providing meteorological lookup and mathematical computation.",
        version="1.0.0",
        capabilities=[
            "weather:get_city_weather",
            "math:calculate",
            "delegation:a2a_task_execution",
        ],
        endpoints={
            "agent_card": f"{base_url}/.well-known/agent.json",
            "task_execution": f"{base_url}/tasks",
            "health": f"{base_url}/healthz",
        },
    )
