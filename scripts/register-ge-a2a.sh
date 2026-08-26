#!/usr/bin/env bash
# =============================================================================
# Register A2A Agent with Gemini Enterprise (GE) / Discovery Engine
# Reference: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent
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

# Configuration with environment defaults
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
LOCATION="${GE_LOCATION:-global}"
ENDPOINT_LOCATION="${GE_ENDPOINT_LOCATION:-global}"
APP_ID="${GE_APP_ID:-}"
AUTH_ID="${GE_AUTH_ID:-todoist-oauth-auth}"
AGENT_NAME="${GE_AGENT_NAME:-todoist_weather_agent}"
AGENT_DISPLAY_NAME="${GE_AGENT_DISPLAY_NAME:-Todoist & Weather Assistant}"
AGENT_SERVICE_URL="${GE_AGENT_SERVICE_URL:-}"

# Todoist OAuth Credentials
TODOIST_CLIENT_ID="${TODOIST_CLIENT_ID:-f1d3a4ec08fb4b60a61679156e2edd92}"
TODOIST_CLIENT_SECRET="${TODOIST_CLIENT_SECRET:-f1d3a4ec08fb4b60a61679156e2edd92}"

COLOR_RESET="\033[0m"
COLOR_INFO="\033[36m"
COLOR_SUCCESS="\033[32m"
COLOR_WARN="\033[33m"
COLOR_ERROR="\033[31m"

echo -e "${COLOR_INFO}=================================================================${COLOR_RESET}"
echo -e "${COLOR_INFO}  Gemini Enterprise (GE) A2A Agent & OAuth Registration Script  ${COLOR_RESET}"
echo -e "${COLOR_INFO}=================================================================${COLOR_RESET}"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${COLOR_WARN}No GOOGLE_CLOUD_PROJECT set in .env or environment.${COLOR_RESET}"
    echo -e "Attempting to retrieve active project from gcloud..."
    if command -v gcloud &> /dev/null; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
    fi
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${COLOR_ERROR}ERROR: GCP Project ID is required. Set GOOGLE_CLOUD_PROJECT in your .env file.${COLOR_RESET}"
    exit 1
fi

echo -e "• GCP Project ID:       ${COLOR_SUCCESS}${PROJECT_ID}${COLOR_RESET}"
echo -e "• GE Location:          ${COLOR_SUCCESS}${LOCATION}${COLOR_RESET}"

# Fetch Project Number via gcloud
if command -v gcloud &> /dev/null; then
    echo -e "${COLOR_INFO}Fetching GCP Project Number...${COLOR_RESET}"
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")
    if [ -n "$PROJECT_NUMBER" ]; then
        echo -e "• GCP Project Number:   ${COLOR_SUCCESS}${PROJECT_NUMBER}${COLOR_RESET}"
    fi
else
    PROJECT_NUMBER="YOUR_PROJECT_NUMBER"
fi

# Discover Gemini Enterprise / Discovery Engine App ID if not specified
if [ -z "$APP_ID" ] && command -v gcloud &> /dev/null; then
    echo -e "${COLOR_INFO}Discovering Gemini Enterprise Apps in project ${PROJECT_ID}...${COLOR_RESET}"
    ACCESS_TOKEN=$(gcloud auth print-access-token)
    LIST_ENGINES_URL="https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines"
    
    ENGINES_RESPONSE=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" -H "X-Goog-User-Project: ${PROJECT_ID}" "${LIST_ENGINES_URL}" || echo "{}")
    
    # Extract the first engine ID
    DISCOVERED_APP=$(echo "$ENGINES_RESPONSE" | grep -o '"name": *"[^"]*"' | head -n 1 | sed -E 's/.*\/engines\/([^"]+)"/\1/' || echo "")
    
    if [ -n "$DISCOVERED_APP" ]; then
        APP_ID="$DISCOVERED_APP"
        echo -e "• Discovered App ID:    ${COLOR_SUCCESS}${APP_ID}${COLOR_RESET}"
    fi
