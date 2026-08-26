"""CLI Entrypoint for the ADK 2.0 Agent-to-Agent (A2A) sample project."""

import argparse

import uvicorn

from adk_a2a.a2a.card import build_agent_card
from adk_a2a.a2a.server import create_a2a_app, expose_agent_via_to_a2a
from adk_a2a.agents.orchestrator import create_orchestrator_agent
from adk_a2a.core.config import get_settings
from adk_a2a.core.logging import configure_logging, get_logger
from adk_a2a.domain.models import AgentTask

logger = get_logger(__name__)


def serve_command(host: str, port: int, mode: str = "adk") -> None:
    """Starts the A2A micro-agent server.

    Args:
        host: Host IP to bind.
        port: Port number to bind.
        mode: 'adk' (uses official to_a2a utility) or 'custom' (uses custom FastAPI app).
    """
    logger.info("Starting ADK A2A server [%s mode] on %s:%d", mode, host, port)
    app = expose_agent_via_to_a2a(host=host, port=port) if mode == "adk" else create_a2a_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


def run_command(goal: str) -> None:
    """Runs a direct goal through the master orchestrator agent."""
    settings = get_settings()
    logger.info("Initializing Master Orchestrator Agent (Model: %s)", settings.adk_model)
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


def main() -> None:
    """Main CLI entrypoint."""
    settings = get_settings()
    configure_logging(level=settings.log_level)

    parser = argparse.ArgumentParser(
        description="ADK 2.0 Agent-to-Agent (A2A) Sample CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute an orchestrator goal")
    run_parser.add_argument(
        "goal",
        nargs="?",
        default="Compare the temperature difference between Tokyo and Paris",
        help="Goal or prompt for the multi-agent system",
    )

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch the A2A HTTP server")
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
    subparsers.add_parser("info", help="Display A2A Agent Card and configuration")

    args = parser.parse_args()

    if args.command == "serve":
        serve_command(host=args.host, port=args.port, mode=args.mode)
    elif args.command == "info":
        info_command()
    elif args.command == "run":
        run_command(goal=args.goal)
    else:
        run_command(goal="Compare the temperature difference between Tokyo and Paris")


if __name__ == "__main__":
    main()
