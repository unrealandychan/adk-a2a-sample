#!/usr/bin/env bash
# =============================================================================
# Register A2A Agent with Gemini Enterprise (GE) / Discovery Engine
# Reference: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent
# =============================================================================

set -euo pipefail

# Configuration with environment defaults
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
LOCATION="${GE_LOCATION:-global}"
ENDPOINT_LOCATION="${GE_ENDPOINT_LOCATION:-global}"
APP_ID="${GE_APP_ID:-default-gemini-enterprise-app}"
AUTH_ID="${GE_AUTH_ID:-todoist-oauth-auth}"
AGENT_NAME="${GE_AGENT_NAME:-todoist_weather_agent}"
AGENT_DISPLAY_NAME="${GE_AGENT_DISPLAY_NAME:-Todoist & Weather Assistant}"
AGENT_SERVICE_URL="${GE_AGENT_SERVICE_URL:-http://127.0.0.1:8080}"

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
    echo -e "${COLOR_WARN}No GOOGLE_CLOUD_PROJECT environment variable provided.${COLOR_RESET}"
    echo -e "Attempting to retrieve active project from gcloud..."
    if command -v gcloud &> /dev/null; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
    fi
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${COLOR_ERROR}ERROR: GCP Project ID is required. Export GOOGLE_CLOUD_PROJECT=your-project-id${COLOR_RESET}"
    exit 1
fi

echo -e "• GCP Project ID:       ${COLOR_SUCCESS}${PROJECT_ID}${COLOR_RESET}"
echo -e "• GE Location:          ${COLOR_SUCCESS}${LOCATION}${COLOR_RESET}"
echo -e "• GE App ID:            ${COLOR_SUCCESS}${APP_ID}${COLOR_RESET}"
echo -e "• A2A Agent Service URL:${COLOR_SUCCESS}${AGENT_SERVICE_URL}${COLOR_RESET}"
echo -e "• Todoist Client ID:    ${COLOR_SUCCESS}${TODOIST_CLIENT_ID}${COLOR_RESET}"

# Fetch Project Number via gcloud
if command -v gcloud &> /dev/null; then
    echo -e "\n${COLOR_INFO}Fetching GCP Project Number...${COLOR_RESET}"
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")
    if [ -n "$PROJECT_NUMBER" ]; then
        echo -e "• GCP Project Number:   ${COLOR_SUCCESS}${PROJECT_NUMBER}${COLOR_RESET}"
    fi
else
    PROJECT_NUMBER="YOUR_PROJECT_NUMBER"
fi

# Step 1: Add Authorization Resource to Gemini Enterprise
echo -e "\n${COLOR_INFO}[Step 1/2] Creating Todoist OAuth 2.0 Authorization Resource in GE...${COLOR_RESET}"
AUTH_URI="https://todoist.com/oauth/authorize?client_id=${TODOIST_CLIENT_ID}&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&scope=data%3Aread_write%20task%3Aadd&response_type=code&access_type=offline&prompt=consent"

if command -v gcloud &> /dev/null && [ "$PROJECT_NUMBER" != "YOUR_PROJECT_NUMBER" ]; then
    ACCESS_TOKEN=$(gcloud auth print-access-token)
    AUTH_ENDPOINT="https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/${LOCATION}/authorizations?authorizationId=${AUTH_ID}"

    echo "Registering authorization resource at: $AUTH_ENDPOINT"
    curl -s -X POST "$AUTH_ENDPOINT" \
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
        }" || echo -e "${COLOR_WARN}Authorization resource already exists or returned a non-zero status.${COLOR_RESET}"
fi

# Step 2: Register A2A Agent with Gemini Enterprise
echo -e "\n${COLOR_INFO}[Step 2/2] Registering A2A Agent in Gemini Enterprise Assistant...${COLOR_RESET}"

AGENT_CARD_JSON="{\"protocolVersion\":\"0.3.0\",\"name\":\"${AGENT_NAME}\",\"description\":\"ADK 2.0 A2A Agent managing Todoist tasks with OAuth 2.0 and weather computation.\",\"url\":\"${AGENT_SERVICE_URL}\",\"version\":\"1.0.0\",\"defaultInputModes\":[\"text/plain\",\"application/json\"],\"defaultOutputModes\":[\"text/plain\",\"application/json\"],\"capabilities\":{\"streaming\":false},\"skills\":[{\"id\":\"todoist_management\",\"name\":\"Todoist Task Management\",\"description\":\"Manage user tasks, list active tasks, create new items, and complete tasks in Todoist.\",\"tags\":[\"productivity\",\"todoist\",\"tasks\"],\"examples\":[\"List my todoist tasks\",\"Create a task to review ADK architecture\",\"Complete task 101\"]},{\"id\":\"weather_analysis\",\"name\":\"Weather Analysis\",\"description\":\"Query global city weather conditions and temperature forecasts.\",\"tags\":[\"weather\",\"meteorology\",\"forecast\"],\"examples\":[\"What is the weather in Tokyo?\",\"Compare temperature between Paris and London\"]},{\"id\":\"calculator\",\"name\":\"Calculator\",\"description\":\"Evaluate mathematical formulas and numerical comparisons.\",\"tags\":[\"math\",\"calculator\"],\"examples\":[\"Calculate 25 * 4 + 10\",\"Compute 100 / 4\"]}]}"

ESCAPED_AGENT_CARD=$(echo "$AGENT_CARD_JSON" | sed 's/"/\\"/g')

if command -v gcloud &> /dev/null && [ "$PROJECT_NUMBER" != "YOUR_PROJECT_NUMBER" ]; then
    REGISTER_ENDPOINT="https://${ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents"

    echo "Registering agent at: $REGISTER_ENDPOINT"
    curl -s -X POST "$REGISTER_ENDPOINT" \
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
        }" || echo -e "${COLOR_WARN}Agent registration completed or returned a status code.${COLOR_RESET}"
fi

echo -e "\n${COLOR_SUCCESS}✅ Registration sequence complete!${COLOR_RESET}"
echo -e "You can also register manually via the Google Cloud Console at:"
echo -e "https://console.cloud.google.com/gemini-enterprise/apps/${APP_ID}/agents"

