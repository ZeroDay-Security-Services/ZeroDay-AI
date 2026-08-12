from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class ComplianceScanRequest(BaseModel):
    config: Dict[str, Any]


class RuleOutcome(BaseModel):
    rule_id: str
    title: str
    severity: str
    passed: bool
    detail: str


class ComplianceResult(BaseModel):
    compliant: bool
    compliance_score: float
    rules_evaluated: int
    rules_passed: int
    violations: List[RuleOutcome]
    results: List[RuleOutcome]


class IncidentDeadlineRequest(BaseModel):
    detected_at: datetime
    incident_category: str | None = None


class IncidentDeadlineResponse(BaseModel):
    detected_at: str
    reporting_deadline: str
    reporting_window_hours: int
    is_overdue: bool
    seconds_remaining: float
    incident_category: str | None = None
