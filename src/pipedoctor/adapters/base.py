"""Adapter selection helpers."""

from __future__ import annotations

from typing import Any


def engine_name(obj: Any) -> str:
    module = type(obj).__module__
    name = type(obj).__name__
    if module.startswith("pandas.") and name == "DataFrame":
        return "pandas"
    if module.startswith("pyspark.") and name == "DataFrame":
        return "pyspark"
    return "unknown"


def is_pandas_dataframe(obj: Any) -> bool:
    return engine_name(obj) == "pandas"


def is_spark_dataframe(obj: Any) -> bool:
    return engine_name(obj) == "pyspark"
