"""Google Gemini provider client (REST API, no Python SDK dependency).

Gemini has its own API format -- this client converts Anthropic-format
messages and tool definitions to Gemini's `contents` + `functionDeclarations`
shape and normalizes the response back to Anthropic content blocks.

Free models available with a Gemini API key (gemini.google.com/app or
aistudio.google.com):
  gemini-2.0-flash          (fastest, great tool-use support)
  gemini-2.0-flash-thinking (reasoning model)
  gemini-1.5-pro            (most capable)
  gemini-1.5-flash          (balanced)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.ai_core.providers.base import BaseLLMClient

logger = logging.getLogger("zeroday.ai_core.gemini")

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _anthropic_tools_to_gemini(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "functionDeclarations": [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get(
                        "input_schema", {"type": "object", "properties": {}}
                    ),
                }
            ]
        }
        for t in tools
    ]


def _content_str(content: str | list[dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content if b.get("type") == "text")


def _anthropic_messages_to_gemini(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert Anthropic message list to Gemini `contents` list."""
    out: list[dict[str, Any]] = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        gemini_role = "model" if role == "assistant" else "user"

        if isinstance(content, str):
            out.append({"role": gemini_role, "parts": [{"text": content}]})
            continue

        parts: list[dict[str, Any]] = []
        for block in content:
            btype = block.get("type")
            if btype == "text":
                parts.append({"text": block.get("text", "")})
            elif btype == "tool_use":
                parts.append(
                    {
                        "functionCall": {
                            "name": block["name"],
                            "args": block.get("input", {}),
                        }
                    }
                )
            elif btype == "tool_result":
                parts.append(
                    {
                        "functionResponse": {
                            "name": block.get("tool_use_id", "unknown"),
                            "response": {"content": block.get("content", "")},
                        }
                    }
                )

        if parts:
            out.append({"role": gemini_role, "parts": parts})

    return out


def _gemini_response_to_anthropic(body: dict[str, Any]) -> dict[str, Any]:
    candidates = body.get("candidates", [])
    if not candidates:
        return {"content": [{"type": "text", "text": ""}], "stop_reason": "end_turn"}

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts", [])

    content: list[dict[str, Any]] = []
    has_tool_call = False

    for part in parts:
        if "text" in part:
            content.append({"type": "text", "text": part["text"]})
        elif "functionCall" in part:
            fc = part["functionCall"]
            content.append(
                {
                    "type": "tool_use",
                    "id": f"gemini_{fc['name']}",
                    "name": fc["name"],
                    "input": fc.get("args", {}),
                }
            )
            has_tool_call = True

    stop_reason = "tool_use" if has_tool_call else "end_turn"
    return {"content": content, "stop_reason": stop_reason}


class GeminiClient(BaseLLMClient):
    def __init__(
        self, api_key: str, model: str = "gemini-2.0-flash", timeout: float = 60.0
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
        url = f"{GEMINI_BASE}/{self.model}:generateContent?key={self.api_key}"

        payload: dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": _anthropic_messages_to_gemini(messages),
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if tools:
            payload["tools"] = _anthropic_tools_to_gemini(tools)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        return _gemini_response_to_anthropic(response.json())
