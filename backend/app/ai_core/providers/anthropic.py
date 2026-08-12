"""Anthropic Claude provider (moved from app/ai_core/anthropic_client.py)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.ai_core.providers.base import BaseLLMClient

logger = logging.getLogger("zeroday.ai_core.anthropic")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"


class AnthropicClient(BaseLLMClient):
    def __init__(
        self, api_key: str, model: str = "claude-sonnet-4-6", timeout: float = 60.0
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                ANTHROPIC_API_URL, json=payload, headers=headers
            )
            response.raise_for_status()

        body = response.json()
        return {
            "content": body.get("content", []),
            "stop_reason": body.get("stop_reason", "end_turn"),
        }
