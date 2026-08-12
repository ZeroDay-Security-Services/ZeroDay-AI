"""Real statistical behavioral-anomaly detection.

Replaces the uploaded behavioral_analytics.py / behavioral_analysis.py,
which either returned a hardcoded {"anomalies_detected": True, ...} for
any input or used a fixed magic-number threshold with no statistical
basis.

Uses the modified z-score (median + median absolute deviation, per
Iglewicz & Hoaglin) rather than mean/stdev. A plain mean/stdev z-score is
vulnerable to "masking": one extreme outlier drags the mean toward itself
and inflates the stdev, which can hide the very outlier it should flag
(verified against this project's own test data during integration -- a
single 950-vs-~12 outlier scored a boundary z of exactly 2.0 and failed
to trigger). Median/MAD is resistant to that because a single extreme
value barely moves the median.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Dict, List

# Iglewicz & Hoaglin's constant relating MAD to standard deviation for a
# normal distribution; standard in modified z-score anomaly detection.
_MAD_CONSTANT = 0.6745


@dataclass
class ActivityEvent:
    user_id: str
    activity_level: float
    label: str = ""


@dataclass
class AnomalyResult:
    user_id: str
    activity_level: float
    z_score: float
    is_anomaly: bool
    label: str


def _fallback_stdev_z(level: float, baseline: List[float]) -> float:
    if len(baseline) < 2:
        return 0.0
    stdev = statistics.pstdev(baseline)
    if stdev == 0:
        return 0.0
    mean = statistics.fmean(baseline)
    return (level - mean) / stdev


def _modified_z(level: float, baseline: List[float]) -> float:
    median = statistics.median(baseline)
    abs_deviations = [abs(x - median) for x in baseline]
    mad = statistics.median(abs_deviations)

    if mad > 0:
        return _MAD_CONSTANT * (level - median) / mad

    # MAD is 0 when at least half the baseline equals the median (e.g.
    # mostly constant data with one spike). Fall back to a stdev-based
    # z-score so a genuine spike still surfaces instead of dividing by
    # zero and silently reporting "no anomaly".
    return _fallback_stdev_z(level, baseline)


def detect_anomalies(
    events: List[ActivityEvent], z_threshold: float = 3.5
) -> List[AnomalyResult]:
    """Flags events whose modified z-score exceeds `z_threshold` (3.5 is
    the standard Iglewicz & Hoaglin recommendation) against that user's
    own activity history. Falls back to the population's history for
    users with fewer than 2 events, since a per-user baseline needs at
    least two data points."""

    by_user: Dict[str, List[ActivityEvent]] = {}
    for e in events:
        by_user.setdefault(e.user_id, []).append(e)

    population_levels = [e.activity_level for e in events]

    results: List[AnomalyResult] = []
    for user_id, user_events in by_user.items():
        levels = [e.activity_level for e in user_events]
        baseline = levels if len(levels) >= 2 else population_levels

        for e in user_events:
            z = _modified_z(e.activity_level, baseline)
            results.append(
                AnomalyResult(
                    user_id=user_id,
                    activity_level=e.activity_level,
                    z_score=round(z, 3),
                    is_anomaly=abs(z) >= z_threshold,
                    label=e.label,
                )
            )
    return results
