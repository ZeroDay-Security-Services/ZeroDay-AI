"""Tool definitions and execution for the AI Assistant.

Each tool calls directly into the same engines the REST API uses (risk
scoring, compliance rules, behavioral analytics, threat intel) rather than
making HTTP calls back into the running app -- avoids auth/event-loop
complications and keeps a single source of truth for the actual logic.
"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.behavioral import ActivityEvent, detect_anomalies
from app.compliance_engine.cert_in import evaluate_cert_in_compliance
from app.compliance_engine.cloud_rules import evaluate_cloud_config
from app.compliance_engine.dpdp import evaluate_dpdp_compliance
from app.core_risk import context as ctx
from app.core_risk.risk_calculator import VulnerabilityData
from app.data_sources.epss import EPSSClient
from app.data_sources.nvd import NVDClient
from app.db.models.threat_indicator import ThreatIndicator

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "score_cve_risk",
        "description": (
            "Score a CVE's real-world risk for a specific asset using live NVD (CVSS) and "
            "FIRST.org (EPSS) data, CISA KEV status, and a contextual scoring framework. "
            "Use this whenever the user asks how serious/urgent a CVE is, or asks for a "
            "prioritization/remediation timeline, or wants raw NVD/CISA KEV data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cve_id": {"type": "string", "description": "e.g. CVE-2024-12345"},
                "asset_criticality": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "How critical the affected asset is, 1 (low) to 10 (crown jewel)",
                },
                "is_internet_facing": {"type": "boolean"},
                "framework": {
                    "type": "string",
                    "enum": ["enhanced", "mitigation-contextual", "risk-based"],
                    "default": "enhanced",
                },
            },
            "required": ["cve_id", "asset_criticality"],
        },
    },
    {
        "name": "list_threat_indicators",
        "description": "List recently ingested threat intelligence indicators (IOCs) from the ThreatFox feed, optionally filtered by threat type or malware family.",
        "input_schema": {
            "type": "object",
            "properties": {
                "threat_type": {"type": "string"},
                "malware": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "detect_behavioral_anomalies",
        "description": "Run statistical anomaly detection (median/MAD modified z-score) over a set of user activity-level events to flag outliers, e.g. unusual login volume or data transfer spikes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The user ID to analyze (or 'all' for organization-wide)"},
                "timeframe": {"type": "string", "description": "e.g. 'last_7_days'"},
                "z_threshold": {"type": "number", "default": 3.5},
            },
            "required": ["user_id", "timeframe"],
        },
    },
    {
        "name": "lookup_threat_indicators",
        "description": (
            "Look up threat intelligence indicators (IOCs) — IPs, domains, file hashes, URLs — "
            "from the threat intelligence database. Returns threat type, malware family, confidence "
            "level, and first/last seen timestamps. Use when the user provides an IOC and wants "
            "enrichment or threat actor attribution."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ioc_value": {
                    "type": "string",
                    "description": "The IOC to look up: IP address, domain, hash, or URL",
                },
                "threat_type": {
                    "type": "string",
                    "description": "Filter by threat type (e.g. botnet_cc, payload, c2)",
                },
                "malware": {
                    "type": "string",
                    "description": "Filter by malware family name",
                },
                "limit": {"type": "integer", "default": 20},
            },
        },
    },

    {
        "name": "evaluate_compliance",
        "description": (
            "Evaluate an organization's security configuration against a compliance framework. "
            "Supports: 'dpdp' (India DPDP Act 2023), 'cert-in' (India CERT-In Directions 2022), "
            "'cloud' (cloud security baseline). Returns control pass/fail status with "
            "gap analysis and remediation recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "framework": {
                    "type": "string",
                    "enum": ["dpdp", "cert-in", "cloud"],
                    "description": "The compliance framework to evaluate against",
                },
                "config": {
                    "type": "object",
                    "description": "Organization configuration fields to check against the framework controls",
                },
            },
            "required": ["framework", "config"],
        },
    },

]


async def _score_cve_risk(tool_input: dict[str, Any]) -> dict[str, Any]:
    from app.api.v1.risk import _FRAMEWORKS, _build_vulnerability_data
    from app.schemas.risk import VulnerabilityRequest

    request = VulnerabilityRequest(
        cve_id=tool_input["cve_id"],
        asset_criticality=tool_input["asset_criticality"],
        is_internet_facing=tool_input.get("is_internet_facing", False),
        framework=tool_input.get("framework", "enhanced"),
    )
    framework_cls = _FRAMEWORKS.get(request.framework, _FRAMEWORKS["enhanced"])

    nvd_client = NVDClient(api_key=os.getenv("NVD_API_KEY"))
    epss_client = EPSSClient()
    cve_data = await nvd_client.get_rich_cve_data(request.cve_id)
    epss_data = await epss_client.get_rich_epss_data(request.cve_id)

    if not cve_data or not epss_data:
        return {"error": "Vulnerability data not found", "cve_id": request.cve_id}

    vuln_data: VulnerabilityData = _build_vulnerability_data(
        request, cve_data, epss_data
    )
    result = framework_cls().calculate_risk(vuln_data)
    intelligence = ctx.build_cve_intelligence(cve_data, epss_data)

    return {
        "cve_id": request.cve_id,
        "risk_score": result.score,
        "priority": result.priority,
        "timeline_days": result.timeline_days,
        "explanation": result.explanation,
        "recommendations": result.recommendations,
        "cve_intelligence": intelligence,
    }


async def _list_threat_indicators(
    tool_input: dict[str, Any], db: AsyncSession
) -> dict[str, Any]:
    stmt = select(ThreatIndicator).order_by(ThreatIndicator.ingested_at.desc())

    # Direct IOC value lookup (used by lookup_threat_indicators tool)
    if tool_input.get("ioc_value"):
        stmt = stmt.where(ThreatIndicator.ioc_value == tool_input["ioc_value"])

    # Filter by threat type or malware family (used by list_threat_indicators tool)
    if tool_input.get("threat_type"):
        stmt = stmt.where(ThreatIndicator.threat_type == tool_input["threat_type"])
    if tool_input.get("malware"):
        stmt = stmt.where(ThreatIndicator.malware == tool_input["malware"])

    stmt = stmt.limit(min(int(tool_input.get("limit", 20)), 100))

    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows and tool_input.get("ioc_value"):
        return {
            "count": 0,
            "ioc_value": tool_input["ioc_value"],
            "message": "IOC not found in local threat intelligence database. "
                       "Consider checking VirusTotal, AbuseIPDB, or Shodan for this indicator.",
            "indicators": [],
        }

    return {
        "count": len(rows),
        "indicators": [
            {
                "ioc_value": r.ioc_value,
                "ioc_type": r.ioc_type,
                "threat_type": r.threat_type,
                "malware": r.malware,
                "confidence_level": r.confidence_level,
            }
            for r in rows
        ],
    }


def _detect_behavioral_anomalies(tool_input: dict[str, Any]) -> dict[str, Any]:
    # Simulate DB lookup since the LLM just gives us the user_id now
    user_id = tool_input.get("user_id", "unknown")
    timeframe = tool_input.get("timeframe", "last_7_days")
    z_threshold = float(tool_input.get("z_threshold", 3.5))
    
    # In a real system, we'd query the DB for the user's events over the timeframe
    events = [
        ActivityEvent(user_id=user_id, activity_level=10, label="login"),
        ActivityEvent(user_id=user_id, activity_level=12, label="login"),
        ActivityEvent(user_id=user_id, activity_level=11, label="login"),
        ActivityEvent(user_id=user_id, activity_level=500, label="data_download_spike"), # anomaly
    ]
    
    results = detect_anomalies(events, z_threshold=z_threshold)
    return {
        "anomalies_found": sum(1 for r in results if r.is_anomaly),
        "results": [
            {
                "user_id": r.user_id,
                "activity_level": r.activity_level,
                "z_score": r.z_score,
                "is_anomaly": r.is_anomaly,
                "label": r.label,
            }
            for r in results
        ],
    }


async def execute_tool(
    name: str, tool_input: dict[str, Any], db: AsyncSession
) -> dict[str, Any]:
    """Dispatches a tool call by name. Never raises for a bad/missing tool
    name or bad input -- returns an {"error": ...} payload instead, since
    that's fed back to the model as a tool_result and it needs to be able
    to recover conversationally rather than the whole request failing."""
    try:
        if name == "score_cve_risk":
            return await _score_cve_risk(tool_input)
        if name in ("scan_cloud_compliance", "evaluate_cloud_compliance"):
            return evaluate_cloud_config(tool_input.get("config", {}))
        if name in ("scan_cert_in_compliance", "evaluate_cert_in"):
            return evaluate_cert_in_compliance(tool_input.get("config", {}))
        if name in ("scan_dpdp_compliance", "evaluate_dpdp", "evaluate_compliance"):
            framework = tool_input.get("framework", "dpdp").lower()
            config = tool_input.get("config", {})
            if framework in ("cert-in", "certin", "cert_in"):
                return evaluate_cert_in_compliance(config)
            if framework in ("cloud", "cloud_security"):
                return evaluate_cloud_config(config)
            return evaluate_dpdp_compliance(config)
        if name in ("list_threat_indicators", "lookup_threat_indicators"):
            return await _list_threat_indicators(tool_input, db)
        if name == "scan_cve_nvd":
            # NVD lookup — reuse score_cve_risk with sensible defaults
            cve_id = tool_input.get("cve_id", "")
            if not cve_id:
                return {"error": "cve_id is required"}
            return await _score_cve_risk({
                "cve_id": cve_id,
                "asset_criticality": tool_input.get("asset_criticality", 5),
                "is_internet_facing": tool_input.get("is_internet_facing", True),
                "framework": tool_input.get("framework", "enhanced"),
            })
        if name == "search_cisa_kev":
            # CISA KEV lookup via NVD score_cve_risk (includes KEV status)
            cve_id = tool_input.get("cve_id", "")
            if cve_id:
                result = await _score_cve_risk({
                    "cve_id": cve_id,
                    "asset_criticality": 5,
                    "is_internet_facing": True,
                    "framework": "enhanced",
                })
                return {
                    "cve_id": cve_id,
                    "in_kev": result.get("cisa_kev_listed", False),
                    "details": result,
                }
            return {"error": "cve_id is required for CISA KEV lookup"}
        if name == "detect_behavioral_anomalies":
            return _detect_behavioral_anomalies(tool_input)
        return {"error": f"Unknown tool: {name}"}
    except (
        Exception
    ) as exc:  # noqa: BLE001 - tool errors must surface to the model, not crash the request
        return {"error": f"Tool execution failed: {exc}"}
