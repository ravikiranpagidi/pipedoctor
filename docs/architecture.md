# PipeDoctor Architecture

PipeDoctor is intentionally small. The library has four layers:

1. Public API: `diagnose` and `diagnose_join`.
2. Adapters: normalize Pandas and PySpark objects into a `DataProfile`.
3. Detectors: pure functions that turn a `DataProfile` into findings.
4. Reporters: console, JSON, Markdown, and HTML rendering.

This keeps the project friendly for contributors. A new check should usually be one detector function plus tests.

## Package Layout

```text
src/pipedoctor/
  api.py                 public API
  models.py              report, finding, and profile dataclasses
  adapters/              Pandas and PySpark profiling
  detectors/             built-in diagnostic rules
  reporters/             console/HTML/Markdown rendering
  recommendations/       future richer recommendation hooks
  utils/                 internal helpers
```

## Adapter Contract

Adapters return `DataProfile`, a small normalized object with schema, nulls, duplicate metrics, cardinality, numeric stats, partition metadata, CDC hints, and optional Spark plan text.

Adapters should be lazy. PipeDoctor should not import Pandas, PySpark, or warehouse SDKs unless the user actually passes that type of object.

## Detector Contract

A detector accepts one or more profiles and returns a list of `Finding` objects.

```python
def detect_nulls(profile: DataProfile) -> list[Finding]:
    ...
```

Rules should be:

- explainable
- fast enough for notebooks
- conservative about severity
- specific about next action

## Spark Safety

Spark analysis uses bounded sampling by default. Full-table data-quality checks are valuable, but they should be explicit in a future `mode="full"` API. The default path should not surprise users with expensive jobs.

## Future Plugin Direction

The current detector layout can evolve into:

```python
from pipedoctor import registry

registry.add_rule(my_rule)
```

The first plugin targets should be Polars, DuckDB, Delta Lake metadata, and SQL text diagnostics.
