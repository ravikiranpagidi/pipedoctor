"""CDC health checks."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_cdc_health(profile: DataProfile, *, key_columns: list[str] | None = None) -> list[Finding]:
    keys = key_columns or []
    cdc = profile.cdc
    findings: list[Finding] = []
    possible_cdc_columns = {"op", "operation", "change_type", "event_time", "updated_at", "sequence", "version"}
    looks_like_cdc = bool(possible_cdc_columns & set(profile.columns)) or bool(keys)

    if looks_like_cdc and not cdc.get("has_order_column"):
        findings.append(
            Finding(
                rule_id="PD_CDC_001",
                title="CDC ordering column not configured",
                severity="medium",
                category="cdc",
                message="This data looks like change-event data, but no ordering column was provided.",
                recommendation="Pass cdc_order_column='event_time' or a sequence/version column to detect late events.",
                evidence={"key_columns": keys, "available_columns": profile.columns},
            )
        )
    duplicate_events = cdc.get("duplicate_events")
    if duplicate_events:
        findings.append(
            Finding(
                rule_id="PD_CDC_002",
                title="Duplicate CDC events detected",
                severity="high",
                category="cdc",
                message=f"{duplicate_events} duplicate change event(s) were found for the configured keys and order column.",
                recommendation="Deduplicate by business key plus ordering column before applying merge/upsert logic.",
                evidence={"duplicate_events": duplicate_events, "order_column": cdc.get("order_column")},
            )
        )
    late_events = cdc.get("late_events")
    if late_events:
        findings.append(
            Finding(
                rule_id="PD_CDC_003",
                title="Late-arriving CDC events detected",
                severity="medium",
                category="cdc",
                message=f"{late_events} key group(s) appear to contain out-of-order change events.",
                recommendation="Apply watermarking or sort within key before merge/upsert processing.",
                evidence={"late_events": late_events, "order_column": cdc.get("order_column")},
            )
        )
    return findings
