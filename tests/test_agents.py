"""Unit tests for agents and orchestrator."""

from adk_a2a.agents.orchestrator import create_orchestrator_agent
from adk_a2a.agents.specialized import create_calculator_agent, create_weather_agent
from adk_a2a.domain.models import AgentTask


def test_weather_agent_execution() -> None:
    """Tests Weather Analyst agent direct execution."""
    agent = create_weather_agent()
    task = AgentTask(goal="Find weather in Tokyo")
    response = agent.execute(task)

    assert response.success is True
    assert "Tokyo" in response.output
    assert response.sub_agent_name == "weather_analyst_agent"


def test_calculator_agent_execution() -> None:
    """Tests Calculator agent direct execution."""
    agent = create_calculator_agent()
    task = AgentTask(goal="calculate 25 * 4")
    response = agent.execute(task)

    assert response.success is True
    assert "100.0" in response.output
    assert response.sub_agent_name == "calculator_agent"


def test_orchestrator_multi_city_comparison() -> None:
    """Tests Orchestrator delegating and comparing multiple cities."""
    orchestrator = create_orchestrator_agent()
    task = AgentTask(goal="Compare the temperature difference between Tokyo and Paris")
    response = orchestrator.run(task)

    assert response.success is True
    assert "Multi-Agent Analysis Summary" in response.output
    assert "Tokyo" in response.output
    assert "Paris" in response.output
    assert "difference" in response.output


def test_orchestrator_single_weather_delegation() -> None:
    """Tests Orchestrator routing to weather sub-agent."""
    orchestrator = create_orchestrator_agent()
    task = AgentTask(goal="What is the weather in London?")
    response = orchestrator.run(task)

    assert response.success is True
    assert "London" in response.output
