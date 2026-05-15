import json

import pandas as pd

from pipedoctor import diagnose, diagnose_join


def test_diagnose_pandas_finds_common_issues():
    df = pd.DataFrame(
        {
            "customer_id": [1, 1, 2, None, None, None, 4, 5],
            "country": ["US", "US", "US", "US", "US", "IN", "UK", "US"],
            "amount": [10, 10, 20, 9999, 18, 17, 16, 15],
            "event_time": pd.to_datetime(
                [
                    "2026-05-01 10:00",
                    "2026-05-01 10:00",
                    "2026-05-01 10:01",
                    "2026-05-01 09:58",
                    "2026-05-01 10:04",
                    "2026-05-01 10:05",
                    "2026-05-01 10:06",
                    "2026-05-01 10:07",
                ]
            ),
        }
    )

    report = diagnose(
        df,
        name="orders",
        key_columns=["customer_id"],
        critical_columns=["customer_id"],
        cdc_order_column="event_time",
        show=False,
    )

    rule_ids = {finding.rule_id for finding in report.findings}
    assert "PD_NULL_001" in rule_ids
    assert "PD_DUP_002" in rule_ids
    assert "PD_SKEW_001" in rule_ids
    assert report.score < 100


def test_schema_drift_between_pandas_dataframes():
    previous = pd.DataFrame({"id": [1], "amount": [10.0], "old_col": ["x"]})
    current = pd.DataFrame({"id": [1], "amount": ["10.0"], "new_col": ["y"]})

    report = diagnose(current, previous=previous, show=False)

    rule_ids = {finding.rule_id for finding in report.findings}
    assert "PD_SCHEMA_001" in rule_ids
    assert "PD_SCHEMA_002" in rule_ids
    assert "PD_SCHEMA_003" in rule_ids


def test_report_exports_are_strings_and_optionally_write_files(tmp_path):
    df = pd.DataFrame({"id": [1, 1], "value": [10, 10]})
    report = diagnose(df, show=False)

    payload = json.loads(report.to_json())
    assert payload["score"] <= 100

    markdown_path = tmp_path / "report.md"
    html_path = tmp_path / "report.html"

    assert "# PipeDoctor Report" in report.to_markdown(str(markdown_path))
    assert "<!doctype html>" in report.to_html(str(html_path))
    assert markdown_path.exists()
    assert html_path.exists()


def test_diagnose_join_detects_many_to_many_risk():
    left = pd.DataFrame({"customer_id": [1, 1, 2], "amount": [10, 20, 30]})
    right = pd.DataFrame({"customer_id": [1, 1, 3], "segment": ["a", "a", "b"]})

    report = diagnose_join(left, right, on=["customer_id"], show=False)

    assert any(finding.rule_id == "PD_JOIN_001" for finding in report.findings)