fi

if [ -z "$APP_ID" ]; then
    echo -e "\n${COLOR_WARN}⚠️  No Gemini Enterprise App ID found. Set GE_APP_ID in your .env file.${COLOR_RESET}"
    echo -e "To create an App in Gemini Enterprise:"
    echo -e "1. Go to https://console.cloud.google.com/gemini-enterprise/"
    echo -e "2. Click 'Create App' and put GE_APP_ID=<app-id> into your .env"
    APP_ID="YOUR_APP_ID"
fi

# Auto-discover Cloud Run service URL if AGENT_SERVICE_URL is not explicitly set
if [ -z "$AGENT_SERVICE_URL" ] && command -v gcloud &> /dev/null; then
    echo -e "${COLOR_INFO}Checking for deployed Cloud Run service URL (adk-a2a-service)...${COLOR_RESET}"
    CLOUD_RUN_URL=$(gcloud run services describe adk-a2a-service --region="${CLOUD_RUN_REGION:-us-central1}" --format="value(status.url)" 2>/dev/null || echo "")
    if [ -n "$CLOUD_RUN_URL" ]; then
        AGENT_SERVICE_URL="$CLOUD_RUN_URL"
        echo -e "• Discovered Cloud Run HTTPS URL: ${COLOR_SUCCESS}${AGENT_SERVICE_URL}${COLOR_RESET}"
    fi
fi

if [ -z "$AGENT_SERVICE_URL" ]; then
    AGENT_SERVICE_URL="https://example.com/adk-agent"
fi

echo -e "• Target GE App ID:     ${COLOR_SUCCESS}${APP_ID}${COLOR_RESET}"
echo -e "• A2A Agent Service URL:${COLOR_SUCCESS}${AGENT_SERVICE_URL}${COLOR_RESET}"
echo -e "• Todoist Client ID:    ${COLOR_SUCCESS}${TODOIST_CLIENT_ID}${COLOR_RESET}"

