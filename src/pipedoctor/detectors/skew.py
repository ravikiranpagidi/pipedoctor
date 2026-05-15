"""Skew detection."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_skew(profile: DataProfile) -> list[Finding]:
    findings: list[Finding] = []
    for column, metrics in profile.hot_values.items():
        pct = metrics.get("top_pct")
        if pct is None:
            continue
        if pct >= 0.7:
            severity = "high"
        elif pct >= 0.45:
            severity = "medium"
        elif pct >= 0.3:
            severity = "low"
        else:
            continue
        findings.append(
            Finding(
                rule_id="PD_SKEW_001",
                title=f"Candidate skew key: {column}",
                severity=severity,
                category="skew",
                message=f"Top value {metrics.get('top_value')!r} holds {pct:.2%} of checked rows.",
                recommendation="Repartition, salt, or isolate this key before wide joins or aggregations.",
                evidence={"column": column, **metrics},
            )
        )
    return findings
