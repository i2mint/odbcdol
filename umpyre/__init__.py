"""Umpyre - Code analysis and quality metrics tracking."""

# Original python_code_stats exports
from umpyre.python_code_stats import (
    modules_info_gen,
    modules_info_df,
    modules_info_df_stats,
    stats_of,
    get_objs,
)

# New metrics tracking exports
from umpyre.config import Config
from umpyre.schema import MetricSchema
from umpyre.collectors import (
    MetricCollector,
    CollectorRegistry,
    registry,
    UmpyreCollector,
    WorkflowStatusCollector,
    WilyCollector,
    CoverageCollector,
)
from umpyre.storage import (
    GitBranchStorage,
    serialize_metrics,
    deserialize_metrics,
)

__all__ = [
    # Original exports
    "modules_info_gen",
    "modules_info_df",
    "modules_info_df_stats",
    "stats_of",
    "get_objs",
    # New exports
    "Config",
    "MetricSchema",
    "MetricCollector",
    "CollectorRegistry",
    "registry",
    "UmpyreCollector",
    "WorkflowStatusCollector",
    "WilyCollector",
    "CoverageCollector",
    "GitBranchStorage",
    "serialize_metrics",
    "deserialize_metrics",
]
