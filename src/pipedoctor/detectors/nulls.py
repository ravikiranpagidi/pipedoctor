"""Null-risk detection."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_nulls(
    current: DataProfile,
    previous: DataProfile | None = None,
    *,
    critical_columns: list[str] | None = None,
) -> list[Finding]:
    critical = set(critical_columns or [])
    findings: list[Finding] = []
    for column, metrics in current.nulls.items():
        pct = metrics.get("pct")
        if pct is None:
            continue
        severity = None
        if column in critical and pct > 0:
            severity = "high"
        elif pct >= 0.5:
            severity = "high"
        elif pct >= 0.2:
            severity = "medium"
        elif pct >= 0.05:
            severity = "low"
        if severity:
            findings.append(
                Finding(
                    rule_id="PD_NULL_001",
                    title=f"Null risk in {column}",
                    severity=severity,
                    category="nulls",
                    message=f"{pct:.2%} of values are null.",
                    recommendation="Validate upstream joins, source extracts, and required-field checks for this column.",
                    evidence={"column": column, "null_pct": round(pct, 4), "null_count": metrics.get("count")},
                )
            )

    if previous:
        for column, metrics in current.nulls.items():
            current_pct = metrics.get("pct")
            prev_pct = previous.nulls.get(column, {}).get("pct")
            if current_pct is None or prev_pct is None:
                continue
            delta = current_pct - prev_pct
            if delta >= 0.1:
                findings.append(
                    Finding(
                        rule_id="PD_NULL_002",
                        title=f"Null spike in {column}",
                        severity="high" if delta >= 0.25 else "medium",
                        category="nulls",
                        message=f"Null percentage increased from {prev_pct:.2%} to {current_pct:.2%}.",
                        recommendation="Compare the latest source batch, join keys, and transformation logic against the previous run.",
                        evidence={
                            "column": column,
                            "previous_null_pct": round(prev_pct, 4),
                            "current_null_pct": round(current_pct, 4),
                            "delta": round(delta, 4),
                        },
                    )
                )
    return findings
