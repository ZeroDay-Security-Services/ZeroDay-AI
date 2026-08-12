async def _authed_headers(async_client, email="edr@zeroday.dev"):
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "EDR User", "password": "correcthorse123"},
    )
    login = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correcthorse123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_enroll_and_list_endpoint(async_client):
    headers = await _authed_headers(async_client)
    enroll = await async_client.post(
        "/api/v1/edr/enroll",
        json={
            "hostname": "workstation-01",
            "os_name": "Windows 11",
            "agent_version": "1.0.0",
        },
        headers=headers,
    )
    assert enroll.status_code == 201
    body = enroll.json()
    assert body["status"] == "online"
    assert body["hostname"] == "workstation-01"

    listing = await async_client.get("/api/v1/edr/endpoints", headers=headers)
    assert listing.status_code == 200
    summary = listing.json()
    assert summary["total"] == 1
    assert summary["online"] == 1


async def test_heartbeat_updates_findings(async_client):
    headers = await _authed_headers(async_client, email="edr2@zeroday.dev")
    enroll = await async_client.post(
        "/api/v1/edr/enroll",
        json={
            "hostname": "server-01",
            "os_name": "Ubuntu 24.04",
            "agent_version": "1.2.0",
        },
        headers=headers,
    )
    endpoint_id = enroll.json()["id"]

    hb = await async_client.post(
        f"/api/v1/edr/{endpoint_id}/heartbeat",
        json={"findings": {"open_ports": [22, 443], "av_status": "up-to-date"}},
        headers=headers,
    )
    assert hb.status_code == 200
    assert hb.json()["last_reported_findings"]["av_status"] == "up-to-date"


async def test_heartbeat_unknown_endpoint_404(async_client):
    headers = await _authed_headers(async_client, email="edr3@zeroday.dev")
    response = await async_client.post(
        "/api/v1/edr/does-not-exist/heartbeat", json={"findings": {}}, headers=headers
    )
    assert response.status_code == 404


async def test_endpoints_require_auth(async_client):
    response = await async_client.get("/api/v1/edr/endpoints")
    assert response.status_code == 401
