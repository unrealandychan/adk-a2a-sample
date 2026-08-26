# ADK 2.0 Agent-to-Agent (A2A) Boilerplate

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![ADK 2.0](https://img.shields.io/badge/ADK-2.0-green.svg)](https://adk.dev/2.0/)
[![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-purple.svg)](https://adk.dev/a2a/quickstart-exposing/)
[![Gemini Enterprise / GE](https://img.shields.io/badge/Gemini%20Enterprise-A2A%20Registration-blue.svg)](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent)
[![Clean Code](https://img.shields.io/badge/Clean%20Code-DDD%20%2B%20Harness-orange.svg)](https://github.com/unrealandychan/clean-code-skill)

A production-ready **Google Agent Development Kit (ADK) 2.0** multi-agent starter boilerplate featuring **Agent-to-Agent (A2A)** protocol communication, **Gemini Enterprise (GE) / Discovery Engine** A2A registration with **Todoist OAuth 2.0**, **Vertex AI Agent Engine**, **Graph Engine** workflows, and automated **Cloud Run & Docker** deployment scripts, built following **Clean Code**, **Domain-Driven Design (DDD)**, and **Harness Engineering** principles from [`unrealandychan/clean-code-skill`](https://github.com/unrealandychan/clean-code-skill).

---

## 🏛 Architecture & DDD Layers

```
adk-a2a-sample/
├── src/adk_a2a/
│   ├── domain/               # Pure Domain: Entities, Value Objects, Domain Exceptions
│   │   ├── models.py         # Immutable Value Objects (CityWeather, TodoistTask, AgentCard)
│   │   └── exceptions.py     # DomainError, AgentExecutionError, ToolExecutionError
│   ├── agents/               # ADK Agents & Orchestration
│   │   ├── orchestrator.py   # Master Orchestrator Agent delegating tasks to local & RemoteA2aAgent
│   │   └── specialized.py    # Native ADK Agents: Todoist Agent, Weather Analyst Agent, Calculator
│   ├── tools/                # Pure, testable tools with type contracts
│   │   ├── todoist.py        # Todoist App OAuth 2.0 & Task Management tools
│   │   ├── calculator.py     # Safe arithmetic computation
│   │   └── weather.py        # Weather retrieval service
│   ├── a2a/                  # A2A Protocol Implementation (to_a2a wrapper, server & client)
│   │   ├── server.py         # to_a2a() ASGI bridge & discovery endpoints
│   │   ├── card.py           # Standardized Agent Card descriptor & Gemini Enterprise v0.3.0 builders
│   │   └── client.py         # Remote A2A Agent HTTP client
│   ├── integrations/         # Google Cloud & GE (Discovery Engine, Agent Engine, Graph Engine)
│   │   ├── ge_registration.py# Gemini Enterprise A2A & OAuth2 Authorization registration payloads
│   │   ├── agent_engine.py   # Vertex AI Agent Engine Session, Memory & App Factory
│   │   └── graph_engine.py   # Graph Engine Topological Multi-Agent Workflow State
│   └── core/                 # Observability & Configuration
│       ├── config.py         # Pydantic Settings
│       └── logging.py        # Structured logging with correlation ID tracing
├── tests/                    # Automated Pytest Suite (41 tests passing)
│   ├── test_domain.py        # Domain model immutability & validation tests
│   ├── test_tools.py         # Tool unit tests & error handling
│   ├── test_todoist.py       # Todoist OAuth2 & CRUD unit tests
│   ├── test_ge_registration.py # Gemini Enterprise A2A registration & card tests
│   ├── test_agents.py        # Agent orchestration tests
│   ├── test_a2a_server.py    # A2A server, to_a2a() exposure & discovery tests
│   └── test_integrations.py  # GE (Agent Engine & Graph Engine) integration tests
├── scripts/                  # Deployment & Tooling scripts
│   ├── register-ge-a2a.sh    # Automated Gemini Enterprise A2A & OAuth registration
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

## 🏛️ Registering A2A Agent with Gemini Enterprise (GE)

According to the [Gemini Enterprise A2A Agent Registration Guide](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent#register_a2a_agent-console), A2A agents can be registered into Gemini Enterprise apps with end-user OAuth 2.0 authorization support.

### Option 1: Automated Registration Script
Set your GCP project and run:
```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project make register-ge-a2a
```
This script will:
1. Create the `authorizations` resource in Discovery Engine with the Todoist OAuth2 credentials.
2. Generate the A2A v0.3.0 compliant Agent Card descriptor.
3. Register the agent in your Gemini Enterprise assistant with OAuth delegation.

### Option 2: Inspect Payloads / Google Cloud Console Setup
To print the JSON manifests ready to paste into the Google Cloud Console:
```bash
make ge-manifest
# or with project number:
uv run python main.py ge-manifest --project-number 1234567890 --url https://your-a2a-service.run.app
```

#### Steps in Google Cloud Console:
1. Open [Gemini Enterprise Console](https://console.cloud.google.com/gemini-enterprise/).
2. Select your App $\to$ **Agents** $\to$ **Add Agents** $\to$ **Custom agent via A2A**.
3. Paste the **A2A Agent Card JSON** (from `make ge-manifest`).
4. In Authorization, enter the **Client ID** (`f1d3a4ec08fb4b60a61679156e2edd92`), **Client Secret**, and Redirect URI (`https://vertexaisearch.cloud.google.com/oauth-redirect`).
5. Click **Finish**.

---

## 🔐 Todoist App OAuth 2.0 Integration

Follows the official [ADK Custom Tools OAuth 2.0 Authentication specification](https://adk.dev/tools-custom/authentication/#oauth2):

- **Client ID**: `f1d3a4ec08fb4b60a61679156e2edd92`
- **Client Secret**: `f1d3a4ec08fb4b60a61679156e2edd92`
- **Redirect URIs**:
  - `https://vertexaisearch.cloud.google.com/oauth-redirect`
  - `https://vertexaisearch.cloud.google.com/static/oauth/oauth.html`
- **Scopes**: `data:read_write,task:add`
- **Supported Operations**: List tasks (`get_todoist_tasks`), Create task (`create_todoist_task`), Complete task (`complete_todoist_task`), and OAuth token exchange (`exchange_todoist_code`).

```bash
# Display OAuth login URL and instruction:
make todoist-auth

# Exchange authorization code:
uv run python main.py todoist-auth --exchange <AUTHORIZATION_CODE>
```

> [!TIP]
> **Single User / Dev Testing Alternative**: If you just want to manage your personal tasks without multi-user OAuth login flows, you can simply set `TODOIST_API_TOKEN=<your_personal_token>` in `.env` (obtained from Todoist Settings $\to$ Integrations $\to$ Developer $\to$ API token).

---

## 🛠 Developer Commands via `make`

The repository provides a `Makefile` for developer workflows and quick scripts:

```bash
make help               # Display list of all available commands
make install            # Install all dependencies with uv
make run                # Run orchestrator goal locally
make serve              # Launch A2A agent server on port 8080 (to_a2a mode)
make info               # Print A2A Agent Card descriptor
make todoist-auth       # Display Todoist OAuth2 login URL and instructions
make ge-manifest        # Display Gemini Enterprise A2A registration manifest & payloads
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
make register-ge-a2a    # Register A2A Agent & Todoist OAuth in Gemini Enterprise
make clean              # Clean cache files and build artifacts
```

---

## 🚀 Cloud Run & Vertex AI Deployment

### 1. Deploy to Google Cloud Run
```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project ./scripts/deploy.sh cloud_run
```

### 2. Deploy to Vertex AI Agent Engine (GE)
```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project ./scripts/deploy.sh agent_engine
```

### 3. Local Docker Build & Test
```bash
./scripts/deploy.sh docker
```

---

## 🧪 Testing & Code Quality

### Run Automated Tests (41/41 Passing)
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

---

## 📄 License
MIT
