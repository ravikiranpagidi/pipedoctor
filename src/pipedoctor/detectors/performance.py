"""Spark plan performance signal detection."""

from __future__ import annotations

from pipedoctor.models import DataProfile, Finding


def detect_performance(profile: DataProfile) -> list[Finding]:
    plan = profile.plan_text or ""
    if not plan:
        return []
    findings: list[Finding] = []
    lower = plan.lower()
    exchange_count = lower.count("exchange")
    sort_count = lower.count("sort")

    if "cartesianproduct" in lower or "broadcastnestedloopjoin" in lower:
        findings.append(
            Finding(
                rule_id="PD_PERF_001",
                title="Join explosion risk in Spark plan",
                severity="critical",
                category="performance",
                message="The Spark plan contains a Cartesian or nested-loop join signal.",
                recommendation="Check join keys, filters, and table sizes before running this on production data.",
                evidence={"plan_signal": "cartesian_or_nested_loop_join"},
            )
        )
    if exchange_count >= 3:
        findings.append(
            Finding(
                rule_id="PD_PERF_002",
                title="Excessive shuffle overhead",
                severity="high" if exchange_count >= 6 else "medium",
                category="performance",
                message=f"The Spark plan contains {exchange_count} Exchange operator(s).",
                recommendation="Review repartitions, groupBy keys, join keys, and broadcast opportunities.",
                evidence={"exchange_count": exchange_count},
            )
        )
    if "sortmergejoin" in lower and "broadcasthashjoin" not in lower:
        findings.append(
            Finding(
                rule_id="PD_PERF_003",
                title="Sort-merge join without broadcast signal",
                severity="low",
                category="performance",
                message="The plan uses SortMergeJoin and no BroadcastHashJoin signal was found.",
                recommendation="If one side is small, test a broadcast hint or update table statistics.",
                evidence={"plan_signal": "SortMergeJoin"},
            )
        )
    if "pythonudf" in lower or "batchedevalpython" in lower:
        findings.append(
            Finding(
                rule_id="PD_PERF_004",
                title="Python UDF in execution plan",
                severity="medium",
                category="performance",
                message="Python UDF execution can limit Catalyst optimization and increase serialization overhead.",
                recommendation="Prefer built-in Spark SQL functions or vectorized alternatives when possible.",
                evidence={"plan_signal": "python_udf"},
            )
        )
    if sort_count >= 3:
        findings.append(
            Finding(
                rule_id="PD_PERF_005",
                title="Many sort stages in Spark plan",
                severity="low",
                category="performance",
                message=f"The Spark plan contains {sort_count} Sort operator(s).",
                recommendation="Check whether all orderBy/sort operations are required before writing or aggregating.",
                evidence={"sort_count": sort_count},
            )
        )
    if len(plan.splitlines()) >= 80:
        findings.append(
            Finding(
                rule_id="PD_PERF_006",
                title="Very wide Spark plan",
                severity="low",
                category="performance",
                message="The Spark plan is large enough to be hard to reason about in reviews.",
                recommendation="Break the pipeline into named steps, persist only where useful, and inspect each phase separately.",
                evidence={"plan_lines": len(plan.splitlines())},
            )
        )
    return findings
