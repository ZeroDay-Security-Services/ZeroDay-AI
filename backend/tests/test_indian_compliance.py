from datetime import datetime, timedelta, timezone


async def test_cert_in_fully_compliant_config(async_client):
    config = {
        "log_retention_days": 200,
        "logs_stored_in_india": True,
        "ntp_server": "samay1.nic.in",
        "point_of_contact": "soc@example.in",
        "incident_reporting_process_documented": True,
        "is_data_center_vps_cloud_or_vpn_provider": False,
    }
    response = await async_client.post(
        "/api/v1/compliance/india/cert-in/scan", json={"config": config}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert body["compliance_score"] == 100.0


async def test_cert_in_insufficient_log_retention(async_client):
    config = {
        "log_retention_days": 30,
        "logs_stored_in_india": True,
        "ntp_server": "samay1.nic.in",
        "point_of_contact": "soc@example.in",
        "incident_reporting_process_documented": True,
    }
    response = await async_client.post(
        "/api/v1/compliance/india/cert-in/scan", json={"config": config}
    )
    body = response.json()
    assert body["compliant"] is False
    violated_ids = {v["rule_id"] for v in body["violations"]}
    assert "CERT-IN-001" in violated_ids


async def test_cert_in_vpn_provider_must_retain_subscriber_records(async_client):
    config = {
        "log_retention_days": 200,
        "logs_stored_in_india": True,
        "ntp_server": "samay1.nic.in",
        "point_of_contact": "soc@example.in",
        "incident_reporting_process_documented": True,
        "is_data_center_vps_cloud_or_vpn_provider": True,
        "subscriber_records_retained_5_years": False,
    }
    response = await async_client.post(
        "/api/v1/compliance/india/cert-in/scan", json={"config": config}
    )
    body = response.json()
    assert body["compliant"] is False
    violated_ids = {v["rule_id"] for v in body["violations"]}
    assert "CERT-IN-006" in violated_ids


async def test_cert_in_incident_categories_lists_twenty(async_client):
    response = await async_client.get(
        "/api/v1/compliance/india/cert-in/incident-categories"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reporting_window_hours"] == 6
    assert len(body["categories"]) == 20


async def test_cert_in_incident_deadline_is_six_hours_out(async_client):
    detected = datetime.now(timezone.utc) - timedelta(hours=1)
    response = await async_client.post(
        "/api/v1/compliance/india/cert-in/incident-deadline",
        json={
            "detected_at": detected.isoformat(),
            "incident_category": "Data breaches",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_overdue"] is False
    assert body["seconds_remaining"] > 0
    assert body["reporting_window_hours"] == 6


async def test_cert_in_incident_deadline_overdue(async_client):
    detected = datetime.now(timezone.utc) - timedelta(hours=10)
    response = await async_client.post(
        "/api/v1/compliance/india/cert-in/incident-deadline",
        json={"detected_at": detected.isoformat()},
    )
    body = response.json()
    assert body["is_overdue"] is True
    assert body["seconds_remaining"] == 0.0


async def test_dpdp_fully_compliant_non_sdf(async_client):
    config = {
        "consent_is_free_specific_informed_unambiguous": True,
        "itemized_notice_provided": True,
        "data_principal_rights_supported": [
            "access",
            "correction",
            "erasure",
            "grievance_redressal",
        ],
        "data_used_only_for_stated_purpose": True,
        "data_retention_policy_defined": True,
        "breach_notification_process_documented": True,
        "reasonable_security_safeguards_in_place": True,
        "processes_childrens_data": False,
        "is_significant_data_fiduciary": False,
    }
    response = await async_client.post(
        "/api/v1/compliance/india/dpdp/scan", json={"config": config}
    )
    body = response.json()
    assert body["compliant"] is True
    assert body["compliance_score"] == 100.0


async def test_dpdp_missing_data_principal_rights(async_client):
    config = {
        "consent_is_free_specific_informed_unambiguous": True,
        "itemized_notice_provided": True,
        "data_principal_rights_supported": ["access"],
        "data_used_only_for_stated_purpose": True,
        "data_retention_policy_defined": True,
        "breach_notification_process_documented": True,
        "reasonable_security_safeguards_in_place": True,
    }
    response = await async_client.post(
        "/api/v1/compliance/india/dpdp/scan", json={"config": config}
    )
    body = response.json()
    assert body["compliant"] is False
    violation = next(v for v in body["violations"] if v["rule_id"] == "DPDP-003")
    assert "correction" in violation["detail"]
    assert "erasure" in violation["detail"]


async def test_dpdp_significant_data_fiduciary_requires_dpo(async_client):
    config = {
        "consent_is_free_specific_informed_unambiguous": True,
        "itemized_notice_provided": True,
        "data_principal_rights_supported": [
            "access",
            "correction",
            "erasure",
            "grievance_redressal",
        ],
        "data_used_only_for_stated_purpose": True,
        "data_retention_policy_defined": True,
        "breach_notification_process_documented": True,
        "reasonable_security_safeguards_in_place": True,
        "is_significant_data_fiduciary": True,
        "dpo_appointed_india_based": False,
        "dpia_conducted": True,
        "independent_audit_conducted": True,
    }
    response = await async_client.post(
        "/api/v1/compliance/india/dpdp/scan", json={"config": config}
    )
    body = response.json()
    assert body["compliant"] is False
    violated_ids = {v["rule_id"] for v in body["violations"]}
    assert "DPDP-009" in violated_ids


async def test_dpdp_childrens_data_requires_parental_consent_no_tracking(async_client):
    config = {
        "consent_is_free_specific_informed_unambiguous": True,
        "itemized_notice_provided": True,
        "data_principal_rights_supported": [
            "access",
            "correction",
            "erasure",
            "grievance_redressal",
        ],
        "data_used_only_for_stated_purpose": True,
        "data_retention_policy_defined": True,
        "breach_notification_process_documented": True,
        "reasonable_security_safeguards_in_place": True,
        "processes_childrens_data": True,
        "verifiable_parental_consent_obtained": True,
        "tracks_or_targets_ads_to_children": True,
    }
    response = await async_client.post(
        "/api/v1/compliance/india/dpdp/scan", json={"config": config}
    )
    body = response.json()
    assert body["compliant"] is False
    violated_ids = {v["rule_id"] for v in body["violations"]}
    assert "DPDP-008" in violated_ids
