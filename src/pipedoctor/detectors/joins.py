"""Join explosion risk detection."""

from __future__ import annotations

from typing import Any, Iterable, List

from pipedoctor.adapters.base import engine_name
from pipedoctor.adapters.pandas import profile_pandas
from pipedoctor.models import DataProfile, Finding


def detect_join_risk(
    left: DataProfile,
    right: DataProfile,
    *,
    on: Iterable[str],
) -> list[Finding]:
    keys = list(on)
    findings: list[Finding] = []
    left_dup = _key_duplicate_pct(left, keys)
    right_dup = _key_duplicate_pct(right, keys)
    if left_dup is not None and right_dup is not None and left_dup > 0 and right_dup > 0:
        severity = "critical" if left_dup >= 0.1 and right_dup >= 0.1 else "high"
        findings.append(
            Finding(
                rule_id="PD_JOIN_001",
                title="Many-to-many join risk",
                severity=severity,
                category="joins",
                message="Both sides have duplicate rows for the proposed join key.",
                recommendation="Pre-aggregate, deduplicate, or join on a more specific key before production execution.",
                evidence={
                    "join_keys": keys,
                    "left_duplicate_pct": round(left_dup, 4),
                    "right_duplicate_pct": round(right_dup, 4),
                },
            )
        )
    if left.rows and right.rows:
        ratio = max(left.rows, right.rows) / max(min(left.rows, right.rows), 1)
        smaller = min(left.rows, right.rows)
        if smaller <= 10000 and ratio >= 5:
            findings.append(
                Finding(
                    rule_id="PD_JOIN_002",
                    title="Broadcast join opportunity",
                    severity="low",
                    category="joins",
                    message="One side of the join is much smaller than the other.",
                    recommendation="For Spark, consider broadcasting the smaller side if it fits in executor memory.",
                    evidence={"left_rows": left.rows, "right_rows": right.rows, "size_ratio": round(ratio, 2)},
                )
            )
    return findings


def profile_for_join(obj: Any, *, name: str, on: List[str]) -> DataProfile:
    engine = engine_name(obj)
    if engine == "pandas":
        return profile_pandas(obj, name=name, key_columns=on)
    if engine == "pyspark":
        from pipedoctor.adapters.spark import profile_spark

        return profile_spark(obj, name=name, key_columns=on, sample_rows=10000)
    raise TypeError(f"Unsupported DataFrame type for join diagnosis: {type(obj)!r}")


def _key_duplicate_pct(profile: DataProfile, keys: list[str]) -> float | None:
    joined = ",".join(keys)
    if joined in profile.duplicates.get("keys", {}):
        return profile.duplicates["keys"][joined].get("pct")
    return None
