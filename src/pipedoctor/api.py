"""Public diagnosis functions."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from pipedoctor.adapters.base import engine_name
from pipedoctor.adapters.pandas import profile_pandas
from pipedoctor.detectors import (
    detect_cdc_health,
    detect_distribution,
    detect_duplicates,
    detect_join_risk,
    detect_nulls,
    detect_partition_health,
    detect_performance,
    detect_schema_drift,
    detect_skew,
)
from pipedoctor.detectors.joins import profile_for_join
from pipedoctor.models import DataProfile, DiagnoseOptions, DiagnosisReport, Finding


def diagnose(
    df: Any,
    *,
    name: str = "dataframe",
    previous: Any = None,
    baseline_schema: Optional[Mapping[str, Mapping[str, Any]]] = None,
    key_columns: Optional[Iterable[str]] = None,
    critical_columns: Optional[Iterable[str]] = None,
    cdc_order_column: Optional[str] = None,
    sample_rows: int = 10000,
    show: bool = True,
) -> DiagnosisReport:
    """Diagnose a Pandas or PySpark DataFrame.

    Parameters are optional so the default notebook path stays simple:
    ``diagnose(df)``.
    """

    options = DiagnoseOptions(
        name=name,
        previous=previous,
        baseline_schema=baseline_schema,
        key_columns=list(key_columns or []),
        critical_columns=list(critical_columns or []),
        cdc_order_column=cdc_order_column,
        sample_rows=sample_rows,
        show=show,
    )
    profile = _profile(df, options)
    previous_profile = _profile(previous, options) if previous is not None else None
    findings = _run_detectors(profile, previous_profile, options)
    report = DiagnosisReport(
        name=name,
        engine=profile.engine,
        findings=findings,
        metrics=_metrics(profile),
    )
    if show:
        report.print()
    return report


def diagnose_join(
    left: Any,
    right: Any,
    *,
    on: str | Iterable[str],
    name: str = "join",
    show: bool = True,
) -> DiagnosisReport:
    """Diagnose a potential join before running it at full scale."""

    keys = [on] if isinstance(on, str) else list(on)
    left_profile = profile_for_join(left, name="left", on=keys)
    right_profile = profile_for_join(right, name="right", on=keys)
    findings = detect_join_risk(left_profile, right_profile, on=keys)
    report = DiagnosisReport(
        name=name,
        engine=f"{left_profile.engine}+{right_profile.engine}",
        findings=findings,
        metrics={
            "join_keys": keys,
            "left_rows": left_profile.rows,
            "right_rows": right_profile.rows,
            "left_columns": left_profile.columns,
            "right_columns": right_profile.columns,
        },
    )
    if show:
        report.print()
    return report


def _profile(df: Any, options: DiagnoseOptions) -> DataProfile:
    engine = engine_name(df)
    if engine == "pandas":
        return profile_pandas(
            df,
            name=options.name,
            key_columns=options.key_columns,
            cdc_order_column=options.cdc_order_column,
        )
    if engine == "pyspark":
        from pipedoctor.adapters.spark import profile_spark

        return profile_spark(
            df,
            name=options.name,
            key_columns=options.key_columns,
            cdc_order_column=options.cdc_order_column,
            sample_rows=options.sample_rows,
        )
    raise TypeError(
        "PipeDoctor supports Pandas and PySpark DataFrames. "
        f"Got {type(df).__module__}.{type(df).__name__}."
    )


def _run_detectors(
    profile: DataProfile,
    previous_profile: DataProfile | None,
    options: DiagnoseOptions,
) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(
        detect_schema_drift(
            profile,
            previous=previous_profile,
            baseline_schema=options.baseline_schema,
        )
    )
    findings.extend(
        detect_nulls(
            profile,
            previous=previous_profile,
            critical_columns=options.critical_columns + options.key_columns,
        )
    )
    findings.extend(detect_duplicates(profile))
    findings.extend(detect_skew(profile))
    findings.extend(detect_distribution(profile))
    findings.extend(detect_partition_health(profile))
    findings.extend(detect_performance(profile))
    findings.extend(detect_cdc_health(profile, key_columns=options.key_columns))
    return findings


def _metrics(profile: DataProfile) -> dict[str, Any]:
    return {
        "rows_checked": profile.rows,
        "columns": profile.columns,
        "column_count": profile.column_count,
        "schema": profile.schema,
        "sampled": profile.sampled,
        "sample_rows": profile.sample_rows,
        "partitions": profile.partitions,
    }
