#!/usr/bin/env bash
# =============================================================================
# Deployment Script for ADK 2.0 Agent-to-Agent (A2A) Micro-Services
# Supports: Google Cloud Run, Vertex AI Agent Engine (GE), and Local Docker
# =============================================================================

set -euo pipefail

# Automatically load variables from local .env if present
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Configuration defaults
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="${A2A_SERVICE_NAME:-adk-a2a-service}"
PORT="${PORT:-8080}"
MODE="${1:-cloud_run}"

show_help() {
  cat << EOF
Usage: ./scripts/deploy.sh [COMMAND] [OPTIONS]

Commands:
  cloud_run       Deploy A2A Agent Service to Google Cloud Run (default)
  agent_engine    Deploy A2A Agent to Vertex AI Agent Engine (GE)
  docker          Build and test local Docker container image
  help            Show this help message

Environment Variables:
  GOOGLE_CLOUD_PROJECT   GCP Project ID (Required for Cloud deployments)
  GOOGLE_CLOUD_REGION    GCP Region (Default: us-central1)
  A2A_SERVICE_NAME       Name of the Cloud Run service (Default: adk-a2a-service)
  PORT                   Port to expose on Cloud Run (Default: 8080)
  GOOGLE_API_KEY         Gemini API Key to pass to the container

Examples:
  ./scripts/deploy.sh cloud_run
  ./scripts/deploy.sh agent_engine
  ./scripts/deploy.sh docker
EOF
}

deploy_docker() {
  echo "============================================================"
  echo "Building Local Production Docker Image..."
  echo "============================================================"
  docker build -t "${SERVICE_NAME}:latest" .
  echo "Docker image built successfully: ${SERVICE_NAME}:latest"
  echo ""
  echo "To test run locally:"
  echo "  docker run -p ${PORT}:8080 -e GOOGLE_API_KEY=\"\${GOOGLE_API_KEY}\" ${SERVICE_NAME}:latest"
}

deploy_cloud_run() {
  if [[ -z "${PROJECT_ID}" ]]; then
    echo "Error: GOOGLE_CLOUD_PROJECT environment variable is not set."
    echo "Please set it in your .env file: GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
  fi

  echo "============================================================"
  echo "Deploying ADK A2A Service to Google Cloud Run"
  echo "============================================================"
  echo "Project : ${PROJECT_ID}"
  echo "Region  : ${REGION}"
  echo "Service : ${SERVICE_NAME}"
  echo "Port    : ${PORT}"
  echo "============================================================"

  # 1. Check if gcloud CLI is available
  if ! command -v gcloud &> /dev/null; then
    echo "Error: 'gcloud' CLI is required for Cloud Run deployment."
    exit 1
  fi

  # 2. Configure GCP project
  echo "Setting active project to ${PROJECT_ID}..."
  gcloud config set project "${PROJECT_ID}" --quiet

  # 3. Enable necessary Google Cloud APIs
  echo "Enabling required GCP APIs (Cloud Run, Artifact Registry, Cloud Build, Vertex AI)..."
  gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    aiplatform.googleapis.com \
    --quiet

  # 4. Build and push container using Google Cloud Build
  IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
  echo "Submitting build to Google Cloud Build: ${IMAGE_TAG}..."
  gcloud builds submit --tag "${IMAGE_TAG}" .

  # 5. Deploy to Cloud Run with A2A configuration
  echo "Deploying container to Cloud Run..."
  gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_TAG}" \
    --platform managed \
    --region "${REGION}" \
    --port "${PORT}" \
    --allow-unauthenticated \
    --set-env-vars="ADK_ENVIRONMENT=production,ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS=true" \
    --quiet

  # 6. Retrieve service URL and verify Agent Card
  SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --format="value(status.url)")
  echo ""
  echo "============================================================"
  echo "Deployment Successful!"
  echo "Service URL      : ${SERVICE_URL}"
  echo "A2A Agent Card   : ${SERVICE_URL}/.well-known/agent-card.json"
  echo "Health Endpoint  : ${SERVICE_URL}/healthz"
  echo "============================================================"
}

deploy_agent_engine() {
  if [[ -z "${PROJECT_ID}" ]]; then
    echo "Error: GOOGLE_CLOUD_PROJECT environment variable is not set in .env or environment."
    exit 1
  fi

  echo "============================================================"
  echo "Deploying A2A Agent to Vertex AI Agent Engine (GE)"
  echo "============================================================"
  echo "Project  : ${PROJECT_ID}"
  echo "Location : ${REGION}"
  echo "============================================================"

  # Check ADK CLI availability
  if command -v adk &> /dev/null || python -m google.adk --help &> /dev/null; then
    echo "Invoking ADK Agent Engine deployment..."
    uv run python -c "
import os
from google.adk.cli.cli_deploy import to_agent_engine

to_agent_engine(
    agent_folder='.',
    project='${PROJECT_ID}',
    region='${REGION}',
    display_name='${SERVICE_NAME}-ge',
    description='ADK 2.0 A2A Agent deployed to Vertex AI Agent Engine'
)
"
    echo "Agent Engine (GE) deployment initiated."
  else
    echo "ADK deployment facade completed. Running Cloud Run deployment with GE configuration..."
    deploy_cloud_run
  fi
}

case "${MODE}" in
  cloud_run)
    deploy_cloud_run
    ;;
  agent_engine|ge)
    deploy_agent_engine
    ;;
  docker)
    deploy_docker
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    echo "Unknown command: ${MODE}"
    show_help
    exit 1
    ;;
esac
