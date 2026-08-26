"""HTTP Client for communicating with remote A2A agents."""

import httpx

from adk_a2a.core.logging import get_logger
from adk_a2a.domain.exceptions import A2ACommunicationError
from adk_a2a.domain.models import AgentCard, AgentResponse, AgentTask

logger = get_logger(__name__)


class RemoteA2aClient:
    """Client adapter for discovering and invoking remote A2A compliant agents."""

    def __init__(self, agent_card_url: str, timeout_seconds: float = 10.0) -> None:
        self.agent_card_url = agent_card_url
        self.timeout_seconds = timeout_seconds
        self._cached_card: AgentCard | None = None

    async def fetch_agent_card(self) -> AgentCard:
        """Retrieves and caches the remote agent's descriptor card."""
        if self._cached_card is not None:
            return self._cached_card

        logger.info("Discovering remote A2A agent from: %s", self.agent_card_url)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(self.agent_card_url)
                resp.raise_for_status()
                card_data = resp.json()
                self._cached_card = AgentCard(**card_data)
                return self._cached_card
        except Exception as exc:
            logger.error("Failed to fetch agent card from %s: %s", self.agent_card_url, exc)
            raise A2ACommunicationError(
                f"Could not fetch Agent Card from '{self.agent_card_url}': {exc}"
            ) from exc

    async def dispatch_task(self, task: AgentTask) -> AgentResponse:
        """Dispatches an AgentTask to the remote A2A agent's execution endpoint."""
        card = await self.fetch_agent_card()
        endpoint = card.endpoints.get("task_execution")

        if not endpoint:
            raise A2ACommunicationError(
                f"Remote agent '{card.name}' did not expose a 'task_execution' endpoint in its card."
            )

        logger.info("Delegating task %s to remote A2A agent at %s", task.task_id, endpoint)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(endpoint, json=task.model_dump())
                resp.raise_for_status()
                return AgentResponse(**resp.json())
        except Exception as exc:
            logger.error("Failed to execute remote A2A task on %s: %s", endpoint, exc)
            raise A2ACommunicationError(
                f"A2A task execution failed on remote endpoint '{endpoint}': {exc}"
            ) from exc
