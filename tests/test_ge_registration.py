"""Tests for Gemini Enterprise (GE) / Discovery Engine A2A agent registration."""

import json

from adk_a2a.a2a.card import build_gemini_enterprise_agent_card
from adk_a2a.core.config import get_settings
from adk_a2a.integrations.ge_registration import (
    build_ge_agent_registration_payload,
    build_ge_authorization_payload,
)


def test_gemini_enterprise_agent_card() -> None:
    """Tests that Agent Card conforms to Gemini Enterprise A2A v0.3.0 schema."""
    card = build_gemini_enterprise_agent_card(agent_url="https://a2a.example.com")

    assert card["protocolVersion"] == "0.3.0"
    assert card["url"] == "https://a2a.example.com"
    assert len(card["skills"]) >= 3
    assert any(s["id"] == "todoist_management" for s in card["skills"])
    assert any(s["id"] == "weather_analysis" for s in card["skills"])
    assert any(s["id"] == "calculator" for s in card["skills"])


def test_ge_authorization_payload() -> None:
    """Tests constructing Discovery Engine serverSideOauth2 authorization payload."""
    payload = build_ge_authorization_payload(
        project_number="1234567890",
        location="global",
        auth_id="todoist-auth-id",
    )

    assert payload["name"] == "projects/1234567890/locations/global/authorizations/todoist-auth-id"
    oauth_config = payload["serverSideOauth2"]
    settings = get_settings()
    assert oauth_config["clientId"] == settings.todoist_client_id
    assert oauth_config["clientSecret"] == settings.todoist_client_secret
    assert "https://todoist.com/oauth/authorize" in oauth_config["authorizationUri"]
    assert "vertexaisearch.cloud.google.com" in oauth_config["authorizationUri"]
    assert oauth_config["tokenUri"] == "https://todoist.com/oauth/access_token"


def test_ge_agent_registration_payload() -> None:
    """Tests constructing Discovery Engine A2A agent creation payload."""
    payload = build_ge_agent_registration_payload(
        agent_name="my_todoist_agent",
        display_name="My Todoist Agent",
        agent_service_url="https://my-a2a-service.run.app",
        project_number="1234567890",
        location="global",
        auth_id="todoist-auth-id",
    )

    assert payload["name"] == "my_todoist_agent"
    assert payload["displayName"] == "My Todoist Agent"
    assert "a2aAgentDefinition" in payload

    # Ensure jsonAgentCard is valid serialized JSON
    agent_card_data = json.loads(payload["a2aAgentDefinition"]["jsonAgentCard"])
    assert agent_card_data["protocolVersion"] == "0.3.0"
    assert agent_card_data["url"] == "https://my-a2a-service.run.app"

    # Ensure authorizationConfig points to the created authorization resource
    assert (
        payload["authorizationConfig"]["agentAuthorization"]
        == "projects/1234567890/locations/global/authorizations/todoist-auth-id"
    )
