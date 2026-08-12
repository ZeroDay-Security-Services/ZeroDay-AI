from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ThreatIndicatorRead(BaseModel):
    ioc_value: str
    ioc_type: str
    threat_type: str
    malware: str | None
    confidence_level: int
    tags: List[str]
    source_reference: str
    first_seen: str | None
    last_seen: str | None


class ThreatFeedSyncResult(BaseModel):
    fetched: int
    stored_new: int
    updated: int
    fetched_at: str
