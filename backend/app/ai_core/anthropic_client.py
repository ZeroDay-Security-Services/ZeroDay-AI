"""Thin client for the Anthropic Messages API.

Implemented directly against the documented REST endpoint (no `anthropic`
SDK dependency) since the project already has httpx. This is the only LLM
provider actually reachable and testable from this environment: Gemini
and Ollama endpoints aren't on this sandbox's network allowlist and no
credentials for them are available, so wiring those in now would be
unverifiable code. The client is provider-agnostic at the call site
(AssistantService doesn't know it's talking to Anthropic specifically),
so a Gemini/Ollama client can be added alongside this one later without
changing the assistant's tool-calling logic.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger("zeroday.ai_core")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"


class AnthropicNotConfiguredError(Exception):
    """Raised when ANTHROPIC_API_KEY is not set."""


class AnthropicClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout
        self.settings = get_settings()

    async def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        if not self.settings.anthropic_api_key:
            raise AnthropicNotConfiguredError(
                "ANTHROPIC_API_KEY is not configured on the server"
            )

        payload: dict[str, Any] = {
            "model": self.settings.anthropic_model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                ANTHROPIC_API_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()
