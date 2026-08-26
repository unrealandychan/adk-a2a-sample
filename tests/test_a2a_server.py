"""Integration tests for A2A server, to_a2a() wrapper, and client adapters."""

import httpx
import pytest
from starlette.testclient import TestClient

from adk_a2a.a2a.server import create_a2a_app, expose_agent_via_to_a2a
from adk_a2a.agents.orchestrator import create_adk_remote_weather_agent
from adk_a2a.agents.specialized import create_adk_weather_agent
from adk_a2a.domain.models import AgentTask


@pytest.mark.asyncio
async def test_a2a_health_endpoint() -> None:
    """Tests the /healthz endpoint."""
    app = create_a2a_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data


@pytest.mark.asyncio
async def test_a2a_agent_card_endpoint() -> None:
    """Tests the /.well-known/agent.json A2A discovery endpoint."""
    app = create_a2a_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/.well-known/agent.json")
        assert response.status_code == 200
        card_data = response.json()
        assert card_data["name"] == "adk_weather_and_compute_service"
        assert len(card_data["capabilities"]) > 0
        assert "endpoints" in card_data


@pytest.mark.asyncio
async def test_a2a_task_execution_endpoint() -> None:
    """Tests the /tasks POST endpoint for executing remote workloads."""
    app = create_a2a_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        task = AgentTask(goal="Check weather in Tokyo")
        response = await client.post("/tasks", json=task.model_dump())
        assert response.status_code == 200
        resp_data = response.json()
        assert resp_data["success"] is True
        assert "Tokyo" in resp_data["output"]


def test_to_a2a_exposure_agent_card() -> None:
    """Tests exposing an ADK Agent using to_a2a() and retrieving its auto-generated agent card."""
    adk_agent = create_adk_weather_agent()
    a2a_starlette_app = expose_agent_via_to_a2a(agent=adk_agent, port=8080)

    with TestClient(a2a_starlette_app) as client:
        response = client.get("/.well-known/agent-card.json")
        assert response.status_code == 200
        card = response.json()
        assert card["name"] == "weather_analyst_agent"
        assert "skills" in card
        assert any(skill.get("name") == "get_city_weather" for skill in card["skills"])


def test_remote_a2a_agent_creation() -> None:
    """Tests instantiating an ADK RemoteA2aAgent referencing the agent card URL."""
    remote_agent = create_adk_remote_weather_agent(
        "http://localhost:8080/.well-known/agent-card.json"
    )
    assert remote_agent.name == "remote_weather_agent"
    assert "agent-card.json" in str(remote_agent._agent_card_source)
