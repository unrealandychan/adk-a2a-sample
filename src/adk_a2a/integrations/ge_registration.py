"""Gemini Enterprise (GE) / Discovery Engine A2A Agent Registration helper."""

import json
import urllib.parse
from typing import Any

from adk_a2a.a2a.card import build_gemini_enterprise_agent_card
from adk_a2a.core.config import get_settings


def build_ge_authorization_payload(
    project_number: str,
    location: str = "global",
    auth_id: str = "todoist-oauth-auth",
    client_id: str | None = None,
    client_secret: str | None = None,
) -> dict[str, Any]:
    """Constructs the Discovery Engine Authorization resource payload for Todoist OAuth2.

    Reference:
    https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent#add-authorization-resource
    """
    settings = get_settings()
    c_id = client_id or settings.todoist_client_id
    c_secret = client_secret or settings.todoist_client_secret

    auth_params = {
        "client_id": c_id,
        "redirect_uri": "https://vertexaisearch.cloud.google.com/static/oauth/oauth.html",
        "scope": "data:read_write task:add",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_uri = f"{settings.todoist_auth_url}?{urllib.parse.urlencode(auth_params)}"

    return {
        "name": f"projects/{project_number}/locations/{location}/authorizations/{auth_id}",
        "serverSideOauth2": {
            "clientId": c_id,
            "clientSecret": c_secret,
            "authorizationUri": auth_uri,
            "tokenUri": settings.todoist_token_url,
        },
    }


def build_ge_agent_registration_payload(
    agent_name: str = "todoist_weather_agent",
    display_name: str = "Todoist & Weather Agent",
    description: str = "ADK 2.0 A2A Agent managing Todoist tasks with OAuth 2.0 and weather computation.",
    agent_service_url: str | None = None,
    project_number: str | None = None,
    location: str = "global",
    auth_id: str = "todoist-oauth-auth",
) -> dict[str, Any]:
    """Constructs the Discovery Engine A2A Agent registration payload.

    Reference:
    https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent#register-your-a2a-agent
    """
    settings = get_settings()
    url = agent_service_url or settings.a2a_server_base_url.rstrip("/")
    agent_card = build_gemini_enterprise_agent_card(agent_url=url)

    payload: dict[str, Any] = {
        "name": agent_name,
        "displayName": display_name,
        "description": description,
        "a2aAgentDefinition": {
            "jsonAgentCard": json.dumps(agent_card),
        },
    }

    if project_number:
        payload["authorizationConfig"] = {
            "agentAuthorization": f"projects/{project_number}/locations/{location}/authorizations/{auth_id}"
        }

    return payload
