# PipeDoctor

Instant health checks and diagnostics for Pandas, PySpark, and data pipelines.

PipeDoctor is a small Python library for the first 30 seconds of pipeline debugging: null spikes, duplicate records, schema drift, skew, risky joins, partition smells, CDC ordering issues, and plan-level performance hints.

It is not an orchestration platform or a monitoring dashboard. It is a fast local doctor for data engineers who want a useful answer while the DataFrame is still in front of them.

```python
from pipedoctor import diagnose

report = diagnose(df)
```

## One Call, Engine-Aware Underneath

`diagnose(df)` is the public API. PipeDoctor inspects the object you pass in, selects the matching adapter, builds a normalized profile, and runs the same detector set on top of that profile.

| Input today | What PipeDoctor does |
| --- | --- |
| Pandas `DataFrame` | Profiles the local DataFrame directly |
| PySpark `DataFrame` | Uses bounded sampling plus Spark schema and plan signals |

That design keeps the call site simple while letting the internals stay engine-specific. You do not need separate functions such as `diagnose_pandas()` or `diagnose_spark()`. The current release supports Pandas and PySpark. Future SQL relation or SQL-text adapters can use the same public entry point once they are implemented, so users should not need to learn a second API for each engine.

Example output:

```text
PipeDoctor report for dataframe
Engine: pandas | Health score: 62/100 | Findings: 5

⚠ HIGH   Null risk in customer_id
  37.50% of values are null.
  Try validating upstream joins or source extracts before this field is used as a key.

⚠ MEDIUM Duplicate rows detected
  2 duplicate rows found in 8 sampled rows.
  Add a uniqueness test or deduplicate on stable business keys.

✅ LOW    Candidate skew key: country
  Top value 'US' holds 75.00% of rows.
  Repartition or salt by this key before wide joins or aggregations.
```

## Install

From GitHub while the project is young:

```bash
pip install git+https://github.com/ravikiranpagidi/pipedoctor.git
```

For Pandas examples:

```bash
pip install "pipedoctor[pandas] @ git+https://github.com/ravikiranpagidi/pipedoctor.git"
```

From a clone:

```bash
pip install -e ".[dev]"
pytest
```

## Quick Start With Pandas

```python
import pandas as pd
from pipedoctor import diagnose

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
    name="orders_pipeline",
    key_columns=["customer_id"],
    cdc_order_column="event_time",
)

report.to_markdown("pipedoctor-report.md")
report.to_html("pipedoctor-report.html")
```

## Quick Start With PySpark

PipeDoctor works with PySpark DataFrames without importing Spark at package import time.

```python
from pipedoctor import diagnose

report = diagnose(
    spark_df,
    name="daily_orders_job",
    key_columns=["customer_id"],
    sample_rows=10000,
)
```

For Spark, PipeDoctor uses bounded sampling for data-quality checks and parses the execution plan for shuffle, join, UDF, sort, and partition hints. That keeps the default notebook workflow practical.

## Schema Drift

Compare a current DataFrame against a previous DataFrame or a stored schema:

```python
report = diagnose(current_df, previous=previous_df)
```

PipeDoctor detects added columns, removed columns, type changes, and nullability changes.

## Join Risk

Use `diagnose_join` before an expensive join:

```python
from pipedoctor import diagnose_join

join_report = diagnose_join(left_df, right_df, on=["customer_id"])
```

It checks key duplication, many-to-many risk, estimated explosion, and broadcast opportunities.

## CLI

```bash
pipedoctor demo
pipedoctor csv examples/orders.csv --key customer_id
pipedoctor csv examples/orders.csv --format markdown --output report.md
```

## What It Checks Today

| Area | Checks |
| --- | --- |
| Schema drift | Added, removed, type-changed, and nullability-changed columns |
| Nulls | Null percentage, critical key nulls, spike versus previous data |
| Duplicates | Exact row duplicates and duplicate business keys |
| Skew | Hot values and high top-value share for candidate key columns |
| Join explosion | Many-to-many join risk and estimated cardinality growth |
| Partitions | Spark partition count, overpartitioning, underpartitioning hints |
| Distribution | Numeric outliers and cardinality anomalies |
| Performance | Spark plan signals: exchanges, sort-merge joins, Cartesian joins, Python UDFs, wide plans |
| CDC | Duplicate change events, missing order column, late-arriving records |
| Summary | Health score, risk list, and recommendations |

## Report Exports

```python
report.to_dict()
report.to_json()
report.to_markdown()
report.to_html()
```

All report methods also accept a path:

```python
report.to_json("report.json")
```

## Design Principles

- one-line first use
- no required runtime dependencies
- lazy Pandas and PySpark support
- one public API with engine-specific adapters underneath
- safe bounded sampling for Spark
- plain Python report objects
- explainable rules, not magic scores
- easy first contributions

## Good First PRs

- add a Polars adapter
- add a DuckDB relation adapter
- add more Spark plan rules
- add Great Expectations export
- add SARIF output for CI
- add Databricks notebook examples
- add more CDC rules
- add report themes

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/architecture.md](docs/architecture.md).

## Roadmap

Near term:

- custom rule registry
- richer Spark skew metrics
- SQL text diagnostics
- Delta Lake and Iceberg metadata checks
- notebook widgets for before/after comparisons

Later:

- AI-ready recommendation bundles
- OpenTelemetry export
- warehouse adapters for Snowflake, BigQuery, DuckDB, and Databricks SQL
- historical health baselines
- pipeline-level report comparison

## License

MIT
