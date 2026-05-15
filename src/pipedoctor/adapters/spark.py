"""PySpark profiling adapter.

The Spark adapter is intentionally conservative. It inspects the plan and uses a
bounded sample for data-quality checks so ``diagnose(df)`` stays notebook-safe.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipedoctor.models import DataProfile


def profile_spark(
    df: Any,
    *,
    name: str,
    sample_rows: int,
    key_columns: Optional[List[str]] = None,
    cdc_order_column: Optional[str] = None,
) -> DataProfile:
    key_columns = key_columns or []
    columns = [str(col) for col in df.columns]
    schema = _schema(df)
    plan_text = _plan_text(df)
    partitions = _partitions(df)
    sample = df.limit(sample_rows)
    sampled_rows = _safe_count(sample)
    nulls = _nulls(sample, columns, sampled_rows)
    duplicates = _duplicates(sample, key_columns, sampled_rows)
    cardinality = _cardinality(sample, columns)
    numeric = _numeric_profile(sample)
    hot_values = _hot_values(sample, key_columns, cardinality, sampled_rows)
    cdc = _cdc_profile(sample, key_columns, cdc_order_column)
    return DataProfile(
        engine="pyspark",
        name=name,
        rows=sampled_rows,
        columns=columns,
        schema=schema,
        nulls=nulls,
        duplicates=duplicates,
        cardinality=cardinality,
        numeric=numeric,
        hot_values=hot_values,
        partitions=partitions,
        cdc=cdc,
        plan_text=plan_text,
        sampled=True,
        sample_rows=sample_rows,
    )


def _schema(df: Any) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for field in df.schema.fields:
        result[str(field.name)] = {
            "type": field.dataType.simpleString(),
            "nullable": bool(field.nullable),
        }
    return result


def _plan_text(df: Any) -> str:
    try:
        return df._jdf.queryExecution().executedPlan().toString()
    except Exception:
        try:
            return df._jdf.queryExecution().simpleString()
        except Exception:
            return ""


def _partitions(df: Any) -> Dict[str, Any]:
    try:
        return {"count": int(df.rdd.getNumPartitions())}
    except Exception as exc:
        return {"count": None, "error": str(exc)}


def _safe_count(df: Any) -> Optional[int]:
    try:
        return int(df.count())
    except Exception:
        return None


def _nulls(df: Any, columns: List[str], row_count: Optional[int]) -> Dict[str, Dict[str, Any]]:
    if row_count in (None, 0):
        return {column: {"count": None, "pct": None} for column in columns}
    try:
        from pyspark.sql import functions as F

        exprs = [
            F.sum(F.col(column).isNull().cast("int")).alias(column) for column in columns
        ]
        row = df.select(exprs).collect()[0].asDict()
        return {
            column: {
                "count": int(row.get(column) or 0),
                "pct": float((row.get(column) or 0) / row_count),
            }
            for column in columns
        }
    except Exception:
        return {column: {"count": None, "pct": None} for column in columns}


def _duplicates(df: Any, key_columns: List[str], row_count: Optional[int]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"exact_count": None, "exact_pct": None, "keys": {}}
    if row_count in (None, 0):
        return result
    try:
        unique_count = int(df.dropDuplicates().count())
        exact = max(0, row_count - unique_count)
        result["exact_count"] = exact
        result["exact_pct"] = float(exact / row_count)
    except Exception:
        pass
    valid_keys = [key for key in key_columns if key in df.columns]
    if valid_keys:
        try:
            unique_keys = int(df.dropDuplicates(valid_keys).count())
            key_dup = max(0, row_count - unique_keys)
            result["keys"][",".join(valid_keys)] = {
                "count": key_dup,
                "pct": float(key_dup / row_count),
            }
        except Exception:
            pass
    return result


def _cardinality(df: Any, columns: List[str]) -> Dict[str, int]:
    try:
        from pyspark.sql import functions as F

        exprs = [F.approx_count_distinct(column).alias(column) for column in columns]
        row = df.select(exprs).collect()[0].asDict()
        return {column: int(row.get(column) or 0) for column in columns}
    except Exception:
        return {}


def _numeric_profile(df: Any) -> Dict[str, Dict[str, Any]]:
    numeric_types = {
        "byte",
        "short",
        "int",
        "bigint",
        "float",
        "double",
        "decimal",
        "long",
    }
    numeric_columns = [
        field.name
        for field in df.schema.fields
        if field.dataType.simpleString().split("(")[0] in numeric_types
    ]
    if not numeric_columns:
        return {}
    try:
        summary = df.select(numeric_columns).summary("min", "max", "mean").collect()
        rows = {row["summary"]: row.asDict() for row in summary}
        result: Dict[str, Dict[str, Any]] = {}
        for column in numeric_columns:
            result[column] = {
                "min": _to_float(rows.get("min", {}).get(column)),
                "max": _to_float(rows.get("max", {}).get(column)),
                "mean": _to_float(rows.get("mean", {}).get(column)),
                "outlier_count": None,
                "outlier_pct": None,
            }
        return result
    except Exception:
        return {}


def _hot_values(
    df: Any, key_columns: List[str], cardinality: Dict[str, int], row_count: Optional[int]
) -> Dict[str, Dict[str, Any]]:
    if row_count in (None, 0):
        return {}
    candidates = list(key_columns)
    for column, unique_count in cardinality.items():
        if column not in candidates and 1 < unique_count <= 50:
            candidates.append(column)
    result: Dict[str, Dict[str, Any]] = {}
    for column in candidates:
        if column not in df.columns:
            continue
        try:
            top = df.groupBy(column).count().orderBy("count", ascending=False).limit(1).collect()
            if top:
                row = top[0]
                count = int(row["count"])
                result[column] = {
                    "top_value": str(row[column]),
                    "top_count": count,
                    "top_pct": float(count / row_count),
                    "unique_count": cardinality.get(column),
                }
        except Exception:
            continue
    return result


def _cdc_profile(
    df: Any, key_columns: List[str], cdc_order_column: Optional[str]
) -> Dict[str, Any]:
    valid_keys = [key for key in key_columns if key in df.columns]
    has_order = bool(cdc_order_column and cdc_order_column in df.columns)
    result: Dict[str, Any] = {
        "has_order_column": has_order,
        "order_column": cdc_order_column,
        "duplicate_events": None,
        "late_events": None,
    }
    if valid_keys and has_order:
        try:
            total = int(df.count())
            unique = int(df.dropDuplicates(valid_keys + [cdc_order_column]).count())
            result["duplicate_events"] = max(0, total - unique)
        except Exception:
            pass
    return result


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
