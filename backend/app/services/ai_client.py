"""Generic OpenAI-compatible LLM client for Ollama and OpenAI APIs."""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0  # seconds


class AIClient:
    """Thin wrapper around the OpenAI-compatible chat completions API.

    Works with both Ollama (``/v1/chat/completions``) and any
    OpenAI-compatible endpoint using the same code path.
    """

    def __init__(self, base_url: str, model: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _completions_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def chat(self, messages: list[dict], max_tokens: int = 500) -> str | None:
        """Send a chat completion request synchronously.

        Returns the assistant message content or ``None`` on any failure
        (timeout, network, bad response) so callers can fall back gracefully.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        try:
            resp = httpx.post(
                self._completions_url(),
                headers=self._headers(),
                json=payload,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.warning("AI chat request failed: %s", exc)
            return None


def get_ai_client() -> AIClient | None:
    """Return a configured AIClient or None if AI is not configured."""
    if not settings.ai_provider:
        return None
    return AIClient(
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        api_key=settings.ai_api_key,
    )
