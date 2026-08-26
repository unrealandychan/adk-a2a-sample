"""Agent tools with Clean Code and strict typing."""

from adk_a2a.tools.calculator import calculate
from adk_a2a.tools.todoist import (
    complete_todoist_task,
    create_todoist_task,
    exchange_todoist_code,
    get_todoist_adk_auth_objects,
    get_todoist_auth_status,
    get_todoist_auth_url,
    get_todoist_tasks,
)
from adk_a2a.tools.weather import get_city_weather

__all__ = [
    "calculate",
    "complete_todoist_task",
    "create_todoist_task",
    "exchange_todoist_code",
    "get_city_weather",
    "get_todoist_adk_auth_objects",
    "get_todoist_auth_status",
    "get_todoist_auth_url",
    "get_todoist_tasks",
]
