"""Schema drift detection."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from pipedoctor.models import DataProfile, Finding


def detect_schema_drift(
    current: DataProfile,
    previous: Optional[DataProfile] = None,
    baseline_schema: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> list[Finding]:
    baseline = baseline_schema or (previous.schema if previous else None)
    if not baseline:
        return []

    findings: list[Finding] = []
    current_cols = set(current.schema)
    baseline_cols = set(baseline)

    added = sorted(current_cols - baseline_cols)
    removed = sorted(baseline_cols - current_cols)
    type_changes = []
    nullability_changes = []

    for column in sorted(current_cols & baseline_cols):
        before = baseline[column]
        after = current.schema[column]
        if str(before.get("type")) != str(after.get("type")):
            type_changes.append(
                {
                    "column": column,
                    "before": before.get("type"),
                    "after": after.get("type"),
                }
            )
        if before.get("nullable") != after.get("nullable"):
            nullability_changes.append(
                {
                    "column": column,
                    "before": before.get("nullable"),
                    "after": after.get("nullable"),
                }
            )

    if removed:
        findings.append(
            Finding(
                rule_id="PD_SCHEMA_001",
                title="Columns removed since baseline",
                severity="high",
                category="schema",
                message=f"{len(removed)} column(s) disappeared from the current data.",
                recommendation="Check upstream extracts, select lists, and schema evolution before downstream jobs run.",
                evidence={"removed_columns": removed},
            )
        )
    if added:
        findings.append(
            Finding(
                rule_id="PD_SCHEMA_002",
                title="Columns added since baseline",
                severity="medium",
                category="schema",
                message=f"{len(added)} new column(s) appeared in the current data.",
                recommendation="Confirm downstream consumers tolerate the new fields before promoting the change.",
                evidence={"added_columns": added},
            )
        )
    if type_changes:
        findings.append(
            Finding(
                rule_id="PD_SCHEMA_003",
                title="Column type changes detected",
                severity="high",
                category="schema",
                message=f"{len(type_changes)} column(s) changed type.",
                recommendation="Add explicit casts or version the schema before this breaks joins, BI models, or ML features.",
                evidence={"type_changes": type_changes},
            )
        )
    if nullability_changes:
        findings.append(
            Finding(
                rule_id="PD_SCHEMA_004",
                title="Column nullability changed",
                severity="medium",
                category="schema",
                message=f"{len(nullability_changes)} column(s) changed nullability.",
                recommendation="Validate required-field assumptions and downstream constraints.",
                evidence={"nullability_changes": nullability_changes},
            )
        )
    return findings
