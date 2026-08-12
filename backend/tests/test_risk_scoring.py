"""Risk scoring endpoint tests. NVD/CISA-KEV/EPSS calls are mocked with respx
since this environment has no network access to those live services --
this verifies the parsing, context-derivation, and scoring pipeline end to
end without depending on external connectivity."""

from __future__ import annotations

import respx
from httpx import Response

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://api.first.org/data/v1/epss"

MOCK_NVD_RESPONSE = {
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2024-12345",
                "published": "2024-06-01T00:00:00.000",
                "lastModified": "2024-06-05T00:00:00.000",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "A critical remote code execution vulnerability.",
                    }
                ],
                "references": [
                    {"url": "https://example.com/advisory"},
                    {"url": "https://github.com/example/exploit-poc"},
                ],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "cvssData": {
                                "baseScore": 9.8,
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                                "attackVector": "NETWORK",
                                "attackComplexity": "LOW",
                                "privilegesRequired": "NONE",
                                "userInteraction": "NONE",
                                "scope": "UNCHANGED",
                                "confidentialityImpact": "HIGH",
                                "integrityImpact": "HIGH",
                                "availabilityImpact": "HIGH",
                            }
                        }
                    ]
                },
            },
            "configurations": [],
        }
    ]
}

MOCK_EPSS_RESPONSE = {
    "data": [
        {
            "cve": "CVE-2024-12345",
            "epss": "0.55",
            "percentile": "0.91",
            "date": "2024-06-10",
        }
    ]
}


@respx.mock
async def test_score_vulnerability_enhanced_framework(async_client):
    respx.get(NVD_URL).mock(return_value=Response(200, json=MOCK_NVD_RESPONSE))
    respx.get(CISA_KEV_URL).mock(
        return_value=Response(200, json={"vulnerabilities": []})
    )
    respx.get(EPSS_URL).mock(return_value=Response(200, json=MOCK_EPSS_RESPONSE))

    response = await async_client.post(
        "/api/v1/risk/score",
        json={
            "cve_id": "CVE-2024-12345",
            "asset_criticality": 8,
            "is_internet_facing": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cve_id"] == "CVE-2024-12345"
    assert 0 <= body["risk_score"] <= 100
    assert body["priority"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    assert body["cve_intelligence"]["cvss_score"] == 9.8
    assert body["cve_intelligence"]["cisa_kev"] is False


@respx.mock
async def test_score_vulnerability_risk_based_framework(async_client):
    respx.get(NVD_URL).mock(return_value=Response(200, json=MOCK_NVD_RESPONSE))
    respx.get(CISA_KEV_URL).mock(
        return_value=Response(
            200, json={"vulnerabilities": [{"cveID": "CVE-2024-12345"}]}
        )
    )
    respx.get(EPSS_URL).mock(return_value=Response(200, json=MOCK_EPSS_RESPONSE))

    response = await async_client.post(
        "/api/v1/risk/score",
        json={
            "cve_id": "CVE-2024-12345",
            "asset_criticality": 9,
            "is_internet_facing": True,
            "framework": "risk-based",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cve_intelligence"]["cisa_kev"] is True


@respx.mock
async def test_score_vulnerability_not_found(async_client):
    respx.get(NVD_URL).mock(return_value=Response(200, json={"vulnerabilities": []}))
    respx.get(CISA_KEV_URL).mock(
        return_value=Response(200, json={"vulnerabilities": []})
    )
    respx.get(EPSS_URL).mock(return_value=Response(200, json={"data": []}))

    response = await async_client.post(
        "/api/v1/risk/score",
        json={"cve_id": "CVE-2099-99999", "asset_criticality": 5},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_score_vulnerability_unknown_framework(async_client):
    response = await async_client.post(
        "/api/v1/risk/score",
        json={
            "cve_id": "CVE-2024-12345",
            "asset_criticality": 5,
            "framework": "nonexistent",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNKNOWN_FRAMEWORK"


async def test_list_frameworks(async_client):
    response = await async_client.get("/api/v1/risk/frameworks")
    assert response.status_code == 200
    ids = {f["id"] for f in response.json()["frameworks"]}
    assert {"enhanced", "mitigation-contextual", "risk-based"} <= ids


@respx.mock
async def test_score_and_persist_for_authenticated_user(async_client):
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "riskuser@zeroday.dev",
            "full_name": "Risk User",
            "password": "correcthorse123",
        },
    )
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "riskuser@zeroday.dev", "password": "correcthorse123"},
    )
    token = login.json()["access_token"]

    respx.get(NVD_URL).mock(return_value=Response(200, json=MOCK_NVD_RESPONSE))
    respx.get(CISA_KEV_URL).mock(
        return_value=Response(200, json={"vulnerabilities": []})
    )
    respx.get(EPSS_URL).mock(return_value=Response(200, json=MOCK_EPSS_RESPONSE))

    score_resp = await async_client.post(
        "/api/v1/risk/score",
        json={"cve_id": "CVE-2024-12345", "asset_criticality": 7},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert score_resp.status_code == 200

    history = await async_client.get(
        "/api/v1/risk/history", headers={"Authorization": f"Bearer {token}"}
    )
    assert history.status_code == 200
    entries = history.json()
    assert len(entries) == 1
    assert entries[0]["cve_id"] == "CVE-2024-12345"


async def test_history_empty_when_anonymous(async_client):
    response = await async_client.get("/api/v1/risk/history")
    assert response.status_code == 200
    assert response.json() == []
