"""
Background jobs and maintenance tasks
"""

from backend.jobs.model_deprecation_checker import (
    ModelDeprecationChecker,
    check_model_deprecations,
    DeprecationReport,
    ModelCheckResult,
)

from backend.jobs.peer_evaluation import (
    PeerEvaluationJob,
    run_peer_evaluation,
)

from backend.jobs.stats_aggregation import (
    StatsAggregationJob,
    run_stats_aggregation,
)

__all__ = [
    # Model deprecation
    "ModelDeprecationChecker",
    "check_model_deprecations",
    "DeprecationReport",
    "ModelCheckResult",
    # Peer evaluation (v0.5.0)
    "PeerEvaluationJob",
    "run_peer_evaluation",
    # Stats aggregation (v0.5.0)
    "StatsAggregationJob",
    "run_stats_aggregation",
]
