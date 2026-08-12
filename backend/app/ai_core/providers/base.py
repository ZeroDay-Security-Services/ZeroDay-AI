"""Abstract base class for all LLM provider clients.

All providers normalize their responses to Anthropic's content-block
format so the existing assistant.py tool-calling loop works unchanged
regardless of which provider is active.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    @abstractmethod
    async def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        Args:
            system: System prompt string.
            messages: Anthropic-format message list (role + content).
            tools: Anthropic-format tool definitions.
            max_tokens: Maximum tokens to generate.

        Returns:
            Anthropic-compatible response dict:
            {
              "content": [{"type":"text","text":"..."} | {"type":"tool_use","id":"...","name":"...","input":{...}}],
              "stop_reason": "end_turn" | "tool_use"
            }
        """
        ...
