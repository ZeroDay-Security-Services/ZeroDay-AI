"""Threat intelligence feed client -- abuse.ch ThreatFox.

ThreatFox is a free, public IOC (indicator of compromise) feed run by
abuse.ch. No API key is required for read queries. This replaces the
placeholder threat_feeds.py from the upload (which pointed at a literal
`example.com` URL and did no real parsing) with a client against a real,
documented API: https://threatfox.abuse.ch/api/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("zeroday.threat_feed")

THREATFOX_API_URL = "https://threatfox-api.abuse.ch/api/v1/"


@dataclass
class ThreatIndicatorData:
    ioc_value: str
    ioc_type: str
    threat_type: str
    malware: str | None
    confidence_level: int
    first_seen: str | None
    last_seen: str | None
    tags: list[str]
    source_reference: str


class ThreatFeedClient:
    """Client for abuse.ch ThreatFox recent-IOC feed."""

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def get_recent_iocs(
        self, days: int = 3, limit: int = 200
    ) -> list[ThreatIndicatorData]:
        """Fetch IOCs reported in the last `days` days. Returns an empty
        list (never raises) on any network/parsing failure so callers can
        degrade gracefully -- consistent with the NVD/EPSS clients."""
        payload = {"query": "get_iocs", "days": days}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(THREATFOX_API_URL, json=payload)
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("ThreatFox fetch failed: %s", exc)
            return []

        if body.get("query_status") != "ok":
            logger.info("ThreatFox query_status: %s", body.get("query_status"))
            return []

        indicators: list[ThreatIndicatorData] = []
        for item in body.get("data", [])[:limit]:
            try:
                indicators.append(self._parse_indicator(item))
            except (KeyError, TypeError, ValueError) as exc:
                logger.debug("Skipping malformed ThreatFox record: %s", exc)
                continue
        return indicators

    def _parse_indicator(self, item: dict[str, Any]) -> ThreatIndicatorData:
        return ThreatIndicatorData(
            ioc_value=item["ioc"],
            ioc_type=item.get("ioc_type", "unknown"),
            threat_type=item.get("threat_type", "unknown"),
            malware=item.get("malware_printable") or item.get("malware"),
            confidence_level=int(item.get("confidence_level", 0)),
            first_seen=item.get("first_seen"),
            last_seen=item.get("last_seen"),
            tags=item.get("tags") or [],
            source_reference=item.get("reference", ""),
        )

    @staticmethod
    def fetched_at() -> str:
        return datetime.now(timezone.utc).isoformat()
