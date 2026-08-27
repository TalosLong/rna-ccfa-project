"""RNA-CCFA shared infrastructure."""

from .aggregation import PairEvaluationSummary, aggregate_pair_evaluations
from .errors import (
    EndpointConflict,
    MissingPairAnnotation,
    PairErrorExtraction,
    WrongPartnerEvent,
    annotate_missing_pairs,
    extract_false_positive_pairs,
    extract_missing_pairs,
    extract_pair_errors,
    extract_wrong_partner_events,
)
from .metrics import PairEvaluation, evaluate_pairs, metric_values_from_counts
from .stems import (
    MINIMUM_STEM_PAIRS,
    Stem,
    StemExtraction,
    extract_singleton_pairs,
    extract_stems_and_singletons,
    extract_strict_stems,
    summarize_stem_lengths,
)
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
    "EndpointConflict",
    "MissingPairAnnotation",
    "PairEvaluation",
    "PairErrorExtraction",
    "PairEvaluationSummary",
    "StructureValidationError",
    "WrongPartnerEvent",
    "aggregate_pair_evaluations",
    "annotate_missing_pairs",
    "evaluate_pairs",
    "extract_false_positive_pairs",
    "extract_missing_pairs",
    "extract_pair_errors",
    "extract_wrong_partner_events",
    "metric_values_from_counts",
    "MINIMUM_STEM_PAIRS",
    "Stem",
    "StemExtraction",
    "extract_singleton_pairs",
    "extract_stems_and_singletons",
    "extract_strict_stems",
    "summarize_stem_lengths",
    "parse_dense_matrix",
    "parse_dot_bracket",
    "parse_extended_dot_bracket",
    "parse_pair_list",
    "parse_standard_dot_bracket",
    "parse_structure",
    "validate_pairs",
]
