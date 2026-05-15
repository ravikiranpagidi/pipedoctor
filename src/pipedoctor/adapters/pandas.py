"""Pandas profiling adapter."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipedoctor.models import DataProfile


def profile_pandas(
    df: Any,
    *,
    name: str,
    key_columns: Optional[List[str]] = None,
    cdc_order_column: Optional[str] = None,
) -> DataProfile:
    key_columns = key_columns or []
    row_count = int(len(df))
    columns = [str(col) for col in df.columns]
    schema = _schema(df)
    nulls = _nulls(df, row_count)
    duplicates = _duplicates(df, key_columns, row_count)
    cardinality = _cardinality(df)
    numeric = _numeric_profile(df)
    hot_values = _hot_values(df, key_columns, row_count)
    cdc = _cdc_profile(df, key_columns, cdc_order_column)
    return DataProfile(
        engine="pandas",
        name=name,
        rows=row_count,
        columns=columns,
        schema=schema,
        nulls=nulls,
        duplicates=duplicates,
        cardinality=cardinality,
        numeric=numeric,
        hot_values=hot_values,
        cdc=cdc,
        sampled=False,
        sample_rows=row_count,
    )


def _schema(df: Any) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for column in df.columns:
        series = df[column]
        result[str(column)] = {
            "type": str(series.dtype),
            "nullable": bool(series.isna().any()),
        }
    return result


def _nulls(df: Any, row_count: int) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for column in df.columns:
        count = int(df[column].isna().sum())
        pct = float(count / row_count) if row_count else 0.0
        result[str(column)] = {"count": count, "pct": pct}
    return result


def _duplicates(df: Any, key_columns: List[str], row_count: int) -> Dict[str, Any]:
    exact = int(df.duplicated().sum()) if row_count else 0
    result: Dict[str, Any] = {
        "exact_count": exact,
        "exact_pct": float(exact / row_count) if row_count else 0.0,
        "keys": {},
    }
    valid_keys = [key for key in key_columns if key in df.columns]
    if valid_keys:
        key_dup = int(df.duplicated(subset=valid_keys).sum())
        result["keys"][",".join(valid_keys)] = {
            "count": key_dup,
            "pct": float(key_dup / row_count) if row_count else 0.0,
        }
    return result


def _cardinality(df: Any) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for column in df.columns:
        try:
            result[str(column)] = int(df[column].nunique(dropna=True))
        except TypeError:
            result[str(column)] = int(df[column].astype(str).nunique(dropna=True))
    return result


def _numeric_profile(df: Any) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    numeric_df = df.select_dtypes(include=["number"])
    for column in numeric_df.columns:
        series = numeric_df[column].dropna()
        if series.empty:
            continue
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = int(((series < lower) | (series > upper)).sum()) if iqr else 0
        result[str(column)] = {
            "min": _to_float(series.min()),
            "max": _to_float(series.max()),
            "mean": _to_float(series.mean()),
            "q1": q1,
            "q3": q3,
            "outlier_count": outliers,
            "outlier_pct": float(outliers / len(series)) if len(series) else 0.0,
        }
    return result


def _hot_values(
    df: Any, key_columns: List[str], row_count: int
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    candidates = list(key_columns)
    for column, unique_count in _cardinality(df).items():
        if column not in candidates and 1 < unique_count <= 50:
            candidates.append(column)
    for column in candidates:
        if column not in df.columns or row_count == 0:
            continue
        counts = df[column].value_counts(dropna=False)
        if counts.empty:
            continue
        top_value = counts.index[0]
        top_count = int(counts.iloc[0])
        result[str(column)] = {
            "top_value": str(top_value),
            "top_count": top_count,
            "top_pct": float(top_count / row_count),
            "unique_count": int(df[column].nunique(dropna=True)),
        }
    return result


def _cdc_profile(
    df: Any, key_columns: List[str], cdc_order_column: Optional[str]
) -> Dict[str, Any]:
    valid_keys = [key for key in key_columns if key in df.columns]
    has_order = bool(cdc_order_column and cdc_order_column in df.columns)
    result: Dict[str, Any] = {
        "has_order_column": has_order,
        "order_column": cdc_order_column,
        "duplicate_events": 0,
        "late_events": 0,
    }
    if valid_keys and has_order:
        subset = valid_keys + [cdc_order_column]  # type: ignore[list-item]
        result["duplicate_events"] = int(df.duplicated(subset=subset).sum())
        sorted_df = df.sort_values(valid_keys + [cdc_order_column])
        for _, group in sorted_df.groupby(valid_keys, dropna=False):
            if group[cdc_order_column].is_monotonic_increasing is False:
                result["late_events"] += 1
    return result


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
