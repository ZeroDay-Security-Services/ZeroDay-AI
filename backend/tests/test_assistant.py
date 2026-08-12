"""Assistant tests -- now multi-provider aware."""

import respx
from httpx import Response

from app.core.config import get_settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
GEMINI_URL_PREFIX = "https://generativelanguage.googleapis.com"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


async def _authed_headers(async_client, email="assistant@zeroday.dev"):
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Assistant User",
            "password": "correcthorse123",
        },
    )
    login = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correcthorse123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_chat_without_any_api_key_returns_503(async_client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    headers = await _authed_headers(async_client)

    response = await async_client.post(
        "/api/v1/assistant/chat", json={"message": "hello"}, headers=headers
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ASSISTANT_NOT_CONFIGURED"
    get_settings.cache_clear()


async def test_chat_requires_auth(async_client):
    response = await async_client.post("/api/v1/assistant/chat", json={"message": "hi"})
    assert response.status_code == 401


@respx.mock
async def test_chat_via_groq_provider(async_client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    get_settings.cache_clear()
    headers = await _authed_headers(async_client, email="chat_groq@zeroday.dev")

    respx.post(GROQ_URL).mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Groq reply here",
                            "tool_calls": None,
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        )
    )

    response = await async_client.post(
        "/api/v1/assistant/chat", json={"message": "hi"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["reply"] == "Groq reply here"
    get_settings.cache_clear()


@respx.mock
async def test_chat_via_nvidia_nemotron(async_client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-ultra-253b-v1")
    get_settings.cache_clear()
    headers = await _authed_headers(async_client, email="chat_nvidia@zeroday.dev")

    respx.post(NVIDIA_URL).mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Nemotron Ultra reply",
                            "tool_calls": None,
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        )
    )

    response = await async_client.post(
        "/api/v1/assistant/chat",
        json={"message": "Analyze CVE-2024-0001"},
        headers=headers,
    )
    assert response.status_code == 200
    assert "Nemotron" in response.json()["reply"]
    get_settings.cache_clear()


@respx.mock
async def test_chat_via_gemini(async_client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    get_settings.cache_clear()
    headers = await _authed_headers(async_client, email="chat_gemini@zeroday.dev")

    respx.post(GEMINI_URL_PREFIX).mock(
        return_value=Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [{"text": "Gemini reply"}],
                        },
                        "finishReason": "STOP",
                    }
                ]
            },
        )
    )

    response = await async_client.post(
        "/api/v1/assistant/chat", json={"message": "hello"}, headers=headers
    )
    assert response.status_code == 200
    assert "Gemini" in response.json()["reply"]
    get_settings.cache_clear()


@respx.mock
async def test_groq_tool_call_executes_real_engine(async_client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    get_settings.cache_clear()
    headers = await _authed_headers(async_client, email="chat_groq_tool@zeroday.dev")

    import json

    tool_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "type": "function",
                            "function": {
                                "name": "scan_cloud_compliance",
                                "arguments": json.dumps(
                                    {"config": {"public_read": True}}
                                ),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ]
    }
    final_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Found critical findings: STORAGE-001 violated.",
                    "tool_calls": None,
                },
                "finish_reason": "stop",
            }
        ]
    }

    route = respx.post(GROQ_URL)
    route.side_effect = [
        Response(200, json=tool_response),
        Response(200, json=final_response),
    ]

    response = await async_client.post(
        "/api/v1/assistant/chat",
        json={"message": "Is my bucket compliant?"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool_calls_made"] == 1
    assert "STORAGE-001" in body["reply"]
    get_settings.cache_clear()


async def test_list_conversations_empty(async_client):
    headers = await _authed_headers(async_client, email="chat_list@zeroday.dev")
    response = await async_client.get(
        "/api/v1/assistant/conversations", headers=headers
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_get_unknown_conversation_404(async_client):
    headers = await _authed_headers(async_client, email="chat_404@zeroday.dev")
    response = await async_client.get(
        "/api/v1/assistant/conversations/nope", headers=headers
    )
    assert response.status_code == 404
