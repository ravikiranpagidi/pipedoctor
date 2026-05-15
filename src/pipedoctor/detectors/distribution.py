"""Distribution and anomaly detection."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_distribution(profile: DataProfile) -> list[Finding]:
    findings: list[Finding] = []
    for column, metrics in profile.numeric.items():
        outlier_pct = metrics.get("outlier_pct")
        outlier_count = metrics.get("outlier_count")
        if outlier_pct is not None and outlier_pct >= 0.05:
            findings.append(
                Finding(
                    rule_id="PD_DIST_001",
                    title=f"Outliers detected in {column}",
                    severity="medium" if outlier_pct >= 0.15 else "low",
                    category="distribution",
                    message=f"{outlier_count} outlier value(s) found using an IQR check.",
                    recommendation="Confirm whether these values are valid business extremes or source-quality issues.",
                    evidence={"column": column, **metrics},
                )
            )
        min_value = metrics.get("min")
        max_value = metrics.get("max")
        mean = metrics.get("mean")
        if min_value is not None and max_value is not None and mean not in (None, 0):
            spread = abs(max_value - min_value) / max(abs(mean), 1)
            if spread >= 100:
                findings.append(
                    Finding(
                        rule_id="PD_DIST_002",
                        title=f"Wide numeric spread in {column}",
                        severity="low",
                        category="distribution",
                        message="The min/max range is very large relative to the mean.",
                        recommendation="Check for unit mismatches, default values, or mixed granularities.",
                        evidence={"column": column, "spread_ratio": round(spread, 2), **metrics},
                    )
                )
    return findings
