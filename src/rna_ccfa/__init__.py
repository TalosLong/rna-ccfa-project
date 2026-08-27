"""RNA-CCFA shared infrastructure."""

from .aggregation import PairEvaluationSummary, aggregate_pair_evaluations
from .metrics import PairEvaluation, evaluate_pairs, metric_values_from_counts
from .structure import (
    Pair,
    StructureValidationError,
    parse_dense_matrix,
    parse_dot_bracket,
    parse_extended_dot_bracket,
    parse_pair_list,
    parse_standard_dot_bracket,
    parse_structure,
    validate_pairs,
)

__all__ = [
    "Pair",
    "PairEvaluation",
    "PairEvaluationSummary",
    "StructureValidationError",
    "aggregate_pair_evaluations",
    "evaluate_pairs",
    "metric_values_from_counts",
    "parse_dense_matrix",
    "parse_dot_bracket",
    "parse_extended_dot_bracket",
    "parse_pair_list",
    "parse_standard_dot_bracket",
    "parse_structure",
    "validate_pairs",
]
