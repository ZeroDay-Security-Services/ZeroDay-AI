"""Digital Personal Data Protection Act, 2023 (India) -- compliance rules.

Covers the core, well-documented obligations on a Data Fiduciary: valid
consent/notice, Data Principal rights support, purpose/retention
limitation, breach notification, and the additional obligations that
apply to a Significant Data Fiduciary (SDF) -- DPO appointment, data
protection impact assessment, and independent audit. This is a
compliance-posture checker, not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class RuleResult:
    rule_id: str
    title: str
    severity: str
    passed: bool
    detail: str


def _rule_valid_consent_mechanism(config: Dict[str, Any]) -> RuleResult:
    valid = bool(config.get("consent_is_free_specific_informed_unambiguous", False))
    return RuleResult(
        rule_id="DPDP-001",
        title="Consent must be free, specific, informed, unconditional, and unambiguous with clear affirmative action",
        severity="critical",
        passed=valid,
        detail=(
            "Consent mechanism meets DPDP requirements"
            if valid
            else "Consent mechanism not confirmed as DPDP-compliant"
        ),
    )


def _rule_notice_provided(config: Dict[str, Any]) -> RuleResult:
    provided = bool(config.get("itemized_notice_provided", False))
    return RuleResult(
        rule_id="DPDP-002",
        title="An itemized notice describing personal data processed and its purpose must be given",
        severity="high",
        passed=provided,
        detail=(
            "Notice is provided at/before consent"
            if provided
            else "No itemized notice reported"
        ),
    )


def _rule_data_principal_rights(config: Dict[str, Any]) -> RuleResult:
    supported: List[str] = config.get("data_principal_rights_supported", [])
    required = {"access", "correction", "erasure", "grievance_redressal"}
    missing = required - set(supported)
    return RuleResult(
        rule_id="DPDP-003",
        title="Data Principal rights (access, correction, erasure, grievance redressal) must be supported",
        severity="critical",
        passed=not missing,
        detail=(
            f"Missing rights: {', '.join(sorted(missing))}"
            if missing
            else "All required rights are supported"
        ),
    )


def _rule_purpose_limitation(config: Dict[str, Any]) -> RuleResult:
    limited = bool(config.get("data_used_only_for_stated_purpose", False))
    return RuleResult(
        rule_id="DPDP-004",
        title="Personal data must be processed only for the purpose it was collected for",
        severity="high",
        passed=limited,
        detail=(
            "Purpose limitation is enforced"
            if limited
            else "Purpose limitation not confirmed"
        ),
    )


def _rule_retention_limitation(config: Dict[str, Any]) -> RuleResult:
    has_policy = bool(config.get("data_retention_policy_defined", False))
    return RuleResult(
        rule_id="DPDP-005",
        title="Personal data must be erased once its purpose is served, per a defined retention policy",
        severity="high",
        passed=has_policy,
        detail=(
            "Retention policy is defined"
            if has_policy
            else "No data retention/erasure policy reported"
        ),
    )


def _rule_breach_notification_process(config: Dict[str, Any]) -> RuleResult:
    has_process = bool(config.get("breach_notification_process_documented", False))
    return RuleResult(
        rule_id="DPDP-006",
        title="A documented process to notify the Data Protection Board and affected Data Principals of a breach must exist",
        severity="critical",
        passed=has_process,
        detail=(
            "Breach notification process is documented"
            if has_process
            else "No documented breach notification process"
        ),
    )


def _rule_reasonable_security_safeguards(config: Dict[str, Any]) -> RuleResult:
    has_safeguards = bool(config.get("reasonable_security_safeguards_in_place", False))
    return RuleResult(
        rule_id="DPDP-007",
        title="Reasonable security safeguards must be in place to prevent personal data breaches",
        severity="critical",
        passed=has_safeguards,
        detail=(
            "Security safeguards reported in place"
            if has_safeguards
            else "No security safeguards reported"
        ),
    )


def _rule_childrens_data_protection(config: Dict[str, Any]) -> RuleResult:
    processes_childrens_data = bool(config.get("processes_childrens_data", False))
    if not processes_childrens_data:
        return RuleResult(
            rule_id="DPDP-008",
            title="Verifiable parental consent required and no tracking/targeted ads for children's data",
            severity="critical",
            passed=True,
            detail="Not applicable -- does not process children's personal data",
        )
    compliant = bool(
        config.get("verifiable_parental_consent_obtained", False)
    ) and not bool(config.get("tracks_or_targets_ads_to_children", True))
    return RuleResult(
        rule_id="DPDP-008",
        title="Verifiable parental consent required and no tracking/targeted ads for children's data",
        severity="critical",
        passed=compliant,
        detail=(
            "Children's data handling meets DPDP requirements"
            if compliant
            else "Children's data handling does not meet DPDP requirements"
        ),
    )


def _rule_sdf_dpo_appointed(config: Dict[str, Any]) -> RuleResult:
    """Only applicable to organizations notified as a Significant Data Fiduciary."""
    is_sdf = bool(config.get("is_significant_data_fiduciary", False))
    if not is_sdf:
        return RuleResult(
            rule_id="DPDP-009",
            title="A India-based Data Protection Officer must be appointed (Significant Data Fiduciary)",
            severity="high",
            passed=True,
            detail="Not applicable -- not designated a Significant Data Fiduciary",
        )
    appointed = bool(config.get("dpo_appointed_india_based", False))
    return RuleResult(
        rule_id="DPDP-009",
        title="A India-based Data Protection Officer must be appointed (Significant Data Fiduciary)",
        severity="high",
        passed=appointed,
        detail="DPO appointed" if appointed else "No India-based DPO reported",
    )


def _rule_sdf_dpia_and_audit(config: Dict[str, Any]) -> RuleResult:
    is_sdf = bool(config.get("is_significant_data_fiduciary", False))
    if not is_sdf:
        return RuleResult(
            rule_id="DPDP-010",
            title="Periodic Data Protection Impact Assessment and independent audit required (Significant Data Fiduciary)",
            severity="high",
            passed=True,
            detail="Not applicable -- not designated a Significant Data Fiduciary",
        )
    compliant = bool(config.get("dpia_conducted", False)) and bool(
        config.get("independent_audit_conducted", False)
    )
    return RuleResult(
        rule_id="DPDP-010",
        title="Periodic Data Protection Impact Assessment and independent audit required (Significant Data Fiduciary)",
        severity="high",
        passed=compliant,
        detail=(
            "DPIA and independent audit reported"
            if compliant
            else "DPIA and/or independent audit not reported"
        ),
    )


_RULES: List[Callable[[Dict[str, Any]], RuleResult]] = [
    _rule_valid_consent_mechanism,
    _rule_notice_provided,
    _rule_data_principal_rights,
    _rule_purpose_limitation,
    _rule_retention_limitation,
    _rule_breach_notification_process,
    _rule_reasonable_security_safeguards,
    _rule_childrens_data_protection,
    _rule_sdf_dpo_appointed,
    _rule_sdf_dpia_and_audit,
]

_SEVERITY_WEIGHT = {"critical": 30, "high": 15, "medium": 8, "low": 3}


def evaluate_dpdp_compliance(config: Dict[str, Any]) -> Dict[str, Any]:
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
