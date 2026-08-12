async def test_fully_compliant_config(async_client):
    config = {
        "public_read": False,
        "encryption_enabled": True,
        "versioning_enabled": True,
        "access_logging_enabled": True,
        "mfa_required": True,
        "iam_policy_actions": ["s3:GetObject", "s3:PutObject"],
        "access_key_age_days": 30,
        "open_security_group_ports": [],
    }
    response = await async_client.post(
        "/api/v1/compliance/cloud/scan", json={"config": config}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert body["compliance_score"] == 100.0
    assert body["violations"] == []


async def test_multiple_violations_detected(async_client):
    config = {
        "public_read": True,
        "encryption_enabled": False,
        "mfa_required": False,
        "iam_policy_actions": ["*"],
        "open_security_group_ports": [{"port": 22, "cidr": "0.0.0.0/0"}],
    }
    response = await async_client.post(
        "/api/v1/compliance/cloud/scan", json={"config": config}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert body["compliance_score"] < 100.0
    violated_ids = {v["rule_id"] for v in body["violations"]}
    assert {
        "STORAGE-001",
        "STORAGE-002",
        "IAM-001",
        "IAM-002",
        "NET-001",
    } <= violated_ids


async def test_empty_config_flags_all_defaults_as_violations(async_client):
    response = await async_client.post(
        "/api/v1/compliance/cloud/scan", json={"config": {}}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rules_evaluated"] == 8
    assert len(body["violations"]) > 0
