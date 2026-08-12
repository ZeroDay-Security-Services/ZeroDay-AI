"""Real, deterministic cloud configuration compliance rules engine.

Replaces the uploaded cloud_compliance.py, which unconditionally returned
{"compliant": True, "violations": []} for any input. Every rule here
actually inspects the submitted configuration and can fail it.
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


def _rule_no_public_read(config: Dict[str, Any]) -> RuleResult:
    public = (
        bool(config.get("public_read", False)) or config.get("acl") == "public-read"
    )
    return RuleResult(
        rule_id="STORAGE-001",
        title="Storage bucket must not allow public read access",
        severity="critical",
        passed=not public,
        detail=(
            "Bucket ACL grants public read access"
            if public
            else "No public read access detected"
        ),
    )


def _rule_encryption_at_rest(config: Dict[str, Any]) -> RuleResult:
    encrypted = bool(config.get("encryption_enabled", False))
    return RuleResult(
        rule_id="STORAGE-002",
        title="Encryption at rest must be enabled",
        severity="high",
        passed=encrypted,
        detail=(
            "Encryption at rest is enabled"
            if encrypted
            else "Encryption at rest is not enabled"
        ),
    )


def _rule_versioning_enabled(config: Dict[str, Any]) -> RuleResult:
    versioning = bool(config.get("versioning_enabled", False))
    return RuleResult(
        rule_id="STORAGE-003",
        title="Object versioning should be enabled",
        severity="medium",
        passed=versioning,
        detail="Versioning is enabled" if versioning else "Versioning is disabled",
    )


def _rule_access_logging(config: Dict[str, Any]) -> RuleResult:
    logging_enabled = bool(config.get("access_logging_enabled", False))
    return RuleResult(
        rule_id="STORAGE-004",
        title="Access logging should be enabled",
        severity="medium",
        passed=logging_enabled,
        detail=(
            "Access logging is enabled"
            if logging_enabled
            else "Access logging is disabled"
        ),
    )


def _rule_mfa_required(config: Dict[str, Any]) -> RuleResult:
    mfa = bool(config.get("mfa_required", False))
    return RuleResult(
        rule_id="IAM-001",
        title="MFA must be required for privileged access",
        severity="critical",
        passed=mfa,
        detail=(
            "MFA is enforced" if mfa else "MFA is not enforced for privileged access"
        ),
    )


def _rule_no_wildcard_iam_policy(config: Dict[str, Any]) -> RuleResult:
    policies: List[str] = config.get("iam_policy_actions", [])
    has_wildcard = any(action.strip() == "*" for action in policies)
    return RuleResult(
        rule_id="IAM-002",
        title="IAM policies must not grant wildcard (*) actions",
        severity="critical",
        passed=not has_wildcard,
        detail=(
            "A wildcard (*) action was found in an IAM policy"
            if has_wildcard
            else "No wildcard actions found"
        ),
    )


def _rule_key_rotation(config: Dict[str, Any]) -> RuleResult:
    max_days = int(config.get("access_key_age_days", 0) or 0)
    rotated = 0 < max_days <= 90
    return RuleResult(
        rule_id="IAM-003",
        title="Access keys must be rotated at least every 90 days",
        severity="high",
        passed=rotated,
        detail=(
            f"Oldest access key is {max_days} days old"
            if max_days
            else "No access key age reported"
        ),
    )


def _rule_network_restricted(config: Dict[str, Any]) -> RuleResult:
    open_ports = config.get("open_security_group_ports", [])
    risky_open_to_all = any(
        p.get("port") in (22, 3389) and p.get("cidr") == "0.0.0.0/0" for p in open_ports
    )
    return RuleResult(
        rule_id="NET-001",
        title="Management ports (22/3389) must not be open to 0.0.0.0/0",
        severity="critical",
        passed=not risky_open_to_all,
        detail=(
            "SSH/RDP is open to the entire internet"
            if risky_open_to_all
            else "No unrestricted management port exposure detected"
        ),
    )


_RULES: List[Callable[[Dict[str, Any]], RuleResult]] = [
    _rule_no_public_read,
    _rule_encryption_at_rest,
    _rule_versioning_enabled,
    _rule_access_logging,
    _rule_mfa_required,
    _rule_no_wildcard_iam_policy,
    _rule_key_rotation,
    _rule_network_restricted,
]

_SEVERITY_WEIGHT = {"critical": 30, "high": 15, "medium": 8, "low": 3}


def evaluate_cloud_config(config: Dict[str, Any]) -> Dict[str, Any]:
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
