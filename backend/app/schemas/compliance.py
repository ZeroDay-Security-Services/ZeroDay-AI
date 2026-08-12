from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class CloudConfigScanRequest(BaseModel):
    config: Dict[str, Any]


class RuleOutcome(BaseModel):
    rule_id: str
    title: str
    severity: str
    passed: bool
    detail: str


class CloudComplianceResult(BaseModel):
    compliant: bool
    compliance_score: float
    rules_evaluated: int
    rules_passed: int
    violations: List[RuleOutcome]
    results: List[RuleOutcome]
