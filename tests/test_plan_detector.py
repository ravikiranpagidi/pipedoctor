from pipedoctor.detectors.performance import detect_performance
from pipedoctor.models import DataProfile


def test_performance_detector_finds_shuffle_and_join_signals():
    profile = DataProfile(
        engine="pyspark",
        name="plan",
        rows=None,
        columns=[],
        schema={},
        plan_text="""
        AdaptiveSparkPlan
        +- Exchange hashpartitioning(customer_id#1, 200)
        +- Exchange hashpartitioning(product_id#2, 200)
        +- Exchange hashpartitioning(country#3, 200)
        +- SortMergeJoin
        """,
    )

    findings = detect_performance(profile)

    rule_ids = {finding.rule_id for finding in findings}
    assert "PD_PERF_002" in rule_ids
    assert "PD_PERF_003" in rule_ids
