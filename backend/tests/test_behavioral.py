async def test_detects_statistical_outlier(async_client):
    events = [
        {"user_id": "u1", "activity_level": lvl} for lvl in [10, 11, 9, 10, 12, 200]
    ]
    response = await async_client.post(
        "/api/v1/analytics/behavioral/anomalies", json={"events": events}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 6
    assert body["anomalies_found"] == 1
    anomaly = next(r for r in body["results"] if r["is_anomaly"])
    assert anomaly["activity_level"] == 200


async def test_uniform_activity_has_no_anomalies(async_client):
    events = [{"user_id": "u1", "activity_level": 50} for _ in range(5)]
    response = await async_client.post(
        "/api/v1/analytics/behavioral/anomalies", json={"events": events}
    )
    assert response.status_code == 200
    assert response.json()["anomalies_found"] == 0


async def test_per_user_isolation(async_client):
    # u1 is a consistently high-activity user (not anomalous for themself);
    # u2 is consistently low. Neither should trigger despite differing baselines.
    events = [{"user_id": "u1", "activity_level": lvl} for lvl in [90, 92, 88, 91]] + [
        {"user_id": "u2", "activity_level": lvl} for lvl in [5, 6, 4, 5]
    ]
    response = await async_client.post(
        "/api/v1/analytics/behavioral/anomalies", json={"events": events}
    )
    assert response.status_code == 200
    assert response.json()["anomalies_found"] == 0


async def test_custom_threshold(async_client):
    events = [{"user_id": "u1", "activity_level": lvl} for lvl in [10, 10, 10, 15]]
    response = await async_client.post(
        "/api/v1/analytics/behavioral/anomalies",
        json={"events": events, "z_threshold": 0.5},
    )
    assert response.status_code == 200
    assert response.json()["anomalies_found"] >= 1
