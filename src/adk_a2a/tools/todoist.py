"""Todoist custom tool and OAuth 2.0 integration for Google ADK 2.0."""

import contextvars
import json
import urllib.parse
import uuid
from typing import Any

import httpx
from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows
from google.adk.auth.auth_credential import (
    AuthCredential,
    AuthCredentialTypes,
    OAuth2Auth,
)

from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import get_logger
from adk_a2a.domain.exceptions import ToolExecutionError
from adk_a2a.domain.models import TodoistAuthStatus, TodoistTask

logger = get_logger(__name__)

# Request-scoped ContextVar to hold incoming OAuth2 Bearer token from Gemini Enterprise / A2A proxy
_current_todoist_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_current_todoist_token", default=None
)


def set_current_todoist_token(token: str | None) -> None:
    """Sets the active request's Todoist OAuth2 Bearer token in the execution context."""
    _current_todoist_token.set(token)


def get_effective_todoist_token(explicit_token: str | None = None) -> str | None:
    """Retrieves the effective Todoist API token from explicit arg, request context, or settings."""
    if explicit_token:
        return explicit_token.strip()
    ctx_token = _current_todoist_token.get()
    if ctx_token:
        if ctx_token.lower().startswith("bearer "):
            return ctx_token[7:].strip()
        return ctx_token.strip()
    settings = get_settings()
    return settings.todoist_api_token or None


def get_todoist_adk_auth_objects() -> tuple[OAuth2, AuthCredential]:
    """Builds standard Google ADK OAuth2 scheme and credential models for Todoist."""
    settings = get_settings()

    auth_scheme = OAuth2(
        flows=OAuthFlows(
            authorizationCode=OAuthFlowAuthorizationCode(
                authorizationUrl=settings.todoist_auth_url,
                tokenUrl=settings.todoist_token_url,
                scopes={"data:read_write": "Full read/write access to Todoist tasks"},
            )
        )
    )

    auth_credential = AuthCredential(
        auth_type=AuthCredentialTypes.OAUTH2,
        oauth2=OAuth2Auth(
            client_id=settings.todoist_client_id,
            client_secret=settings.todoist_client_secret,
            redirect_uri=settings.todoist_redirect_uri,
        ),
    )

    return auth_scheme, auth_credential


def get_todoist_auth_url(state: str | None = None) -> str:
    """Generates the OAuth2 Authorization URL to initiate user login and consent."""
    settings = get_settings()
    params = {
        "client_id": settings.todoist_client_id,
        "scope": settings.todoist_scopes,
        "state": state or "adk_todoist_auth_state",
    }
    encoded_params = urllib.parse.urlencode(params)
    return f"{settings.todoist_auth_url}?{encoded_params}"


def get_todoist_auth_status() -> TodoistAuthStatus:
    """Returns current Todoist OAuth2 authentication configuration and status."""
    settings = get_settings()
    effective_token = get_effective_todoist_token()
    has_token = bool(effective_token)
    return TodoistAuthStatus(
        is_authenticated=has_token,
        access_token_present=has_token,
        client_id=settings.todoist_client_id,
        redirect_uri=settings.todoist_redirect_uri,
        auth_url=get_todoist_auth_url(),
    )


