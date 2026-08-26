"""A2A (Agent-to-Agent) protocol integration, server endpoints, and client adapters."""

from adk_a2a.a2a.card import build_agent_card
from adk_a2a.a2a.client import RemoteA2aClient
from adk_a2a.a2a.server import a2a_app, create_a2a_app, expose_agent_via_to_a2a

__all__ = [
    "RemoteA2aClient",
    "a2a_app",
    "build_agent_card",
    "create_a2a_app",
    "expose_agent_via_to_a2a",
]
