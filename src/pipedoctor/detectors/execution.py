"""Engine-aware execution diagnostics."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_execution(profile: DataProfile) -> list[Finding]:
    """Return execution-oriented findings for engines without plan text."""

    if profile.engine != "pandas":
        return []

    findings: list[Finding] = []
    execution = profile.execution
    memory_mb = float(execution.get("memory_mb") or 0.0)
    object_count = int(execution.get("object_column_count") or 0)
    object_ratio = float(execution.get("object_column_ratio") or 0.0)
    duplicate_index_count = int(execution.get("duplicate_index_count") or 0)
    duplicate_column_count = int(execution.get("duplicate_column_count") or 0)

    if memory_mb >= 100:
        findings.append(
            Finding(
                rule_id="PD_EXEC_001",
                title="Large in-memory Pandas frame",
                severity="medium" if memory_mb >= 500 else "low",
                category="execution",
                message=f"The DataFrame uses about {memory_mb:.2f} MB in local memory.",
                recommendation="Consider narrower selects, categorical dtypes, chunking, or a distributed engine if this frame keeps growing.",
                evidence={"memory_mb": memory_mb, "rows": profile.rows, "columns": profile.column_count},
            )
        )

    if profile.column_count >= 100:
        findings.append(
            Finding(
                rule_id="PD_EXEC_002",
                title="Very wide Pandas frame",
                severity="medium" if profile.column_count >= 250 else "low",
                category="execution",
                message=f"The DataFrame has {profile.column_count} columns.",
                recommendation="Select only the columns needed for the next step to reduce memory pressure and accidental wide operations.",
                evidence={"column_count": profile.column_count},
            )
        )

    if object_count >= 3 and object_ratio >= 0.5:
        findings.append(
            Finding(
                rule_id="PD_EXEC_003",
                title="Object-heavy Pandas frame",
                severity="medium" if object_ratio >= 0.8 else "low",
                category="execution",
                message=f"{object_count} column(s) use object/string dtype ({object_ratio:.0%} of columns).",
                recommendation="Review whether repeated strings can use categorical dtype or whether parsing should happen earlier.",
                evidence={
                    "object_column_count": object_count,
                    "object_column_ratio": round(object_ratio, 4),
                    "object_columns": execution.get("object_columns", []),
                },
            )
        )

    if duplicate_index_count:
        findings.append(
            Finding(
                rule_id="PD_EXEC_004",
                title="Duplicate Pandas index labels",
                severity="medium",
                category="execution",
                message=f"The index contains {duplicate_index_count} duplicate label(s).",
                recommendation="Reset or validate the index before alignment-sensitive joins, updates, or reindexing operations.",
                evidence={"duplicate_index_count": duplicate_index_count},
            )
        )

    if duplicate_column_count:
        findings.append(
            Finding(
                rule_id="PD_EXEC_005",
                title="Duplicate Pandas column labels",
                severity="medium",
                category="execution",
                message=f"The DataFrame contains {duplicate_column_count} duplicate column label(s).",
                recommendation="Rename or deduplicate columns before selection, export, or merge operations.",
                evidence={"duplicate_column_count": duplicate_column_count},
            )
        )

    return findings
