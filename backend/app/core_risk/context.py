"""Intelligent context-derivation helpers.

These translate raw NVD/EPSS/CISA-KEV data into the qualitative context
inputs (attack path complexity, exploit availability, threat actor
sophistication, etc.) that VulnerabilityData expects. Ported from the
original scoring service's request-handling logic and kept dependency-free
so they're independently testable.
"""

from __future__ import annotations

from typing import Any, Dict

from app.data_sources.epss import EPSSData
from app.data_sources.nvd import CVEData


def determine_cia_impact(cve_data: CVEData | None) -> Dict[str, float]:
    if not cve_data:
        return {"confidentiality": 0.8, "integrity": 0.8, "availability": 0.8}

    impact_mapping = {"HIGH": 1.0, "LOW": 0.6, "NONE": 0.2}
    return {
        "confidentiality": impact_mapping.get(cve_data.confidentiality_impact, 0.8),
        "integrity": impact_mapping.get(cve_data.integrity_impact, 0.8),
        "availability": impact_mapping.get(cve_data.availability_impact, 0.8),
    }


def determine_attack_complexity(
    cve_data: CVEData | None, is_internet_facing: bool
) -> str:
    if not cve_data:
        return "direct"

    if cve_data.attack_vector == "NETWORK":
        return "direct" if is_internet_facing else "single-hop"
    if cve_data.attack_vector == "ADJACENT_NETWORK":
        return "multi-hop"
    if cve_data.attack_vector in ("LOCAL", "PHYSICAL"):
        return "complex"
    return "direct"


def determine_exploit_availability(
    cve_data: CVEData | None, epss_data: EPSSData | None
) -> str:
    if not cve_data:
        return "details"

    if cve_data.cisa_kev:
        return "automated"
    if cve_data.has_exploit_references:
        return "manual"
    if epss_data and epss_data.epss_score >= 0.5:
        return "poc"
    if epss_data and epss_data.epss_score >= 0.1:
        return "details"
    if epss_data and epss_data.epss_score >= 0.01:
        return "limited"
    return "specialized"


def determine_discovery_difficulty(
    cve_data: CVEData | None, is_internet_facing: bool
) -> str:
    if not cve_data:
        return "standard"

    if is_internet_facing:
        return "easy" if cve_data.attack_complexity == "LOW" else "standard"

    if cve_data.privileges_required == "NONE":
        return "authenticated"
    if cve_data.privileges_required == "LOW":
        return "specialized"
    return "manual"


def determine_exploitation_frequency(
    cve_data: CVEData | None, epss_data: EPSSData | None
) -> str:
    if not cve_data:
        return "none"

    if cve_data.cisa_kev:
        return "kev"
    if epss_data:
        if epss_data.percentile >= 95.0 and epss_data.epss_score >= 0.8:
            return "active"
        if epss_data.epss_score >= 0.5:
            return "known"
        if epss_data.epss_score >= 0.1:
            return "sporadic"
        if epss_data.epss_score >= 0.01:
            return "none"
        return "academic"
    return "none"


def determine_target_attractiveness(asset_criticality: int) -> str:
    if asset_criticality >= 9:
        return "high-value"
    if asset_criticality >= 7:
        return "medium-value"
    if asset_criticality >= 4:
        return "standard"
    if asset_criticality >= 2:
        return "low-value"
    return "specialized"


def determine_threat_actor_sophistication(
    cve_data: CVEData | None, epss_data: EPSSData | None
) -> str:
    if not cve_data:
        return "standard"

    if cve_data.cisa_kev:
        return "apt" if epss_data and epss_data.percentile >= 90.0 else "organized"
    if epss_data and epss_data.epss_score >= 0.3:
        return "organized"
    if cve_data.has_exploit_references:
        return "skilled"
    return "standard"


def determine_resource_level(cve_data: CVEData | None, asset_criticality: int) -> str:
    if not cve_data:
        return "standard"

    if cve_data.cisa_kev and asset_criticality >= 8:
        return "well-funded"
    if cve_data.cisa_kev or asset_criticality >= 8:
        return "moderate"
    return "standard"


def determine_patch_availability(vulnerability_age_days: int) -> str:
    if vulnerability_age_days <= 7:
        return "none"
    if vulnerability_age_days <= 30:
        return "complex"
    if vulnerability_age_days <= 180:
        return "standard"
    if vulnerability_age_days <= 730:
        return "deployed"
    return "mandated"


def determine_disclosure_timeline(vulnerability_age_days: int) -> str:
    if vulnerability_age_days <= 1:
        return "zero-day"
    if vulnerability_age_days <= 30:
        return "coordinated"
    if vulnerability_age_days <= 90:
        return "standard"
    if vulnerability_age_days <= 365:
        return "responsible"
    return "full"


def build_cve_intelligence(
    cve_data: CVEData | None, epss_data: EPSSData | None
) -> Dict[str, Any]:
    """Flat intelligence payload consumed by the frontend CVE detail components."""
    return {
        "epss_score": epss_data.epss_score if epss_data else 0,
        "epss_percentile": epss_data.percentile if epss_data else 0,
        "cvss_score": cve_data.cvss_score if cve_data else 0,
        "cvss_vector": cve_data.cvss_vector if cve_data else "",
        "cisa_kev": cve_data.cisa_kev if cve_data else False,
        "has_exploit_references": (
            cve_data.has_exploit_references if cve_data else False
        ),
        "published_date": cve_data.published_date if cve_data else None,
        "modified_date": cve_data.modified_date if cve_data else None,
        "vulnerability_age_days": cve_data.vulnerability_age_days if cve_data else 0,
        "attack_vector": cve_data.attack_vector if cve_data else "NETWORK",
        "attack_complexity": cve_data.attack_complexity if cve_data else "LOW",
        "privileges_required": cve_data.privileges_required if cve_data else "NONE",
        "user_interaction": cve_data.user_interaction if cve_data else "NONE",
        "scope": cve_data.scope if cve_data else "UNCHANGED",
        "confidentiality_impact": (
            cve_data.confidentiality_impact if cve_data else "NONE"
        ),
        "integrity_impact": cve_data.integrity_impact if cve_data else "NONE",
        "availability_impact": cve_data.availability_impact if cve_data else "NONE",
    }
