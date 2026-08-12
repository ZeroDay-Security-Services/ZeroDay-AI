"""OpenAI-compatible provider client.

A single implementation that covers every provider that speaks the
OpenAI Chat Completions API:
  - NVIDIA NIM  (Nemotron Ultra/Super, Llama, etc.)  base_url = integrate.api.nvidia.com/v1
  - Groq        (Llama 3, Mixtral, Gemma)            base_url = api.groq.com/openai/v1
  - Ollama      (any local model)                    base_url = localhost:11434/v1
  - OpenAI      (GPT-4o, etc.)                       base_url = api.openai.com/v1

All four use the same /chat/completions endpoint and the same tool-call
format, so one client handles all of them.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.ai_core.providers.base import BaseLLMClient

logger = logging.getLogger("zeroday.ai_core.openai_compat")


# ─── Format converters (Anthropic ↔ OpenAI) ──────────────────────────────────


def _anthropic_tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Anthropic-format tool definitions to OpenAI function format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get(
                    "input_schema", {"type": "object", "properties": {}}
                ),
            },
        }
        for t in tools
    ]


def _anthropic_messages_to_openai(
    messages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Convert Anthropic-format messages to OpenAI messages list.

    Handles the four content shapes that appear in the assistant.py loop:
      1. user  message with plain string content
      2. user  message with tool_result content blocks
      3. asst  message with text + tool_use content blocks
      4. asst  message with plain string content
    """
    out: list[dict[str, Any]] = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        if not isinstance(content, list):
            out.append({"role": role, "content": str(content)})
            continue

        # Separate text blocks from tool blocks
        text_blocks = [b for b in content if b.get("type") == "text"]
        tool_use_blocks = [b for b in content if b.get("type") == "tool_use"]
        tool_result_blocks = [b for b in content if b.get("type") == "tool_result"]

        if tool_result_blocks:
            # User turn carrying tool results → one "tool" message per result
            for tr in tool_result_blocks:
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.get("tool_use_id", ""),
                        "content": tr.get("content", ""),
                    }
                )
            continue

        if tool_use_blocks:
            # Assistant turn with tool calls
            text_content = "\n".join(b.get("text", "") for b in text_blocks) or None
            tool_calls = [
                {
                    "id": b.get("id", "call_" + b.get("name", "")),
                    "type": "function",
                    "function": {
                        "name": b["name"],
                        "arguments": json.dumps(b.get("input", {})),
                    },
                }
                for b in tool_use_blocks
            ]
            out.append(
                {"role": "assistant", "content": text_content, "tool_calls": tool_calls}
            )
            continue

        # Plain text blocks
        text = "\n".join(b.get("text", "") for b in text_blocks)
        out.append({"role": role, "content": text})

    return out


def _openai_response_to_anthropic(choice: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAI choices[0] to an Anthropic-style response dict."""
    message = choice.get("message", {})
    finish_reason = choice.get("finish_reason", "stop")

    content: list[dict[str, Any]] = []

    if message.get("content"):
        content.append({"type": "text", "text": message["content"]})

    for tc in message.get("tool_calls") or []:
        try:
            args = json.loads(tc["function"]["arguments"])
        except (json.JSONDecodeError, KeyError):
            args = {}
        content.append(
            {
                "type": "tool_use",
                "id": tc.get("id", "call_unknown"),
                "name": tc["function"]["name"],
                "input": args,
            }
        )

    stop_reason = "tool_use" if finish_reason == "tool_calls" else "end_turn"
    return {"content": content, "stop_reason": stop_reason}


# ─── Client ──────────────────────────────────────────────────────────────────


class OpenAICompatClient(BaseLLMClient):
    """Single client for NVIDIA NIM, Groq, Ollama, OpenAI, and any other
    OpenAI-compatible endpoint."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    async def create_message(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        openai_messages = [
            {"role": "system", "content": system}
        ] + _anthropic_messages_to_openai(messages)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = _anthropic_tools_to_openai(tools)
            payload["tool_choice"] = "auto"

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        body = response.json()
        choices = body.get("choices", [])
        if not choices:
            return {
                "content": [{"type": "text", "text": ""}],
                "stop_reason": "end_turn",
            }

        return _openai_response_to_anthropic(choices[0])
