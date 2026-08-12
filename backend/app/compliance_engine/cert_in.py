"""CERT-In Cyber Security Directions, 2022 -- compliance rules and incident
reporting deadline calculator.

Reference: CERT-In "Directions under sub-section (6) of Section 70B of the
Information Technology Act, 2000", issued 28 April 2022. Covers the core,
well-documented obligations: 6-hour incident reporting, 180-day log
retention within Indian jurisdiction, NTP time synchronization, and
designation of a Point of Contact. This is a compliance-posture checker,
not legal advice -- organizations should confirm current requirements
with CERT-In / legal counsel.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List

REPORTING_WINDOW_HOURS = 6
MIN_LOG_RETENTION_DAYS = 180

# The 20 mandatory-reporting incident categories under Annexure I of the
# CERT-In directions (publicly published list).
MANDATORY_INCIDENT_CATEGORIES: List[str] = [
    "Targeted scanning/probing of critical networks/systems",
    "Compromise of critical systems/information",
    "Unauthorised access of IT systems/data",
    "Website defacement or intrusion into a website",
    "Malicious code attacks (virus/worm/trojan/bots/spyware/ransomware/cryptominers)",
    "Attacks on servers (database, mail, DNS) and network devices (routers)",
    "Identity theft, spoofing, and phishing attacks",
    "Denial of Service (DoS) and Distributed Denial of Service (DDoS) attacks",
    "Attacks on critical infrastructure, SCADA/OT systems, ICS, and wireless networks",
    "Attacks on applications such as e-governance and e-commerce",
    "Data breaches",
    "Data leaks",
    "Attacks on IoT devices and associated systems/networks/servers",
    "Attacks or incidents affecting digital payment systems",
    "Attacks via malicious mobile apps",
    "Fake mobile apps impersonating a legitimate organization",
    "Unauthorised access to social media accounts",
    "Attacks or suspicious activities affecting cloud computing systems",
    "Attacks or suspicious activities affecting AI systems",
    "Attacks on systems related to big data, blockchain, virtual assets, and robotics",
]


@dataclass
class RuleResult:
    rule_id: str
    title: str
    severity: str
    passed: bool
    detail: str


def _rule_log_retention(config: Dict[str, Any]) -> RuleResult:
    days = int(config.get("log_retention_days", 0) or 0)
    passed = days >= MIN_LOG_RETENTION_DAYS
    return RuleResult(
        rule_id="CERT-IN-001",
        title=f"ICT system logs must be retained for at least {MIN_LOG_RETENTION_DAYS} days",
        severity="critical",
        passed=passed,
        detail=(
            f"Configured retention is {days} days"
            if days
            else "No log retention period reported"
        ),
    )


def _rule_logs_within_india(config: Dict[str, Any]) -> RuleResult:
    within_india = bool(config.get("logs_stored_in_india", False))
    return RuleResult(
        rule_id="CERT-IN-002",
        title="ICT system logs must be stored within Indian jurisdiction",
        severity="critical",
        passed=within_india,
        detail=(
            "Logs are stored within India"
            if within_india
            else "Logs are not confirmed to be stored within India"
        ),
    )


def _rule_ntp_sync(config: Dict[str, Any]) -> RuleResult:
    ntp_server = str(config.get("ntp_server", "")).strip()
    approved_markers = ("nic.in", "npl.gov.in", "nplindia")
    synced = bool(ntp_server) and any(
        marker in ntp_server.lower() for marker in approved_markers
    )
    return RuleResult(
        rule_id="CERT-IN-003",
        title="System clocks must sync to an NIC/NPL-traceable NTP server",
        severity="high",
        passed=synced,
        detail=(
            (
                f"NTP server '{ntp_server}' does not appear to be NIC/NPL-traceable"
                if ntp_server
                else "No NTP server configured"
            )
            if not synced
            else f"Synced to '{ntp_server}'"
        ),
    )


def _rule_poc_designated(config: Dict[str, Any]) -> RuleResult:
    poc = config.get("point_of_contact")
    designated = bool(poc and str(poc).strip())
    return RuleResult(
        rule_id="CERT-IN-004",
        title="A Point of Contact for CERT-In coordination must be designated",
        severity="high",
        passed=designated,
        detail=(
            "Point of Contact is designated"
            if designated
            else "No Point of Contact reported"
        ),
    )


def _rule_incident_reporting_process(config: Dict[str, Any]) -> RuleResult:
    has_process = bool(config.get("incident_reporting_process_documented", False))
    return RuleResult(
        rule_id="CERT-IN-005",
        title="A documented process must exist to report incidents to CERT-In within 6 hours",
        severity="critical",
        passed=has_process,
        detail=(
            "Incident reporting process is documented"
            if has_process
            else "No documented 6-hour incident reporting process reported"
        ),
    )


def _rule_subscriber_records(config: Dict[str, Any]) -> RuleResult:
    """Only applicable to data centers / VPS / cloud / VPN providers."""
    is_applicable = bool(config.get("is_data_center_vps_cloud_or_vpn_provider", False))
    if not is_applicable:
        return RuleResult(
            rule_id="CERT-IN-006",
            title="Subscriber/customer records must be retained for 5 years (data center/VPS/cloud/VPN providers)",
            severity="high",
            passed=True,
            detail="Not applicable -- not reported as a data center/VPS/cloud/VPN provider",
        )
    retains = bool(config.get("subscriber_records_retained_5_years", False))
    return RuleResult(
        rule_id="CERT-IN-006",
        title="Subscriber/customer records must be retained for 5 years (data center/VPS/cloud/VPN providers)",
        severity="high",
        passed=retains,
        detail=(
            "5-year subscriber record retention confirmed"
            if retains
            else "5-year subscriber record retention not confirmed"
        ),
    )


_RULES: List[Callable[[Dict[str, Any]], RuleResult]] = [
    _rule_log_retention,
    _rule_logs_within_india,
    _rule_ntp_sync,
    _rule_poc_designated,
    _rule_incident_reporting_process,
    _rule_subscriber_records,
]

_SEVERITY_WEIGHT = {"critical": 30, "high": 15, "medium": 8, "low": 3}


def evaluate_cert_in_compliance(config: Dict[str, Any]) -> Dict[str, Any]:
    results = [rule(config) for rule in _RULES]
    violations = [r for r in results if not r.passed]

    max_possible = sum(_SEVERITY_WEIGHT[r.severity] for r in results)
    lost = sum(_SEVERITY_WEIGHT[r.severity] for r in violations)
    compliance_score = (
        round(max(0.0, (max_possible - lost) / max_possible) * 100, 1)
        if max_possible
        else 100.0
    )

    return {
        "compliant": len(violations) == 0,
        "compliance_score": compliance_score,
        "rules_evaluated": len(results),
        "rules_passed": len(results) - len(violations),
        "violations": [
            {
                "rule_id": v.rule_id,
                "title": v.title,
                "severity": v.severity,
                "passed": v.passed,
                "detail": v.detail,
            }
            for v in violations
        ],
        "results": [
            {
                "rule_id": r.rule_id,
                "title": r.title,
                "severity": r.severity,
                "passed": r.passed,
                "detail": r.detail,
            }
            for r in results
        ],
    }


def calculate_reporting_deadline(detected_at: datetime) -> Dict[str, Any]:
    """Given when an incident was noticed, compute the mandatory CERT-In
    reporting deadline (detected_at + 6 hours) and whether it has passed."""
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=timezone.utc)

    deadline = detected_at + timedelta(hours=REPORTING_WINDOW_HOURS)
    now = datetime.now(timezone.utc)
    remaining_seconds = (deadline - now).total_seconds()

    return {
        "detected_at": detected_at.isoformat(),
        "reporting_deadline": deadline.isoformat(),
        "reporting_window_hours": REPORTING_WINDOW_HOURS,
        "is_overdue": remaining_seconds < 0,
        "seconds_remaining": max(0.0, remaining_seconds),
    }