def exchange_todoist_code(
    code: str,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> dict[str, Any]:
    """Exchanges an authorization code for an OAuth2 access token with Todoist."""
    settings = get_settings()
    c_id = client_id or settings.todoist_client_id
    c_secret = client_secret or settings.todoist_client_secret

    payload = {
        "client_id": c_id,
        "client_secret": c_secret,
        "code": code,
        "redirect_uri": settings.todoist_redirect_uri,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(settings.todoist_token_url, data=payload)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.info("Successfully exchanged Todoist OAuth2 authorization code.")
            return data
    except Exception as exc:
        logger.error("Failed to exchange Todoist OAuth authorization code: %s", exc)
        raise ToolExecutionError(f"Failed to exchange Todoist OAuth2 code: {exc}") from exc


def get_todoist_tasks(
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieves active tasks from Todoist API v1.

    Args:
        project_id: Optional project ID to filter tasks.

    Returns:
        List of Todoist task items.
    """
    settings = get_settings()
    token = get_effective_todoist_token()

    if not token:
        logger.warning(
            "No Todoist OAuth token present in request context; returning simulated workspace tasks."
        )
        return [
            TodoistTask(
                id="task-101",
                content="Review ADK 2.0 A2A architecture",
                is_completed=False,
                due_date="2026-08-27",
                priority=4,
                project_id=project_id or "proj-default",
                url="https://todoist.com/app/task/task-101",
            ).model_dump(),
            TodoistTask(
                id="task-102",
                content="Deploy micro-agents to Vertex AI Agent Engine",
                is_completed=False,
                due_date="2026-08-28",
                priority=3,
                project_id=project_id or "proj-default",
                url="https://todoist.com/app/task/task-102",
            ).model_dump(),
        ]

    headers = {"Authorization": f"Bearer {token}"}
    params: dict[str, str] = {}
    if project_id:
        params["project_id"] = project_id

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{settings.todoist_api_base_url}/tasks",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "results" in data:
                tasks: list[dict[str, Any]] = data["results"]
            elif isinstance(data, list):
                tasks = data
            else:
                tasks = []
            return tasks
    except Exception as exc:
        logger.error("Error fetching Todoist tasks: %s", exc)
        raise ToolExecutionError(f"Failed to fetch Todoist tasks: {exc}") from exc


def create_todoist_task(
    content: str,
    due_string: str | None = None,
    priority: int = 1,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Creates a new task in Todoist.

    Args:
        content: The text description or title of the task.
        due_string: Optional due date in human readable format (e.g. 'today', 'tomorrow at 5pm').
        priority: Task priority from 1 (normal) to 4 (urgent).
        project_id: Optional project ID to place the task into.

    Returns:
        Dictionary containing task creation status and task details.
    """
    if not content.strip():
        raise ToolExecutionError("Task content cannot be empty.")

    settings = get_settings()
    token = get_effective_todoist_token()

    if not token:
        logger.info("Simulating task creation in sandbox mode for content: %s", content)
        simulated_task = TodoistTask(
            id="simulated-task-999",
            content=content,
            is_completed=False,
            due_date=due_string or "today",
            priority=priority,
            project_id=project_id or "inbox",
            url="https://todoist.com/app/task/simulated-task-999",
        )
        return {
            "status": "created (simulated)",
            "task": simulated_task.model_dump(),
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "content": content,
        "priority": priority,
    }
    if due_string:
        payload["due_string"] = due_string
    if project_id:
        payload["project_id"] = project_id

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{settings.todoist_api_base_url}/tasks",
                headers=headers,
                content=json.dumps(payload),
            )
            response.raise_for_status()
            created_task: dict[str, Any] = response.json()
            return {"status": "created", "task": created_task}
    except Exception as exc:
        logger.error("Error creating Todoist task: %s", exc)
        raise ToolExecutionError(f"Failed to create Todoist task: {exc}") from exc


def complete_todoist_task(
    task_id: str,
) -> dict[str, Any]:
    """Closes and completes an active task in Todoist.

    Args:
        task_id: The unique ID of the Todoist task to mark as completed.

    Returns:
        Dictionary containing completion status and success flag.
    """
    if not task_id.strip():
        raise ToolExecutionError("Task ID cannot be empty.")

    settings = get_settings()
    token = get_effective_todoist_token()

    if not token:
        logger.info("Simulating task completion in sandbox mode for task_id: %s", task_id)
        return {
            "status": "completed (simulated)",
            "task_id": task_id,
            "success": True,
        }

    sync_payload = {
        "commands": [
            {
                "type": "item_close",
                "uuid": str(uuid.uuid4()),
                "args": {"id": task_id},
            }
        ]
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{settings.todoist_api_base_url}/sync",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(sync_payload),
            )
            response.raise_for_status()
            return {
                "status": "completed",
                "task_id": task_id,
                "success": True,
            }
    except Exception as exc:
        logger.error("Error completing Todoist task %s: %s", task_id, exc)
        raise ToolExecutionError(f"Failed to complete Todoist task: {exc}") from exc
