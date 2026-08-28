"""Frozen v2.0.1 risk-controlled gate aggregation helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AbstainOutcome:
    beneficial_edits: int = 0
    harmful_edits: int = 0
    modified_pairs: int = 0
    modified_rnas: int = 0
    delete_recall: float = 0.0
    correct_pair_preservation: float = 1.0
    macro_delta_f1: float = 0.0
    micro_delta_f1: float = 0.0
    modification_precision: None = None


def event_modification_precision(beneficial: int, harmful: int) -> float | None:
    """Pool edit events; zero-edit collections have undefined precision."""

    if beneficial < 0 or harmful < 0:
        raise ValueError("edit counts must be nonnegative")
    total = beneficial + harmful
    return beneficial / total if total else None


def event_delete_recall(beneficial: int, original_false_positives: int) -> float:
    """Pool beneficial deletions over all original FP opportunities."""

    if beneficial < 0 or original_false_positives <= 0 or beneficial > original_false_positives:
        raise ValueError("invalid DELETE-recall counts")
    return beneficial / original_false_positives


def event_preservation(tp_after: int, tp_before: int) -> float:
    """Pool retained correct-pair events over all original TP opportunities."""

    if tp_before <= 0 or tp_after < 0 or tp_after > tp_before:
        raise ValueError("invalid preservation counts")
    return tp_after / tp_before


def precision_improvement_gate(
    cross_precision: float | None,
    base_precision: float | None,
    minimum_gain: float,
) -> str:
    """Return a binary gate; undefined precision never passes automatically."""

    if cross_precision is None or base_precision is None:
        return "FAIL"
    return "PASS" if cross_precision - base_precision >= minimum_gain else "FAIL"
