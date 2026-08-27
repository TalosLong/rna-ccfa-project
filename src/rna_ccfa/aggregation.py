"""Deterministic aggregation of exact canonical pair evaluations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from statistics import fmean, median, pstdev

from .metrics import PairEvaluation, metric_values_from_counts


@dataclass(frozen=True, slots=True)
class PairEvaluationSummary:
    """Macro, micro, and distribution summaries for a sample collection."""

    n_samples: int
    sum_tp: int
    sum_fp: int
    sum_fn: int
    macro_precision: float
    macro_recall: float
    macro_f1: float
    micro_precision: float
    micro_recall: float
    micro_f1: float
    median_f1: float
    std_f1: float
    min_f1: float
    max_f1: float

    def as_dict(self) -> dict[str, int | float]:
        """Return a machine-readable dictionary in field order."""

        return asdict(self)


def aggregate_pair_evaluations(
    evaluations: Iterable[PairEvaluation],
) -> PairEvaluationSummary:
    """Aggregate pair evaluations with arithmetic macro and count-first micro metrics.

    ``std_f1`` is the population standard deviation (``ddof=0``), because the
    supplied evaluations are the complete dataset being reported rather than a
    sample used to estimate an unseen population.
    """

    samples = tuple(evaluations)
    if not samples:
        raise ValueError("at least one pair evaluation is required")
    if any(not isinstance(sample, PairEvaluation) for sample in samples):
        raise TypeError("all evaluations must be PairEvaluation instances")

    sum_tp = sum(sample.tp for sample in samples)
    sum_fp = sum(sample.fp for sample in samples)
    sum_fn = sum(sample.fn for sample in samples)
    micro_precision, micro_recall, micro_f1 = metric_values_from_counts(
        sum_tp, sum_fp, sum_fn
    )
    f1_values = [sample.f1 for sample in samples]

    return PairEvaluationSummary(
        n_samples=len(samples),
        sum_tp=sum_tp,
        sum_fp=sum_fp,
        sum_fn=sum_fn,
        macro_precision=fmean(sample.precision for sample in samples),
        macro_recall=fmean(sample.recall for sample in samples),
        macro_f1=fmean(f1_values),
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
        median_f1=median(f1_values),
        std_f1=pstdev(f1_values),
        min_f1=min(f1_values),
        max_f1=max(f1_values),
    )
