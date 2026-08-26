"""Unit tests for domain models, value objects, and entities."""

import pytest
from pydantic import ValidationError

from adk_a2a.domain.models import (
    AgentCard,
    AgentResponse,
    AgentTask,
    CalculationResult,
    CityWeather,
    TaskStatus,
)


def test_city_weather_immutability() -> None:
    """Tests that CityWeather value objects are immutable."""
    weather = CityWeather(
        city="Tokyo",
        temperature_celsius=18.5,
        condition="Clear",
        humidity_percent=55,
    )
    assert weather.city == "Tokyo"
    assert weather.temperature_celsius == 18.5

    with pytest.raises(ValidationError):
        weather.temperature_celsius = 25.0


def test_calculation_result_immutability() -> None:
    """Tests that CalculationResult value objects are immutable."""
    calc = CalculationResult(expression="10 + 5", result=15.0)
    assert calc.result == 15.0

    with pytest.raises(ValidationError):
        calc.result = 20.0


def test_agent_task_creation() -> None:
    """Tests AgentTask creation and default fields."""
    task = AgentTask(goal="Check weather in Paris")
    assert task.goal == "Check weather in Paris"
    assert task.status == TaskStatus.PENDING
    assert task.task_id != ""
    assert task.correlation_id != ""


def test_agent_response_creation() -> None:
    """Tests AgentResponse model creation."""
    response = AgentResponse(
        task_id="task-123",
        output="Result output",
        success=True,
        sub_agent_name="weather_analyst_agent",
    )
    assert response.task_id == "task-123"
    assert response.success is True
    assert response.sub_agent_name == "weather_analyst_agent"


def test_agent_card_structure() -> None:
    """Tests AgentCard schema attributes."""
    card = AgentCard(
        name="test_agent",
        description="Test A2A agent description",
        version="1.0.0",
        capabilities=["weather"],
        endpoints={"agent_card": "http://localhost:8080/.well-known/agent.json"},
    )
    assert card.name == "test_agent"
    assert "weather" in card.capabilities
    assert card.endpoints["agent_card"].startswith("http")
