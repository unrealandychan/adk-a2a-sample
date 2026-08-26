"""Specialized sub-agents for domain-specific tasks."""

import os
from collections.abc import Callable
from typing import Any

from google.adk.agents import Agent

from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import get_logger
from adk_a2a.domain.models import AgentResponse, AgentTask
from adk_a2a.tools.calculator import calculate
from adk_a2a.tools.todoist import (
    complete_todoist_task,
    create_todoist_task,
    get_todoist_auth_url,
    get_todoist_tasks,
)
from adk_a2a.tools.weather import get_city_weather

# Suppress ADK A2A experimental feature warnings if configured
settings = get_settings()
if settings.adk_suppress_a2a_experimental_feature_warnings:
    os.environ["ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS"] = "true"

logger = get_logger(__name__)


class DomainAgent:
    """Clean domain representation of an ADK Agent for deterministic local simulation."""

    def __init__(
        self,
        name: str,
        description: str,
        instruction: str,
        tools: list[Callable[..., Any]] | None = None,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self.name = name
        self.description = description
        self.instruction = instruction
        self.tools = tools or []
        self.model = model

    def execute(self, task: AgentTask) -> AgentResponse:
        """Executes a task assigned to this agent.

        Provides deterministic simulation / execution for testing and tooling seams.
        """
        logger.info(
            "Agent [%s] received task %s: %s", self.name, task.task_id, task.goal
        )
        goal_lower = task.goal.lower()

        # Weather Agent specialization logic
        if "weather" in self.name or any(
            t.__name__ == "get_city_weather" for t in self.tools
        ):
            for city in ["tokyo", "paris", "london", "new york", "san francisco"]:
                if city in goal_lower:
                    weather_data = get_city_weather(city)
                    output = (
                        f"Weather in {weather_data.city}: {weather_data.temperature_celsius}°C, "
                        f"{weather_data.condition}, Humidity: {weather_data.humidity_percent}%."
                    )
                    return AgentResponse(
                        task_id=task.task_id,
                        output=output,
                        success=True,
                        sub_agent_name=self.name,
                        metadata={"weather": weather_data.model_dump()},
                    )

        # Calculator Agent specialization logic
        if "calculator" in self.name or any(
            t.__name__ == "calculate" for t in self.tools
        ):
            expr = task.goal.replace("calculate", "").replace("compute", "").strip()
            if expr:
                try:
                    calc_res = calculate(expr)
                    return AgentResponse(
                        task_id=task.task_id,
                        output=f"Calculated {calc_res.expression} = {calc_res.result}",
                        success=True,
                        sub_agent_name=self.name,
                        metadata={"calculation": calc_res.model_dump()},
                    )
                except Exception as exc:
                    logger.warning("Calculation failed in agent: %s", exc)

        # Todoist Agent specialization logic
        if "todoist" in self.name or any(
            t.__name__ == "get_todoist_tasks" for t in self.tools
        ):
            if "create" in goal_lower or "add" in goal_lower:
                task_created = create_todoist_task(content=task.goal)
                return AgentResponse(
                    task_id=task.task_id,
                    output=f"Created Todoist task: {task.goal}",
                    success=True,
                    sub_agent_name=self.name,
                    metadata={"todoist": task_created},
                )
            tasks = get_todoist_tasks()
            task_titles = [f"- [{t['id']}] {t['content']}" for t in tasks]
            output_msg = (
                f"Todoist Tasks ({len(tasks)} found):\n" + "\n".join(task_titles)
            )
            return AgentResponse(
                task_id=task.task_id,
                output=output_msg,
                success=True,
                sub_agent_name=self.name,
                metadata={"todoist_tasks": tasks},
            )

        return AgentResponse(
            task_id=task.task_id,
            output=f"Agent [{self.name}] processed: {task.goal}",
            success=True,
            sub_agent_name=self.name,
        )


def create_weather_agent(model: str = "gemini-2.5-flash") -> DomainAgent:
    """Creates a dedicated Weather Analyst domain agent."""
    return DomainAgent(
        name="weather_analyst_agent",
        description="Analyzes global city meteorological data and forecasts.",
        instruction=(
            "You are a weather specialist. Retrieve and interpret temperature and weather "
            "conditions for requested locations using the get_city_weather tool."
        ),
        tools=[get_city_weather],
        model=model,
    )


def create_calculator_agent(model: str = "gemini-2.5-flash") -> DomainAgent:
    """Creates a dedicated Numerical Computation domain agent."""
    return DomainAgent(
        name="calculator_agent",
        description="Performs high-precision arithmetic computations and statistics.",
        instruction=(
            "You are a numerical computation specialist. Evaluate mathematical formulas "
            "and numerical comparisons using the calculate tool."
        ),
        tools=[calculate],
        model=model,
    )


def create_todoist_agent(model: str = "gemini-2.5-flash") -> DomainAgent:
    """Creates a dedicated Todoist domain agent."""
    return DomainAgent(
        name="todoist_agent",
        description="Manages tasks, projects, and productivity items in Todoist.",
        instruction=(
            "You are a Todoist task management specialist. Manage user tasks, list items, "
            "and complete tasks using Todoist tools."
        ),
        tools=[
            get_todoist_tasks,
            create_todoist_task,
            complete_todoist_task,
            get_todoist_auth_url,
        ],
        model=model,
    )


def create_adk_weather_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Creates a native Google ADK 2.0 Weather Agent ready for A2A exposure."""
    return Agent(
        name="weather_analyst_agent",
        description="Analyzes global city meteorological data and forecasts.",
        instruction=(
            "You are a weather specialist. Retrieve and interpret temperature and weather "
            "conditions for requested locations using the get_city_weather tool."
        ),
        tools=[get_city_weather],
        model=model,
    )


def create_adk_calculator_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Creates a native Google ADK 2.0 Calculator Agent ready for A2A exposure."""
    return Agent(
        name="calculator_agent",
        description="Performs high-precision arithmetic computations and statistics.",
        instruction=(
            "You are a numerical computation specialist. Evaluate mathematical formulas "
            "and numerical comparisons using the calculate tool."
        ),
        tools=[calculate],
        model=model,
    )


def create_adk_todoist_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Creates a native Google ADK 2.0 Todoist Agent with OAuth2 tools."""
    return Agent(
        name="todoist_agent",
        description="Manages Todoist tasks, task creation, listing, and completion with OAuth2.",
        instruction=(
            "You are a Todoist productivity specialist. Help users view active tasks, create "
            "new tasks, and mark items completed using Todoist tools."
        ),
        tools=[
            get_todoist_tasks,
            create_todoist_task,
            complete_todoist_task,
            get_todoist_auth_url,
        ],
        model=model,
    )


def create_adk_unified_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Creates a unified native ADK 2.0 Agent supporting Todoist, Weather, and Math tools."""
    return Agent(
        name="todoist_weather_agent",
        description=(
            "ADK 2.0 A2A Agent managing Todoist tasks with OAuth 2.0, weather forecasts, "
            "and numerical computations."
        ),
        instruction=(
            "You are a versatile assistant specializing in managing Todoist tasks, querying global weather "
            "data, and computing mathematical expressions. Use the corresponding tools."
        ),
        tools=[
            get_todoist_tasks,
            create_todoist_task,
            complete_todoist_task,
            get_city_weather,
            calculate,
        ],
        model=model,
    )