# Verify HTTPS requirement for Gemini Enterprise
if [[ ! "$AGENT_SERVICE_URL" =~ ^https:// ]]; then
    echo -e "\n${COLOR_ERROR}❌ ERROR: Gemini Enterprise strictly requires an HTTPS endpoint URL ('${AGENT_SERVICE_URL}' is invalid).${COLOR_RESET}"
    echo -e "👉 Option 1: Deploy your agent to Google Cloud Run: ${COLOR_INFO}make deploy-cloud-run${COLOR_RESET}"
    echo -e "👉 Option 2: Set GE_AGENT_SERVICE_URL=\"https://your-domain.com\" in your .env file.\n"
    exit 1
fi

# Step 1: Add Authorization Resource to Gemini Enterprise
echo -e "\n${COLOR_INFO}[Step 1/2] Creating Todoist OAuth 2.0 Authorization Resource in GE...${COLOR_RESET}"
AUTH_URI="https://todoist.com/oauth/authorize?client_id=${TODOIST_CLIENT_ID}&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&scope=data%3Aread_write%20task%3Aadd&response_type=code&access_type=offline&prompt=consent"

if command -v gcloud &> /dev/null && [ "$PROJECT_NUMBER" != "YOUR_PROJECT_NUMBER" ]; then
    ACCESS_TOKEN=$(gcloud auth print-access-token)
    AUTH_ENDPOINT="https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/${LOCATION}/authorizations?authorizationId=${AUTH_ID}"

    echo "Registering authorization resource at: $AUTH_ENDPOINT"
    AUTH_RES=$(curl -s -X POST "$AUTH_ENDPOINT" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        -d "{
            \"name\": \"projects/${PROJECT_NUMBER}/locations/${LOCATION}/authorizations/${AUTH_ID}\",
            \"serverSideOauth2\": {
                \"clientId\": \"${TODOIST_CLIENT_ID}\",
                \"clientSecret\": \"${TODOIST_CLIENT_SECRET}\",
                \"authorizationUri\": \"${AUTH_URI}\",
                \"tokenUri\": \"https://todoist.com/oauth/access_token\"
            }
        }")
    echo "$AUTH_RES"
fi

# Step 2: Register A2A Agent with Gemini Enterprise
if [ "$APP_ID" != "YOUR_APP_ID" ]; then
    echo -e "\n${COLOR_INFO}[Step 2/2] Registering A2A Agent in Gemini Enterprise Assistant...${COLOR_RESET}"

    AGENT_CARD_JSON="{\"protocolVersion\":\"0.3.0\",\"name\":\"${AGENT_NAME}\",\"description\":\"ADK 2.0 A2A Agent managing Todoist tasks with OAuth 2.0 and weather computation.\",\"url\":\"${AGENT_SERVICE_URL}\",\"version\":\"1.0.0\",\"defaultInputModes\":[\"text/plain\",\"application/json\"],\"defaultOutputModes\":[\"text/plain\",\"application/json\"],\"capabilities\":{\"streaming\":false},\"skills\":[{\"id\":\"todoist_management\",\"name\":\"Todoist Task Management\",\"description\":\"Manage user tasks, list active tasks, create new items, and complete tasks in Todoist.\",\"tags\":[\"productivity\",\"todoist\",\"tasks\"],\"examples\":[\"List my todoist tasks\",\"Create a task to review ADK architecture\",\"Complete task 101\"]},{\"id\":\"weather_analysis\",\"name\":\"Weather Analysis\",\"description\":\"Query global city weather conditions and temperature forecasts.\",\"tags\":[\"weather\",\"meteorology\",\"forecast\"],\"examples\":[\"What is the weather in Tokyo?\",\"Compare temperature between Paris and London\"]},{\"id\":\"calculator\",\"name\":\"Calculator\",\"description\":\"Evaluate mathematical formulas and numerical comparisons.\",\"tags\":[\"math\",\"calculator\"],\"examples\":[\"Calculate 25 * 4 + 10\",\"Compute 100 / 4\"]}]}"

    ESCAPED_AGENT_CARD=$(echo "$AGENT_CARD_JSON" | sed 's/"/\\"/g')

    if command -v gcloud &> /dev/null && [ "$PROJECT_NUMBER" != "YOUR_PROJECT_NUMBER" ]; then
        REGISTER_ENDPOINT="https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents"

        echo "Registering agent at: $REGISTER_ENDPOINT"
        REG_RES=$(curl -s -X POST "$REGISTER_ENDPOINT" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "Content-Type: application/json" \
            -H "X-Goog-User-Project: ${PROJECT_ID}" \
            -d "{
                \"name\": \"${AGENT_NAME}\",
                \"displayName\": \"${AGENT_DISPLAY_NAME}\",
                \"description\": \"ADK 2.0 A2A Agent managing Todoist tasks with OAuth 2.0 and weather computation.\",
                \"a2aAgentDefinition\": {
                    \"jsonAgentCard\": \"${ESCAPED_AGENT_CARD}\"
                },
                \"authorizationConfig\": {
                    \"agentAuthorization\": \"projects/${PROJECT_NUMBER}/locations/${LOCATION}/authorizations/${AUTH_ID}\"
                }
            }")
        echo "$REG_RES"
    fi

    echo -e "\n${COLOR_SUCCESS}✅ Registration sequence complete!${COLOR_RESET}"
    echo -e "You can view your agent in the Gemini Enterprise Console at:"
    echo -e "https://console.cloud.google.com/gemini-enterprise/apps/${APP_ID}/agents"
else
    echo -e "\n${COLOR_WARN}Skipping Step 2 because no valid GE_APP_ID was provided.${COLOR_RESET}"
fi
