"""Graph Engine (GE) multi-agent workflow topologies for ADK A2A coordination."""

from typing import Any

from google.adk.agents import Agent

from adk_a2a.agents.orchestrator import create_adk_remote_weather_agent
from adk_a2a.agents.specialized import create_adk_calculator_agent
from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import get_logger

logger = get_logger(__name__)


class GraphWorkflowState:
    """Immutable state container for Graph Engine workflow steps."""

    def __init__(
        self,
        task_id: str,
        goal: str,
        current_node: str = "start",
        results: dict[str, Any] | None = None,
    ) -> None:
        self.task_id = task_id
        self.goal = goal
        self.current_node = current_node
        self.results = results or {}


class GraphEngineCoordinator:
    """Coordinates multi-agent execution using Graph Engine topological routing."""

    def __init__(
        self,
        remote_weather_card_url: str | None = None,
        model: str = "gemini-2.5-flash",
    ) -> None:
        settings = get_settings()
        self.model = model
        self.remote_weather_agent = create_adk_remote_weather_agent(
            remote_weather_card_url or settings.remote_weather_agent_url
        )
        self.calculator_agent = create_adk_calculator_agent(model=model)
        logger.info(
            "Initialized Graph Engine (GE) Coordinator with Remote A2A [%s] and Local [%s]",
            self.remote_weather_agent.name,
            self.calculator_agent.name,
        )

    def route_task(self, goal: str) -> str:
        """Determines the initial node routing for a given user goal."""
        goal_lower = goal.lower()
        if any(c in goal_lower for c in ["weather", "temp", "tokyo", "paris", "london"]):
            return "remote_a2a_weather_node"
        if any(op in goal_lower for op in ["calc", "+", "-", "*", "/"]):
            return "local_calculator_node"
        return "root_synthesis_node"

    def execute_workflow_step(
        self,
        state: GraphWorkflowState,
    ) -> GraphWorkflowState:
        """Executes a discrete step in the Graph Engine workflow."""
        target_node = self.route_task(state.goal)
        logger.info(
            "Graph Engine routing task [%s] to node [%s]",
            state.task_id,
            target_node,
        )

        updated_results = dict(state.results)
        updated_results["routed_node"] = target_node
        updated_results["model"] = self.model

        return GraphWorkflowState(
            task_id=state.task_id,
            goal=state.goal,
            current_node=target_node,
            results=updated_results,
        )


def create_ge_graph_agent(
    model: str = "gemini-2.5-flash",
    remote_weather_card_url: str | None = None,
) -> Agent:
    """Creates a native ADK Agent orchestrated via Graph Engine (GE) principles."""
    coordinator = GraphEngineCoordinator(
        remote_weather_card_url=remote_weather_card_url,
        model=model,
    )

    return Agent(
        name="graph_engine_orchestrator",
        description="Coordinates deterministic multi-agent graphs with remote A2A micro-agents.",
        instruction=(
            "You are a Graph Engine orchestrator. Evaluate input goals, route tasks along "
            "the agent execution graph, and synthesize outputs from remote and local sub-agents."
        ),
        model=model,
        sub_agents=[coordinator.remote_weather_agent, coordinator.calculator_agent],
    )
