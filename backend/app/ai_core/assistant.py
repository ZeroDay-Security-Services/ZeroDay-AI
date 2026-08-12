"""AI Assistant orchestration: tool-calling loop over any configured LLM.

Provider is selected at runtime via LLM_PROVIDER env var (see
app/ai_core/llm_factory.py). The loop logic is identical regardless of
which provider is active -- all providers normalize to Anthropic's
content-block format at the client level.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.llm_factory import LLMNotConfiguredError, get_llm_client
from app.ai_core.tools import TOOL_DEFINITIONS, execute_tool
from app.core.config import get_settings

SYSTEM_PROMPT = """You are the ZeroDay Security AI assistant, built by ZeroDay Security Services.
You help security analysts assess vulnerabilities, check compliance posture (including
CERT-In and DPDP Act requirements for Indian organizations), review threat intelligence,
and spot behavioral anomalies. Use the tools available to you to ground your answers in
real data rather than guessing -- always call a tool when one is relevant instead of
estimating a CVSS/EPSS score, compliance result, or anomaly finding yourself. Be direct,
concise, and precise; this is a professional security tool, not a casual chatbot."""


class AssistantError(Exception):
    pass


class AssistantService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def run_turn(self, messages: list[dict], db: AsyncSession) -> list[dict]:
        try:
            client = get_llm_client()
        except LLMNotConfiguredError as exc:
            raise AssistantError(str(exc)) from exc

        working_messages = list(messages)
        new_turns: list[dict] = []

        for _ in range(self.settings.assistant_max_tool_rounds):
            response = await client.create_message(
                system=SYSTEM_PROMPT,
                messages=working_messages,
                tools=TOOL_DEFINITIONS,
            )
            assistant_content = response.get("content", [])
            assistant_turn = {"role": "assistant", "content": assistant_content}
            working_messages.append(assistant_turn)
            new_turns.append(assistant_turn)

            if response.get("stop_reason") != "tool_use":
                return new_turns

            tool_use_blocks = [
                b for b in assistant_content if b.get("type") == "tool_use"
            ]
            if not tool_use_blocks:
                return new_turns

            tool_results = []
            for block in tool_use_blocks:
                result = await execute_tool(block["name"], block.get("input", {}), db)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": str(result),
                    }
                )

            tool_result_turn = {"role": "user", "content": tool_results}
            working_messages.append(tool_result_turn)
            new_turns.append(tool_result_turn)

        return new_turns


def extract_text(content: list[dict]) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(
        block.get("text", "") for block in content if block.get("type") == "text"
    )
