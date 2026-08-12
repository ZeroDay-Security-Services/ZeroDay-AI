import json
import respx
from httpx import Response

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


async def _authed_headers(async_client, email="agents@zeroday.dev"):
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Agent User", "password": "correcthorse123"},
    )
    login = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correcthorse123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_list_agents_returns_five(async_client):
    response = await async_client.get("/api/v1/agents/")
    assert response.status_code == 200
    agents = response.json()["agents"]
    assert len(agents) == 5
    ids = {a["id"] for a in agents}
    assert ids == {
        "vulnerability_analyst",
        "threat_intelligence",
        "soc_analyst",
        "pentest_assistant",
        "security_automation",
    }


async def test_unknown_agent_returns_400(async_client):
    headers = await _authed_headers(async_client, email="agents_unk@zeroday.dev")
    response = await async_client.post(
        "/api/v1/agents/run",
        json={"agent": "nonexistent", "message": "hello"},
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNKNOWN_AGENT"


async def test_agent_requires_auth(async_client):
    response = await async_client.post(
        "/api/v1/agents/run",
        json={"agent": "soc_analyst", "message": "test"},
    )
    assert response.status_code == 401


@respx.mock
async def test_soc_analyst_agent_via_groq(async_client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    get_settings.cache_clear()
    headers = await _authed_headers(async_client, email="agents_soc@zeroday.dev")

    respx.post(GROQ_URL).mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "P2 alert -- suspicious IOC match.",
                            "tool_calls": None,
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        )
    )

    response = await async_client.post(
        "/api/v1/agents/run",
        json={"agent": "soc_analyst", "message": "Investigate 185.220.101.5"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["agent"] == "soc_analyst"
    assert "P2" in body["reply"]
    get_settings.cache_clear()


@respx.mock
async def test_vuln_analyst_agent_via_nvidia_nemotron(async_client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-nvidia-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-super-49b-v1")
    get_settings.cache_clear()
    headers = await _authed_headers(async_client, email="agents_nvidia@zeroday.dev")

    respx.post(NVIDIA_URL).mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Nemotron Super analysis: CVE-2021-44228 is critical.",
                            "tool_calls": None,
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        )
    )

    response = await async_client.post(
        "/api/v1/agents/run",
        json={"agent": "vulnerability_analyst", "message": "Analyze CVE-2021-44228"},
        headers=headers,
    )
    assert response.status_code == 200
    assert "Nemotron" in response.json()["reply"]
    get_settings.cache_clear()
