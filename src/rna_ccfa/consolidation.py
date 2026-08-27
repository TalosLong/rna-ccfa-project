"""Helpers for deterministic, unit-aware Phase 1 error consolidation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class RankedPattern:
    """One pattern measured against an explicit analysis unit and denominator."""

    name: str
    count: int
    rate: float
    analysis_unit: str
    denominator_name: str


def require_fields(row: Mapping[str, object], fields: Sequence[str]) -> None:
    """Reject absent or implicit missing values in an input summary row."""

    missing = [field for field in fields if field not in row or row[field] in (None, "")]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")


def rate(numerator: int, denominator: int) -> float:
    """Return a bounded descriptive rate with an explicit positive denominator."""

    if isinstance(numerator, bool) or isinstance(denominator, bool):
        raise TypeError("rate counts must be integers")
    if not isinstance(numerator, int) or not isinstance(denominator, int):
        raise TypeError("rate counts must be integers")
    if denominator <= 0 or numerator < 0 or numerator > denominator:
        raise ValueError("rate requires 0 <= numerator <= positive denominator")
    return numerator / denominator


def rank_same_unit(patterns: Sequence[RankedPattern]) -> tuple[RankedPattern, ...]:
    """Rank patterns only when their unit and denominator are identical.

    Equal rates are resolved by pattern name, making output independent of input
    order. Raw counts from distinct analysis units cannot enter this function.
    """

    if not patterns:
        return ()
    units = {pattern.analysis_unit for pattern in patterns}
    denominators = {pattern.denominator_name for pattern in patterns}
    if len(units) != 1 or len(denominators) != 1:
        raise ValueError("cannot rank patterns across analysis units or denominators")
    for pattern in patterns:
        if pattern.count < 0 or not 0 <= pattern.rate <= 1:
            raise ValueError("invalid pattern count or rate")
    return tuple(sorted(patterns, key=lambda item: (-item.rate, item.name)))


def relative_consistency(rates: Sequence[float]) -> str:
    """Return a transparent descriptive spread label, not statistical confidence."""

    if len(rates) < 2 or any(not 0 <= value <= 1 for value in rates):
        raise ValueError("relative consistency requires at least two bounded rates")
    low, high = min(rates), max(rates)
    if high == 0:
        return "ABSENT"
    if low == 0:
        return "SOURCE_MODEL_SKEWED"
    ratio = high / low
    if ratio <= 1.25:
        return "SIMILAR"
    if ratio <= 1.75:
        return "MODERATELY_VARIABLE"
    return "SOURCE_MODEL_SKEWED"
