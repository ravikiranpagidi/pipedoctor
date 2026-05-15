"""Duplicate detection."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_duplicates(profile: DataProfile) -> list[Finding]:
    findings: list[Finding] = []
    exact_pct = profile.duplicates.get("exact_pct")
    exact_count = profile.duplicates.get("exact_count")
    if exact_pct is not None and exact_pct > 0:
        severity = "high" if exact_pct >= 0.2 else "medium"
        findings.append(
            Finding(
                rule_id="PD_DUP_001",
                title="Duplicate rows detected",
                severity=severity,
                category="duplicates",
                message=f"{exact_count} duplicate row(s) found in the checked data.",
                recommendation="Add a uniqueness test or deduplicate on stable business keys before downstream joins.",
                evidence={"duplicate_count": exact_count, "duplicate_pct": round(exact_pct, 4)},
            )
        )

    for key, values in profile.duplicates.get("keys", {}).items():
        pct = values.get("pct")
        count = values.get("count")
        if pct is not None and pct > 0:
            findings.append(
                Finding(
                    rule_id="PD_DUP_002",
                    title=f"Duplicate key values for {key}",
                    severity="high" if pct >= 0.1 else "medium",
                    category="duplicates",
                    message=f"{count} duplicate key row(s) found for {key}.",
                    recommendation="Check whether this key should be unique. If not, avoid joining it as if it were one-to-one.",
                    evidence={"key": key, "duplicate_key_count": count, "duplicate_key_pct": round(pct, 4)},
                )
            )
    return findings
