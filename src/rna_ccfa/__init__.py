"""RNA-CCFA shared infrastructure."""

from .metrics import PairEvaluation, evaluate_pairs
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
    "StructureValidationError",
    "evaluate_pairs",
    "parse_dense_matrix",
    "parse_dot_bracket",
    "parse_extended_dot_bracket",
    "parse_pair_list",
    "parse_standard_dot_bracket",
    "parse_structure",
    "validate_pairs",
]
