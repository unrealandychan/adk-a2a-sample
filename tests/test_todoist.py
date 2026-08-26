"""Tests for Todoist tools, OAuth2 authentication, and agent integration."""

from unittest.mock import MagicMock, patch

import pytest

from adk_a2a.agents.orchestrator import create_orchestrator_agent
from adk_a2a.agents.specialized import (
    create_adk_todoist_agent,
    create_todoist_agent,
)
from adk_a2a.domain.exceptions import ToolExecutionError
from adk_a2a.domain.models import AgentTask, TodoistTask
from adk_a2a.tools.todoist import (
    complete_todoist_task,
    create_todoist_task,
    exchange_todoist_code,
    get_todoist_adk_auth_objects,
    get_todoist_auth_status,
    get_todoist_auth_url,
    get_todoist_tasks,
)


def test_todoist_task_model() -> None:
    """Tests TodoistTask value object immutability and attributes."""
    task = TodoistTask(
        id="task-123",
        content="Deploy to Vertex AI Agent Engine",
        is_completed=False,
        priority=4,
    )
    assert task.id == "task-123"
    assert task.priority == 4
    assert task.is_completed is False


def test_todoist_adk_auth_objects() -> None:
    """Tests constructing standard ADK OAuth2 auth objects."""
    scheme, credential = get_todoist_adk_auth_objects()
    assert scheme is not None
    assert credential.auth_type.value == "oauth2"
    assert (
        credential.oauth2.client_id == "f1d3a4ec08fb4b60a61679156e2edd92"
        if credential.oauth2
        else False
    )


def test_todoist_auth_url_generation() -> None:
    """Tests generating OAuth2 authorization URL."""
    auth_url = get_todoist_auth_url(state="test_state_123")
    assert "https://todoist.com/oauth/authorize" in auth_url
    assert "client_id=f1d3a4ec08fb4b60a61679156e2edd92" in auth_url
    assert "test_state_123" in auth_url


def test_todoist_auth_status() -> None:
    """Tests retrieving auth status object."""
    status = get_todoist_auth_status()
    assert status.client_id == "f1d3a4ec08fb4b60a61679156e2edd92"
    assert (
        status.redirect_uri
        == "https://vertexaisearch.cloud.google.com/oauth-redirect"
    )
    assert status.auth_url is not None


def test_get_todoist_tasks_sandbox() -> None:
    """Tests retrieving tasks in offline / sandbox mode."""
    tasks = get_todoist_tasks()
    assert len(tasks) >= 2
    assert "content" in tasks[0]


def test_create_todoist_task_sandbox() -> None:
    """Tests creating a task in offline sandbox mode."""
    res = create_todoist_task(content="Buy groceries for dinner", priority=2)
    assert res["status"] == "created (simulated)"
    assert res["task"]["content"] == "Buy groceries for dinner"


def test_create_todoist_task_empty_fails() -> None:
    """Tests that empty task content raises ToolExecutionError."""
    with pytest.raises(
        ToolExecutionError, match="Task content cannot be empty"
    ):
        create_todoist_task(content="")


def test_complete_todoist_task_sandbox() -> None:
    """Tests completing a task in offline sandbox mode."""
    res = complete_todoist_task(task_id="task-101")
    assert res["status"] == "completed (simulated)"
    assert res["success"] is True


def test_complete_todoist_task_empty_fails() -> None:
    """Tests that empty task ID raises ToolExecutionError."""
    with pytest.raises(ToolExecutionError, match="Task ID cannot be empty"):
        complete_todoist_task(task_id="")


def test_exchange_todoist_code_mocked() -> None:
    """Tests exchanging OAuth authorization code against Todoist token endpoint."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "mocked_access_token_abc",
        "token_type": "Bearer",
    }
    mock_response.raise_for_status.return_value = None

    with patch("httpx.Client.post", return_value=mock_response):
        tokens = exchange_todoist_code(code="sample_auth_code")
        assert tokens["access_token"] == "mocked_access_token_abc"
        assert tokens["token_type"] == "Bearer"


def test_create_adk_todoist_agent() -> None:
    """Tests initializing native Google ADK Todoist agent."""
    agent = create_adk_todoist_agent()
    assert agent.name == "todoist_agent"
    assert len(agent.tools) == 3


def test_todoist_context_token_handling() -> None:
    """Tests setting and getting request-scoped context token."""
    from adk_a2a.tools.todoist import (
        get_effective_todoist_token,
        set_current_todoist_token,
    )

    set_current_todoist_token("Bearer oauth_token_xyz_123")
    assert get_effective_todoist_token() == "oauth_token_xyz_123"
    set_current_todoist_token(None)


def test_todoist_domain_agent_execution() -> None:
    """Tests Todoist Domain Agent task listing and creation."""
    agent = create_todoist_agent()

    # Listing tasks
    list_task = AgentTask(goal="List my todoist tasks")
    res = agent.execute(list_task)
    assert res.success is True
    assert "Todoist Tasks" in res.output

    # Creating a task
    create_task = AgentTask(goal="Create a new task to write unit tests")
    res_create = agent.execute(create_task)
    assert res_create.success is True
    assert "Created Todoist task" in res_create.output


def test_orchestrator_delegation_to_todoist() -> None:
    """Tests Master Orchestrator delegating task management to Todoist sub-agent."""
    orchestrator = create_orchestrator_agent()
    task = AgentTask(goal="Check my todo tasks for today")
    response = orchestrator.run(task)

    assert response.success is True
    assert response.sub_agent_name == "todoist_agent"
    assert "Todoist Tasks" in response.output
