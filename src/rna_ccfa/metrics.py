"""Exact base-pair metrics for canonical RNA secondary structures.

Metrics use exact equality of zero-based canonical ``(i, j)`` pairs. Crossing
pairs require no special handling and are preserved as ordinary set members.

Empty-set convention
--------------------
* Empty ground truth and empty prediction are an exact match, so precision,
  recall, and F1 are all 1.0.
* Empty ground truth with a non-empty prediction has all three metrics 0.0.
* Non-empty ground truth with an empty prediction has all three metrics 0.0.

This convention avoids NaN and makes the only perfect empty case the one in
which both structures contain no pairs.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .structure import Pair, validate_pairs


@dataclass(frozen=True, slots=True)
class PairEvaluation:
    """Counts, exact pair partitions, and metrics for one RNA structure."""

    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    true_positive_pairs: tuple[Pair, ...]
    false_positive_pairs: tuple[Pair, ...]
    false_negative_pairs: tuple[Pair, ...]

    def as_dict(self, *, include_pairs: bool = False) -> dict[str, object]:
        """Return a machine-readable dictionary, optionally including pairs."""

        result: dict[str, object] = {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }
        if include_pairs:
            result.update(
                {
                    "true_positive_pairs": [list(pair) for pair in self.true_positive_pairs],
                    "false_positive_pairs": [list(pair) for pair in self.false_positive_pairs],
                    "false_negative_pairs": [list(pair) for pair in self.false_negative_pairs],
                }
            )
        return result


def _metric_values(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    if tp == 0 and fp == 0 and fn == 0:
        return 1.0, 1.0, 1.0

    precision_denominator = tp + fp
    recall_denominator = tp + fn
    f1_denominator = 2 * tp + fp + fn

    precision = tp / precision_denominator if precision_denominator else 0.0
    recall = tp / recall_denominator if recall_denominator else 0.0
    f1 = 2 * tp / f1_denominator if f1_denominator else 0.0
    return precision, recall, f1


def evaluate_pairs(
    prediction: Iterable[Sequence[int]],
    ground_truth: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    prediction_allow_multiple_partners: bool = False,
    ground_truth_allow_multiple_partners: bool = False,
) -> PairEvaluation:
    """Evaluate exact canonical base-pair agreement for one RNA.

    Both inputs pass through :func:`rna_ccfa.structure.validate_pairs`; the
    evaluator does not duplicate parsing or structural validation. Separate
    multiple-partner flags mirror the two structure objects in schema v1.
    """

    validation_coordinates = {
        "sequence": sequence,
        "sequence_length": sequence_length,
    }
    predicted_pairs = validate_pairs(
        prediction,
        allow_multiple_partners=prediction_allow_multiple_partners,
        **validation_coordinates,
    )
    ground_truth_pairs = validate_pairs(
        ground_truth,
        allow_multiple_partners=ground_truth_allow_multiple_partners,
        **validation_coordinates,
    )

    predicted_set = set(predicted_pairs)
    ground_truth_set = set(ground_truth_pairs)
    true_positive_pairs = tuple(sorted(predicted_set & ground_truth_set))
    false_positive_pairs = tuple(sorted(predicted_set - ground_truth_set))
    false_negative_pairs = tuple(sorted(ground_truth_set - predicted_set))

    tp = len(true_positive_pairs)
    fp = len(false_positive_pairs)
    fn = len(false_negative_pairs)
    precision, recall, f1 = _metric_values(tp, fp, fn)

    return PairEvaluation(
        tp=tp,
        fp=fp,
        fn=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        true_positive_pairs=true_positive_pairs,
        false_positive_pairs=false_positive_pairs,
        false_negative_pairs=false_negative_pairs,
    )
