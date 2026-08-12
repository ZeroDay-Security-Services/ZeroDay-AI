"""Base agent class -- specialized system prompt + tool subset over shared factory client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.llm_factory import get_llm_client
from app.ai_core.tools import execute_tool
from app.core.config import get_settings


@dataclass
class AgentResult:
    agent: str
    reply: str
    tool_calls_made: int
    raw_turns: list[dict[str, Any]]


class BaseAgent:
    name: str = "base"
    system_prompt: str = ""
    tool_names: list[str] = []

    def __init__(self) -> None:
        self.settings = get_settings()

    def _filtered_tools(self, all_tools: list[dict]) -> list[dict]:
        if not self.tool_names:
            return all_tools
        return [t for t in all_tools if t["name"] in self.tool_names]

    async def _run_loop(
        self,
        messages: list[dict[str, Any]],
        db: AsyncSession,
    ) -> tuple[list[dict[str, Any]], int]:
        """Core agentic loop — shared by run() and run_with_history()."""
        from app.ai_core.tools import TOOL_DEFINITIONS

        client = get_llm_client()
        tools = self._filtered_tools(TOOL_DEFINITIONS)
        new_turns: list[dict[str, Any]] = []
        tool_calls_made = 0

        for _ in range(self.settings.assistant_max_tool_rounds):
            response = await client.create_message(
                system=self.system_prompt,
                messages=messages,
                tools=tools,
                max_tokens=2048,
            )
            content = response.get("content", [])
            turn = {"role": "assistant", "content": content}
            messages.append(turn)
            new_turns.append(turn)

            if response.get("stop_reason") != "tool_use":
                break

            tool_use_blocks = [b for b in content if b.get("type") == "tool_use"]
            if not tool_use_blocks:
                break

            tool_results = []
            for block in tool_use_blocks:
                result = await execute_tool(block["name"], block.get("input", {}), db)
                tool_calls_made += 1
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": str(result),
                    }
                )

            tool_turn = {"role": "user", "content": tool_results}
            messages.append(tool_turn)
            new_turns.append(tool_turn)

        return new_turns, tool_calls_made

    async def run(self, message: str, db: AsyncSession) -> AgentResult:
        """Run agent with just a single user message (no prior history)."""
        messages: list[dict[str, Any]] = [{"role": "user", "content": message}]
        new_turns, tool_calls_made = await self._run_loop(messages, db)

        reply = ""
        for turn in reversed(new_turns):
            if turn["role"] == "assistant":
                reply = "\n".join(
                    b.get("text", "")
                    for b in turn["content"]
                    if isinstance(b, dict) and b.get("type") == "text"
                )
                break

        return AgentResult(
            agent=self.name,
            reply=reply,
            tool_calls_made=tool_calls_made,
            raw_turns=new_turns,
        )

    async def run_with_history(
        self,
        message: str,
        history: list[dict[str, Any]],
        db: AsyncSession,
    ) -> AgentResult:
        """Run agent with full prior conversation history for context."""
        # Build messages: history + new user message
        messages: list[dict[str, Any]] = list(history) + [
            {"role": "user", "content": message}
        ]
        new_turns, tool_calls_made = await self._run_loop(messages, db)

        reply = ""
        for turn in reversed(new_turns):
            if turn["role"] == "assistant":
                reply = "\n".join(
                    b.get("text", "")
                    for b in turn["content"]
                    if isinstance(b, dict) and b.get("type") == "text"
                )
                break

        return AgentResult(
            agent=self.name,
            reply=reply,
            tool_calls_made=tool_calls_made,
            raw_turns=new_turns,
        )

