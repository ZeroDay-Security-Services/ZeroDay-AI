from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EndpointEnrollRequest(BaseModel):
    hostname: str = Field(min_length=1, max_length=255)
    ip_address: Optional[str] = None
    os_name: str = Field(min_length=1, max_length=64)
    agent_version: str = Field(min_length=1, max_length=32)


class EndpointHeartbeatRequest(BaseModel):
    findings: Dict[str, Any] = Field(default_factory=dict)


class EndpointRead(BaseModel):
    id: str
    hostname: str
    ip_address: Optional[str]
    os_name: str
    agent_version: str
    enrolled_at: str
    last_heartbeat_at: str
    seconds_since_heartbeat: float
    status: str
    last_reported_findings: Dict[str, Any]


class FleetSummary(BaseModel):
    total: int
    online: int
    stale: int
    offline: int
    endpoints: List[EndpointRead]
