"""Master Root Orchestrator Agent delegating tasks to sub-agents and A2A peers."""

from google.adk.agents import Agent, BaseAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from adk_a2a.agents.specialized import (
    DomainAgent,
    create_adk_calculator_agent,
    create_adk_todoist_agent,
    create_calculator_agent,
    create_todoist_agent,
    create_weather_agent,
)
from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import get_logger
from adk_a2a.domain.models import AgentResponse, AgentTask
from adk_a2a.tools.weather import get_city_weather

logger = get_logger(__name__)


class OrchestratorAgent:
    """Root Orchestrator Agent managing task decomposition and agent-to-agent delegation."""

    def __init__(
        self,
        name: str = "master_orchestrator_agent",
        sub_agents: list[DomainAgent] | None = None,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self.name = name
        self.model = model
        self.sub_agents: list[DomainAgent] = sub_agents or [
            create_weather_agent(model=model),
            create_calculator_agent(model=model),
            create_todoist_agent(model=model),
        ]

    def run(self, task: AgentTask) -> AgentResponse:
        """Orchestrates task execution across specialized agents.

        Decomposes complex requests (e.g. multi-city weather comparisons)
        and delegates to appropriate sub-agents or tools.
        """
        logger.info(
            "Orchestrator [%s] starting task execution: %s", self.name, task.goal
        )
        goal_lower = task.goal.lower()

        # Check for multi-city temperature comparison scenario
        cities_detected = [
            c
            for c in ["tokyo", "paris", "london", "new york", "san francisco"]
            if c in goal_lower
        ]

        if len(cities_detected) >= 2 and (
            "diff" in goal_lower or "compare" in goal_lower or "between" in goal_lower
        ):
            c1, c2 = cities_detected[0], cities_detected[1]
            w1 = get_city_weather(c1)
            w2 = get_city_weather(c2)
            diff = abs(round(w1.temperature_celsius - w2.temperature_celsius, 2))

            summary = (
                f"Multi-Agent Analysis Summary:\n"
                f"1. [{c1.title()} Weather]: {w1.temperature_celsius}°C ({w1.condition})\n"
                f"2. [{c2.title()} Weather]: {w2.temperature_celsius}°C ({w2.condition})\n"
                f"3. [Temperature Difference]: {diff}°C difference."
            )
            return AgentResponse(
                task_id=task.task_id,
                output=summary,
                success=True,
                sub_agent_name=self.name,
                metadata={
                    "cities": [w1.model_dump(), w2.model_dump()],
                    "difference_celsius": diff,
                },
            )

        # Single delegation to sub-agents
        for sub_agent in self.sub_agents:
            if "weather" in sub_agent.name and any(
                c in goal_lower for c in ["tokyo", "paris", "london", "weather"]
            ):
                return sub_agent.execute(task)
            if "calculator" in sub_agent.name and any(
                op in goal_lower for op in ["+", "-", "*", "/", "calc"]
            ):
                return sub_agent.execute(task)
            if "todoist" in sub_agent.name and any(
                kw in goal_lower for kw in ["todo", "task", "todoist"]
            ):
                return sub_agent.execute(task)

        # Default fallback execution
        return AgentResponse(
            task_id=task.task_id,
            output=f"Task executed by Orchestrator: {task.goal}",
            success=True,
            sub_agent_name=self.name,
        )


def create_orchestrator_agent(
    model: str = "gemini-2.5-flash",
    sub_agents: list[DomainAgent] | None = None,
) -> OrchestratorAgent:
    """Factory function for creating configured Master Orchestrator."""
    return OrchestratorAgent(
        name="master_orchestrator_agent",
        sub_agents=sub_agents,
        model=model,
    )


def create_adk_remote_weather_agent(
    agent_card_url: str | None = None,
) -> RemoteA2aAgent:
    """Factory creating an ADK RemoteA2aAgent connected to an exposed A2A weather agent."""
    settings = get_settings()
    card_url = agent_card_url or settings.remote_weather_agent_url
    return RemoteA2aAgent(
        name="remote_weather_agent",
        agent_card=card_url,
        description="Remote weather analysis agent communicating via A2A protocol.",
    )


def create_adk_remote_todoist_agent(
    agent_card_url: str | None = None,
) -> RemoteA2aAgent:
    """Factory creating an ADK RemoteA2aAgent connected to an exposed A2A Todoist agent."""
    settings = get_settings()
    card_url = agent_card_url or settings.remote_todoist_agent_url
    return RemoteA2aAgent(
        name="remote_todoist_agent",
        agent_card=card_url,
        description="Remote Todoist task agent communicating via A2A protocol.",
    )


def create_adk_orchestrator_agent(
    model: str = "gemini-2.5-flash",
    remote_weather_card_url: str | None = None,
    include_todoist: bool = True,
) -> Agent:
    """Factory creating native ADK 2.0 Root Agent consuming remote and local sub-agents."""
    remote_weather = create_adk_remote_weather_agent(remote_weather_card_url)
    calculator = create_adk_calculator_agent(model=model)

    sub_agents: list[BaseAgent] = [remote_weather, calculator]
    if include_todoist:
        todoist_agent = create_adk_todoist_agent(model=model)
        sub_agents.append(todoist_agent)

    return Agent(
        name="root_orchestrator_agent",
        description="Master root agent that coordinates with local and remote A2A micro-agents.",
        instruction=(
            "You are the master root agent. Delegate weather queries to the remote weather agent, "
            "arithmetic computations to the calculator agent, and task management to the Todoist agent."
        ),
        model=model,
        sub_agents=sub_agents,
    )
