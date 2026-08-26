# ADK 2.0 Agent-to-Agent (A2A) Boilerplate

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![ADK 2.0](https://img.shields.io/badge/ADK-2.0-green.svg)](https://adk.dev/2.0/)
[![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-purple.svg)](https://adk.dev/a2a/quickstart-exposing/)
[![Google Cloud / GE](https://img.shields.io/badge/Google%20Cloud-Agent%20Engine%20(GE)-blue.svg)](https://cloud.google.com/vertex-ai)
[![Clean Code](https://img.shields.io/badge/Clean%20Code-DDD%20%2B%20Harness-orange.svg)](https://github.com/unrealandychan/clean-code-skill)

A production-ready **Google Agent Development Kit (ADK) 2.0** multi-agent starter boilerplate featuring **Agent-to-Agent (A2A)** protocol communication, **Vertex AI Agent Engine (GE)** integration, **Graph Engine (GE)** workflows, and automated **Cloud Run & Docker** deployment scripts, built following **Clean Code**, **Domain-Driven Design (DDD)**, and **Harness Engineering** principles from [`unrealandychan/clean-code-skill`](https://github.com/unrealandychan/clean-code-skill).

---

## 🏛 Architecture & DDD Layers

```
adk-a2a-sample/
├── src/adk_a2a/
│   ├── domain/               # Pure Domain: Entities, Value Objects, Domain Exceptions
│   │   ├── models.py         # Immutable Value Objects (CityWeather, CalculationResult, AgentCard)
│   │   └── exceptions.py     # DomainError, AgentExecutionError, ToolExecutionError
│   ├── agents/               # ADK Agents & Orchestration
│   │   ├── orchestrator.py   # Master Orchestrator Agent delegating tasks to local & RemoteA2aAgent
│   │   └── specialized.py    # Native ADK Agents: Weather Analyst Agent, Calculator Agent
│   ├── tools/                # Pure, testable tools with type contracts
│   │   ├── calculator.py     # Safe arithmetic computation
│   │   └── weather.py        # Weather retrieval service
│   ├── a2a/                  # A2A Protocol Implementation (to_a2a wrapper, server & client)
│   │   ├── server.py         # to_a2a() ASGI bridge & discovery endpoints
│   │   ├── card.py           # Standardized Agent Card descriptor builder
│   │   └── client.py         # Remote A2A Agent HTTP client
│   ├── integrations/         # Google Cloud & GE (Agent Engine & Graph Engine) Integrations
│   │   ├── agent_engine.py   # Vertex AI Agent Engine (GE) Session, Memory & App Factory
│   │   └── graph_engine.py   # Graph Engine (GE) Topological Multi-Agent Workflow State
│   └── core/                 # Observability & Configuration
│       ├── config.py         # Pydantic Settings
│       └── logging.py        # Structured logging with correlation ID tracing
├── tests/                    # Automated Pytest Suite
│   ├── test_domain.py        # Domain model immutability & validation tests
│   ├── test_tools.py         # Tool unit tests & error handling
│   ├── test_agents.py        # Agent orchestration tests
│   ├── test_a2a_server.py    # A2A server, to_a2a() exposure & discovery tests
│   └── test_integrations.py  # GE (Agent Engine & Graph Engine) integration tests
├── skills/                   # Clean Code + DDD + Harness Engineering Skill Kit
├── scripts/                  # Deployment & Tooling scripts
│   ├── deploy.sh             # Unified deployment script (Cloud Run, GE, Docker)
│   └── lint-and-report.sh    # Fast linting and AI report generator
├── Dockerfile                # Multi-stage optimized container image
├── docker-compose.yml        # Local multi-agent container composition
├── pyproject.toml            # Dependencies (google-adk[a2a,gcp], ruff, mypy, pytest)
├── .env.example              # Environment variables template
└── main.py                   # CLI & Server Entrypoint
```

---

## ⚡ Exposing Remote Agents via A2A (`to_a2a`)

As described in the [ADK 2.0 A2A Quickstart (Exposing)](https://adk.dev/a2a/quickstart-exposing/), ADK allows making any agent A2A-compatible with a single function call:

```python
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from adk_a2a.tools.weather import get_city_weather

# 1. Define your ADK Agent
weather_agent = Agent(
    name="weather_analyst_agent",
    description="Analyzes global city meteorological data.",
    instruction="You are a weather specialist.",
    tools=[get_city_weather],
    model="gemini-2.5-flash",
)

# 2. Expose via to_a2a() - auto-generates Agent Card & routes
a2a_app = to_a2a(weather_agent, port=8080)
```

---

## 🧠 Google Cloud & GE (Agent Engine & Graph Engine) Integrations

### 1. Vertex AI Agent Engine (GE) Integration
Connects A2A agents with managed Vertex AI Agent Engine services:
- **Session Services**: Stateful multi-turn conversation persistence (`VertexAiSessionService`).
- **Memory Banks**: Semantic long-term agent memory (`VertexAiMemoryBankService`).
- **Cloud Tracing & Telemetry**: OpenTelemetry traces exported to Google Cloud Trace.

```python
from adk_a2a.integrations.agent_engine import AgentEngineConfig, create_ge_integrated_a2a_app

config = AgentEngineConfig(project_id="my-gcp-project", location="us-central1")
a2a_ge_app = create_ge_integrated_a2a_app(config=config, port=8080)
```

### 2. Graph Engine (GE) Workflow Topologies
Provides deterministic routing across local and remote A2A agents using state-graph principles:

```python
from adk_a2a.integrations.graph_engine import create_ge_graph_agent

graph_agent = create_ge_graph_agent(
    remote_weather_card_url="http://localhost:8080/.well-known/agent-card.json"
)
```

---

## 🚀 Deployment Scripts

### 1. Deploy to Google Cloud Run
Deploys the containerized A2A micro-service with automated Cloud Build and Artifact Registry publishing:

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project ./scripts/deploy.sh cloud_run
```

### 2. Deploy to Vertex AI Agent Engine (GE)
Deploys the agent directly into the managed Vertex AI Agent Engine runtime:

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project ./scripts/deploy.sh agent_engine
```

### 3. Local Docker Build & Test
Builds the minimal multi-stage image locally:

```bash
./scripts/deploy.sh docker
```

Or with Docker Compose:
```bash
docker compose up -d
```

---

## 🛠 Developer Commands via `make`

The repository provides a `Makefile` for developer workflows and quick scripts:

```bash
make help               # Display list of all available commands
make install            # Install all dependencies with uv
make run                # Run orchestrator goal locally
make serve              # Launch A2A agent server on port 8080 (to_a2a mode)
make info               # Print A2A Agent Card descriptor
make test               # Run Pytest suite
make lint               # Run Ruff linter and strict Mypy
make format             # Auto-format code with Ruff
make check              # Run both lint and test in sequence
make report             # Generate Lint -> AI Clean Code report
make docker-build       # Build local Docker image
make docker-up          # Start containers with docker compose
make docker-down        # Stop docker compose containers
make deploy-cloud-run   # Deploy to Google Cloud Run
make deploy-ge          # Deploy to Vertex AI Agent Engine (GE)
make clean              # Clean cache files and build artifacts
```

---

## 🛠 Local Usage & CLI Commands

### Inspect Agent Card & Discovery Metadata
```bash
uv run python main.py info
```

### Run an Orchestrator Task Locally
```bash
# Run multi-agent weather comparison
uv run python main.py run "Compare the temperature difference between Tokyo and Paris"

# Run calculation task
uv run python main.py run "calculate (50 * 4) + (100 / 2)"
```

### Start the A2A Micro-Agent Server via `to_a2a()`
```bash
# Serves the weather agent via to_a2a on port 8080
uv run python main.py serve --host 0.0.0.0 --port 8080 --mode adk
```

---

## 🧪 Testing & Code Quality

### Run Automated Tests (25/25 Passing)
```bash
uv run pytest
```

### Run Ruff Linter & Formatter
```bash
uv run ruff check .
uv run ruff format .
```

### Run Mypy Strict Type Checking
```bash
uv run mypy src/ tests/
```

### Clean Code Lint → AI Report Script
```bash
./scripts/lint-and-report.sh
```

---

## 📄 License
MIT
