"""Tests for Google Cloud Vertex AI Agent Engine (GE) and Graph Engine integrations."""

from starlette.testclient import TestClient

from adk_a2a.integrations.agent_engine import (
    AgentEngineConfig,
    create_agent_engine_memory_service,
    create_agent_engine_session_service,
    create_ge_integrated_a2a_app,
)
from adk_a2a.integrations.graph_engine import (
    GraphEngineCoordinator,
    GraphWorkflowState,
    create_ge_graph_agent,
)


def test_agent_engine_config_defaults() -> None:
    """Tests AgentEngineConfig default initialization."""
    config = AgentEngineConfig(project_id="test-project", location="us-central1")
    assert config.project_id == "test-project"
    assert config.location == "us-central1"
    assert config.enable_cloud_telemetry is True


def test_agent_engine_services_initialization() -> None:
    """Tests initializing Vertex AI Session and Memory Bank services."""
    session_svc = create_agent_engine_session_service(
        project_id="test-project",
        location="us-central1",
    )
    assert session_svc is not None

    memory_svc = create_agent_engine_memory_service(
        project_id="test-project",
        location="us-central1",
        agent_engine_id="test-agent-engine",
    )
    assert memory_svc is not None


def test_ge_integrated_a2a_app_exposure() -> None:
    """Tests creating and exposing an A2A app integrated with Agent Engine (GE)."""
    config = AgentEngineConfig(project_id="test-proj")
    app = create_ge_integrated_a2a_app(config=config, port=8080)

    with TestClient(app) as client:
        response = client.get("/.well-known/agent-card.json")
        assert response.status_code == 200
        card = response.json()
        assert card["name"] == "weather_analyst_agent"
        assert "skills" in card


def test_graph_engine_routing_logic() -> None:
    """Tests Graph Engine workflow state transitions and task routing."""
    coordinator = GraphEngineCoordinator(
        remote_weather_card_url="http://localhost:8080/.well-known/agent-card.json"
    )

    # Route weather goal
    weather_route = coordinator.route_task("Check temperature in Tokyo")
    assert weather_route == "remote_a2a_weather_node"

    # Route calculation goal
    calc_route = coordinator.route_task("calc 100 * 20")
    assert calc_route == "local_calculator_node"

    # Route general goal
    general_route = coordinator.route_task("General greeting")
    assert general_route == "root_synthesis_node"


def test_graph_engine_workflow_step_execution() -> None:
    """Tests discrete step execution in Graph Engine."""
    coordinator = GraphEngineCoordinator(
        remote_weather_card_url="http://localhost:8080/.well-known/agent-card.json"
    )

    initial_state = GraphWorkflowState(
        task_id="task-123",
        goal="What is the weather in Paris?",
    )

    next_state = coordinator.execute_workflow_step(initial_state)
    assert next_state.current_node == "remote_a2a_weather_node"
    assert next_state.results["routed_node"] == "remote_a2a_weather_node"


def test_create_ge_graph_agent() -> None:
    """Tests factory creating native Graph Engine agent with A2A sub-agents."""
    agent = create_ge_graph_agent(
        remote_weather_card_url="http://localhost:8080/.well-known/agent-card.json"
    )
    assert agent.name == "graph_engine_orchestrator"
    assert len(agent.sub_agents) == 2

