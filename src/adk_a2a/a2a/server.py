"""A2A Server exposing ADK agents via to_a2a() and custom ASGI endpoints."""

import os
from typing import Any

from a2a.types import AgentCard as A2aSdkAgentCard
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import Agent
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from adk_a2a.a2a.card import build_agent_card
from adk_a2a.agents.orchestrator import create_orchestrator_agent
from adk_a2a.agents.specialized import create_adk_unified_agent
from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import get_logger, set_correlation_id
from adk_a2a.domain.models import AgentCard, AgentResponse, AgentTask
from adk_a2a.tools.todoist import set_current_todoist_token

logger = get_logger(__name__)


class AuthHeaderMiddleware(BaseHTTPMiddleware):
    """Captures OAuth Bearer token from Gemini Enterprise / A2A proxy headers into context."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        token = None
        for header_name, header_val in request.headers.items():
            if "authorization" in header_name.lower():
                if header_val.lower().startswith("bearer "):
                    token = header_val[7:].strip()
                    break
                elif header_val:
                    token = header_val.strip()
        if token:
            set_current_todoist_token(token)
        return await call_next(request)


def expose_agent_via_to_a2a(
    agent: Agent | None = None,
    host: str = "localhost",
    port: int = 8080,
    agent_card: A2aSdkAgentCard | str | None = None,
) -> Starlette:
    """Exposes an ADK Agent as an A2A-compliant ASGI application using `to_a2a()`.

    As specified in https://adk.dev/a2a/quickstart-exposing/, `to_a2a()`:
    1. Bridges A2A protocol requests to the ADK agent via `A2aAgentExecutor`.
    2. Auto-generates the Agent Card at `/.well-known/agent-card.json`.
    3. Manages task state and push notifications in-memory.

    Args:
        agent: The primary ADK Agent instance. Defaults to the Unified Agent.
        host: Hostname for advertised A2A endpoint URLs.
        port: Port number for advertised A2A endpoint URLs.
        agent_card: Optional custom AgentCard object or path to JSON file.

    Returns:
        A Starlette ASGI application ready to be served via Uvicorn.
    """
    settings = get_settings()
    if settings.adk_suppress_a2a_experimental_feature_warnings:
        os.environ["ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS"] = "true"

    target_agent = agent or create_adk_unified_agent(model=settings.adk_model)
    logger.info(
        "Exposing agent [%s] via A2A on %s:%d using to_a2a()",
        target_agent.name,
        host,
        port,
    )

    app = to_a2a(
        target_agent,
        host=host,
        port=port,
        agent_card=agent_card,
    )
    app.add_middleware(AuthHeaderMiddleware)
    return app


def create_a2a_app() -> FastAPI:
    """Factory function creating a custom A2A FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="ADK 2.0 A2A Agent Server",
        description="A2A compliant Agent server exposing Agent Cards and Task APIs",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    orchestrator = create_orchestrator_agent(model=settings.adk_model)

    @app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Health"])
    async def health_check() -> dict[str, Any]:
        """Liveness & health check endpoint for Harness pipeline monitoring."""
        return {
            "status": "healthy",
            "environment": settings.adk_environment,
            "agent": orchestrator.name,
        }

    @app.get("/.well-known/agent.json", response_model=AgentCard, tags=["A2A Discovery"])
    @app.get("/.well-known/agent-card.json", response_model=AgentCard, tags=["A2A Discovery"])
    async def get_agent_card() -> AgentCard:
        """Standard A2A discovery endpoint serving the Agent Card."""
        logger.info("Serving A2A Agent Card descriptor")
        return build_agent_card()

    @app.post("/tasks", response_model=AgentResponse, tags=["A2A Execution"])
    async def execute_task(task: AgentTask) -> AgentResponse:
        """A2A task delegation endpoint executing incoming agent workloads."""
        set_correlation_id(task.correlation_id)
        logger.info("Received A2A task request: %s (goal: %s)", task.task_id, task.goal)

        try:
            response = orchestrator.run(task)
            return response
        except Exception as exc:
            logger.error("Failed to execute A2A task: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task execution failed: {exc}",
            ) from exc

    return app


# Module-level ASGI app instance for quick uvicorn execution
# e.g.: uvicorn src.adk_a2a.a2a.server:a2a_app --port 8080
a2a_app = expose_agent_via_to_a2a()
