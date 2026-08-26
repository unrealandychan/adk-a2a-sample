# Multi-stage Dockerfile for ADK 2.0 A2A Agent Service
# Optimized with astral-sh/uv for fast build and minimal image size

FROM python:3.11-slim-bookworm AS builder

# Install uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation and frozen lockfile
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies first for optimal docker layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev --all-extras

# Copy application source and install package
COPY src/ ./src/
COPY main.py README.md ./
RUN uv sync --frozen --no-dev --all-extras

# -----------------------------------------------------------------------------
# Runtime stage
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runner

# Create non-root system user for security
RUN groupadd -r adk && useradd -r -g adk -d /app -s /sbin/nologin -c "ADK App User" adk

WORKDIR /app

# Copy virtual environment and application from builder
COPY --from=builder --chown=adk:adk /app/.venv /app/.venv
COPY --from=builder --chown=adk:adk /app/src /app/src
COPY --from=builder --chown=adk:adk /app/main.py /app/main.py

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0
ENV ADK_ENVIRONMENT=production
ENV ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS=true

USER adk

# Expose A2A server port
EXPOSE 8080

# Health check using Python's urllib to avoid curl dependency in slim image
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')" || exit 1

# Launch A2A application
ENTRYPOINT ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8080", "--mode", "adk"]

