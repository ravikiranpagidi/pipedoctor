"""Built-in diagnostic detectors."""

from pipedoctor.detectors.cdc import detect_cdc_health
from pipedoctor.detectors.distribution import detect_distribution
from pipedoctor.detectors.duplicates import detect_duplicates
from pipedoctor.detectors.execution import detect_execution
from pipedoctor.detectors.joins import detect_join_risk
from pipedoctor.detectors.nulls import detect_nulls
from pipedoctor.detectors.partitions import detect_partition_health
from pipedoctor.detectors.performance import detect_performance
from pipedoctor.detectors.schema import detect_schema_drift
from pipedoctor.detectors.skew import detect_skew

__all__ = [
    "detect_cdc_health",
    "detect_distribution",
    "detect_duplicates",
    "detect_execution",
    "detect_join_risk",
    "detect_nulls",
    "detect_partition_health",
    "detect_performance",
    "detect_schema_drift",
    "detect_skew",
]
