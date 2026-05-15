"""Partition health detection."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_partition_health(profile: DataProfile) -> list[Finding]:
    if profile.engine != "pyspark":
        return []
    count = profile.partitions.get("count")
    if count is None:
        return []
    findings: list[Finding] = []
    rows = profile.rows or 0
    if count <= 1 and rows >= 1000:
        findings.append(
            Finding(
                rule_id="PD_PART_001",
                title="Underpartitioned Spark DataFrame",
                severity="medium",
                category="partitions",
                message=f"The checked DataFrame has {count} partition for about {rows} sampled row(s).",
                recommendation="Increase partitions before wide transformations if the real dataset is large.",
                evidence={"partitions": count, "sample_rows": rows},
            )
        )
    if count > max(200, rows * 2) and rows:
        findings.append(
            Finding(
                rule_id="PD_PART_002",
                title="Possible overpartitioning",
                severity="low",
                category="partitions",
                message=f"{count} partitions for about {rows} sampled row(s) can create scheduling overhead.",
                recommendation="Reduce partitions before small writes or narrow transformations.",
                evidence={"partitions": count, "sample_rows": rows},
            )
        )
    return findings
