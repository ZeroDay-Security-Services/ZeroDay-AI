import respx
from httpx import Response

THREATFOX_URL = "https://threatfox-api.abuse.ch/api/v1/"

MOCK_THREATFOX_RESPONSE = {
    "query_status": "ok",
    "data": [
        {
            "ioc": "185.220.101.5",
            "ioc_type": "ip:port",
            "threat_type": "botnet_cc",
            "malware_printable": "AsyncRAT",
            "confidence_level": 90,
            "first_seen": "2026-08-01 10:00:00 UTC",
            "last_seen": "2026-08-03 12:00:00 UTC",
            "tags": ["asyncrat", "botnet"],
            "reference": "https://threatfox.abuse.ch/ioc/1234/",
        },
        {
            "ioc": "malicious-domain.example",
            "ioc_type": "domain",
            "threat_type": "payload_delivery",
            "malware_printable": "Emotet",
            "confidence_level": 75,
            "first_seen": "2026-08-02 08:00:00 UTC",
            "last_seen": "2026-08-03 09:00:00 UTC",
            "tags": ["emotet"],
            "reference": "https://threatfox.abuse.ch/ioc/5678/",
        },
    ],
}


@respx.mock
async def test_sync_stores_new_indicators(async_client):
    respx.post(THREATFOX_URL).mock(
        return_value=Response(200, json=MOCK_THREATFOX_RESPONSE)
    )

    response = await async_client.post("/api/v1/threat-intel/sync")
    assert response.status_code == 200
    body = response.json()
    assert body["fetched"] == 2
    assert body["stored_new"] == 2
    assert body["updated"] == 0

    listing = await async_client.get("/api/v1/threat-intel/iocs")
    assert listing.status_code == 200
    iocs = listing.json()
    assert len(iocs) == 2
    assert {i["ioc_value"] for i in iocs} == {
        "185.220.101.5",
        "malicious-domain.example",
    }


@respx.mock
async def test_sync_is_idempotent_and_updates_existing(async_client):
    respx.post(THREATFOX_URL).mock(
        return_value=Response(200, json=MOCK_THREATFOX_RESPONSE)
    )

    first = await async_client.post("/api/v1/threat-intel/sync")
    assert first.json()["stored_new"] == 2

    second = await async_client.post("/api/v1/threat-intel/sync")
    body = second.json()
    assert body["stored_new"] == 0
    assert body["updated"] == 2

    listing = await async_client.get("/api/v1/threat-intel/iocs")
    assert len(listing.json()) == 2  # no duplicates


@respx.mock
async def test_filter_by_malware(async_client):
    respx.post(THREATFOX_URL).mock(
        return_value=Response(200, json=MOCK_THREATFOX_RESPONSE)
    )
    await async_client.post("/api/v1/threat-intel/sync")

    response = await async_client.get(
        "/api/v1/threat-intel/iocs", params={"malware": "Emotet"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["malware"] == "Emotet"


@respx.mock
async def test_sync_handles_feed_failure_gracefully(async_client):
    respx.post(THREATFOX_URL).mock(return_value=Response(500))

    response = await async_client.post("/api/v1/threat-intel/sync")
    assert response.status_code == 200
    body = response.json()
    assert body["fetched"] == 0
    assert body["stored_new"] == 0
