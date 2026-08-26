"""Agent Card descriptor builder according to A2A protocol specifications."""

from typing import Any

from adk_a2a.core.config import get_settings
from adk_a2a.domain.models import AgentCard


def build_agent_card() -> AgentCard:
    """Builds the standardized Agent Card for discovery by remote orchestrators."""
    settings = get_settings()
    base_url = settings.a2a_server_base_url.rstrip("/")

    return AgentCard(
        name="adk_weather_and_compute_service",
        description="A2A-compliant micro-agent providing meteorological lookup, mathematics, and Todoist tasks.",
        version="1.0.0",
        capabilities=[
            "weather:get_city_weather",
            "math:calculate",
            "todoist:manage_tasks",
            "delegation:a2a_task_execution",
        ],
        endpoints={
            "agent_card": f"{base_url}/.well-known/agent.json",
            "task_execution": f"{base_url}/tasks",
            "health": f"{base_url}/healthz",
        },
    )


def build_gemini_enterprise_agent_card(
    agent_url: str | None = None,
) -> dict[str, Any]:
    """Builds Gemini Enterprise A2A v0.3.0 compliant Agent Card dictionary.

    Conforms to the Discovery Engine A2A Agent Card specification:
    https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent
    """
    settings = get_settings()
    url = agent_url or settings.a2a_server_base_url.rstrip("/")

    return {
        "protocolVersion": "0.3.0",
        "name": "Todoist, Weather and Compute Agent",
        "description": "ADK 2.0 A2A micro-agent providing meteorological lookup, numerical calculation, and Todoist task management with OAuth 2.0.",
        "url": url,
        "version": "1.0.0",
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "capabilities": {
            "streaming": False,
        },
        "skills": [
            {
                "id": "todoist_management",
                "name": "Todoist Task Management",
                "description": "Manage user tasks, list active tasks, create new items, and complete tasks in Todoist.",
                "tags": ["productivity", "todoist", "tasks"],
                "examples": [
                    "List my todoist tasks",
                    "Create a task to review ADK architecture",
                    "Complete task 101",
                ],
            },
            {
                "id": "weather_analysis",
                "name": "Weather Analysis",
                "description": "Query global city weather conditions and temperature forecasts.",
                "tags": ["weather", "meteorology", "forecast"],
                "examples": [
                    "What is the weather in Tokyo?",
                    "Compare temperature between Paris and London",
                ],
            },
            {
                "id": "calculator",
                "name": "Calculator",
                "description": "Evaluate mathematical formulas and numerical comparisons.",
                "tags": ["math", "calculator"],
                "examples": [
                    "Calculate 25 * 4 + 10",
                    "Compute 100 / 4",
                ],
            },
        ],
    }
