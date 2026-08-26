"""CLI Entrypoint for the ADK 2.0 Agent-to-Agent (A2A) sample project."""

import argparse
import json

import uvicorn

from adk_a2a.a2a.card import build_agent_card, build_gemini_enterprise_agent_card
from adk_a2a.a2a.server import create_a2a_app, expose_agent_via_to_a2a
from adk_a2a.agents.orchestrator import create_orchestrator_agent
from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import configure_logging, get_logger
from adk_a2a.domain.models import AgentTask
from adk_a2a.integrations.ge_registration import (
    build_ge_agent_registration_payload,
    build_ge_authorization_payload,
)
from adk_a2a.tools.todoist import exchange_todoist_code, get_todoist_auth_status

logger = get_logger(__name__)


def serve_command(host: str, port: int, mode: str = "adk") -> None:
    """Starts the A2A micro-agent server.

    Args:
        host: Host IP to bind.
        port: Port number to bind.
        mode: 'adk' (uses official to_a2a utility) or 'custom' (uses custom FastAPI app).
    """
    logger.info("Starting ADK A2A server [%s mode] on %s:%d", mode, host, port)
    app = (
        expose_agent_via_to_a2a(host=host, port=port)
        if mode == "adk"
        else create_a2a_app()
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


def run_command(goal: str) -> None:
    """Runs a direct goal through the master orchestrator agent."""
    settings = get_settings()
    logger.info(
        "Initializing Master Orchestrator Agent (Model: %s)", settings.adk_model
    )
    orchestrator = create_orchestrator_agent(model=settings.adk_model)

    task = AgentTask(goal=goal)
    print(f'\n🚀 Submitting Goal: "{goal}"\n')
    response = orchestrator.run(task)

    print("═══════════════════════════════════════════════════════════")
    print(f"🤖 Agent: {response.sub_agent_name}")
    print(f"📋 Task ID: {response.task_id}")
    print(f"✨ Status: {'Success' if response.success else 'Failed'}")
    print("───────────────────────────────────────────────────────────")
    print(response.output)
    print("═══════════════════════════════════════════════════════════\n")


def info_command() -> None:
    """Prints the A2A Agent Card and environment settings."""
    card = build_agent_card()
    settings = get_settings()

    print("\n🔍 ADK 2.0 A2A Agent Card & Specifications:")
    print("───────────────────────────────────────────────────────────")
    print(f"Name:         {card.name}")
    print(f"Description:  {card.description}")
    print(f"Version:      {card.version}")
    print(f"Environment:  {settings.adk_environment}")
    print(f"Model:        {settings.adk_model}")
    print("\nCapabilities:")
    for cap in card.capabilities:
        print(f"  • {cap}")
    print("\nEndpoints:")
    for name, url in card.endpoints.items():
        print(f"  • {name}: {url}")
    print("───────────────────────────────────────────────────────────\n")


def todoist_auth_command(exchange_code: str | None = None) -> None:
    """Displays Todoist OAuth2 instructions or exchanges an auth code."""
    status = get_todoist_auth_status()

    if exchange_code:
        print(
            "\n🔄 Exchanging authorization code with Todoist token endpoint..."
        )
        try:
            tokens = exchange_todoist_code(code=exchange_code)
            print("✅ Token Exchange Successful!")
            print(f"Access Token: {tokens.get('access_token')}")
            print(f"Token Type:   {tokens.get('token_type')}")
        except Exception as exc:
            print(f"❌ Error exchanging code: {exc}")
        return

    print("\n🔐 Todoist App OAuth 2.0 Configuration:")
    print("───────────────────────────────────────────────────────────")
    print(f"Client ID:    {status.client_id}")
    print(f"Redirect URI: {status.redirect_uri}")
    print(
        f"Auth Status:  {'Authenticated' if status.is_authenticated else 'Requires Authorization'}"
    )
    print("\n👉 Step 1: Open this URL in your browser to authorize:")
    print(f"   {status.auth_url}")
    print("\n👉 Step 2: After consent, copy the 'code' parameter from redirect URL.")
    print("👉 Step 3: Run:")
    print("   uv run python main.py todoist-auth --exchange YOUR_AUTH_CODE")
    print("───────────────────────────────────────────────────────────\n")


def ge_manifest_command(
    project_number: str = "YOUR_PROJECT_NUMBER",
    location: str = "global",
    agent_url: str = "http://127.0.0.1:8080",
) -> None:
    """Generates Gemini Enterprise A2A registration payloads and Agent Card."""
    agent_card = build_gemini_enterprise_agent_card(agent_url=agent_url)
    auth_payload = build_ge_authorization_payload(
        project_number=project_number,
        location=location,
    )
    reg_payload = build_ge_agent_registration_payload(
        agent_service_url=agent_url,
        project_number=project_number,
        location=location,
    )

    print("\n🏛️  Gemini Enterprise (GE) A2A Agent Manifest & Payloads")
    print("───────────────────────────────────────────────────────────")
    print("1. [A2A Agent Card (v0.3.0)]:")
    print(json.dumps(agent_card, indent=2))
    print("\n2. [Discovery Engine Authorization Payload (Todoist OAuth 2.0)]:")
    print(json.dumps(auth_payload, indent=2))
    print("\n3. [Gemini Enterprise Agent Registration Payload]:")
    print(json.dumps(reg_payload, indent=2))
    print("───────────────────────────────────────────────────────────\n")


def main() -> None:
    """Main CLI entrypoint."""
    settings = get_settings()
    configure_logging(level=settings.log_level)

    parser = argparse.ArgumentParser(
        description="ADK 2.0 Agent-to-Agent (A2A) Sample CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )

    # Command: run
    run_parser = subparsers.add_parser(
        "run", help="Execute an orchestrator goal"
    )
    run_parser.add_argument(
        "goal",
        nargs="?",
        default="Compare the temperature difference between Tokyo and Paris",
        help="Goal or prompt for the multi-agent system",
    )

    # Command: serve
    serve_parser = subparsers.add_parser(
        "serve", help="Launch the A2A HTTP server"
    )
    serve_parser.add_argument(
        "--host",
        default=settings.a2a_server_host,
        help=f"Host address to bind (default: {settings.a2a_server_host})",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=settings.a2a_server_port,
        help=f"Port to bind (default: {settings.a2a_server_port})",
    )
    serve_parser.add_argument(
        "--mode",
        choices=["adk", "custom"],
        default="adk",
        help="Server mode: 'adk' (uses official to_a2a() wrapper) or 'custom' (FastAPI)",
    )

    # Command: info
    subparsers.add_parser(
        "info", help="Display A2A Agent Card and configuration"
    )

    # Command: todoist-auth
    todoist_parser = subparsers.add_parser(
        "todoist-auth", help="Manage Todoist OAuth2 authentication"
    )
    todoist_parser.add_argument(
        "--exchange",
        dest="exchange_code",
        default=None,
        help="Exchange an OAuth authorization code for an access token",
    )

    # Command: ge-manifest
    ge_parser = subparsers.add_parser(
        "ge-manifest",
        help="Generate Gemini Enterprise (GE) A2A registration manifests",
    )
    ge_parser.add_argument(
        "--project-number",
        default="YOUR_PROJECT_NUMBER",
        help="GCP Project Number",
    )
    ge_parser.add_argument(
        "--location",
        default="global",
        help="Discovery Engine location (global, us, eu)",
    )
    ge_parser.add_argument(
        "--url",
        default=settings.a2a_server_base_url,
        help="A2A Agent Endpoint URL",
    )

    args = parser.parse_args()

    if args.command == "serve":
        serve_command(host=args.host, port=args.port, mode=args.mode)
    elif args.command == "info":
        info_command()
    elif args.command == "todoist-auth":
        todoist_auth_command(exchange_code=args.exchange_code)
    elif args.command == "ge-manifest":
        ge_manifest_command(
            project_number=args.project_number,
            location=args.location,
            agent_url=args.url,
        )
    elif args.command == "run":
        run_command(goal=args.goal)
    else:
        run_command(
            goal="Compare the temperature difference between Tokyo and Paris"
        )


if __name__ == "__main__":
    main()

