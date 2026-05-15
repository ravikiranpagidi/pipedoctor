import pandas as pd

from pipedoctor import diagnose_execution, diagnose_plan_text


def test_diagnose_execution_finds_pandas_execution_risks():
    df = pd.DataFrame(
        {
            "a": ["x", "y", "z"],
            "b": ["u", "v", "w"],
            "c": ["m", "n", "o"],
        },
        index=[1, 1, 2],
    )
    df["a_copy"] = df["a"]
    df.columns = ["a", "b", "c", "a"]

    report = diagnose_execution(df, show=False)

    rule_ids = {finding.rule_id for finding in report.findings}
    assert "PD_EXEC_003" in rule_ids
    assert "PD_EXEC_004" in rule_ids
    assert "PD_EXEC_005" in rule_ids


def test_diagnose_plan_text_finds_spark_plan_signals():
    report = diagnose_plan_text(
        """
        AdaptiveSparkPlan
        +- Exchange hashpartitioning(customer_id#1, 200)
        +- Exchange hashpartitioning(product_id#2, 200)
        +- Exchange hashpartitioning(country#3, 200)
        +- SortMergeJoin
        """,
        show=False,
    )

    rule_ids = {finding.rule_id for finding in report.findings}
    assert "PD_PERF_002" in rule_ids
    assert "PD_PERF_003" in rule_ids
