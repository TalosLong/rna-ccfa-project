"""Pair sequence-separation calculations and frozen Legacy121 v1 bins."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .structure import Pair


# GT-only relative-separation quantiles (NumPy linear method), frozen for
# Legacy121 v1. Values at a boundary belong to the lower bin.
LEGACY121_RELATIVE_THRESHOLDS = (
    0.25,
    0.5142857142857142,
    0.8,
    0.9333333333333333,
)

LEGACY121_SEPARATION_BINS = (
    "relative_q00_q25",
    "relative_q25_q50",
    "relative_q50_q75",
    "relative_q75_q90",
    "relative_q90_q100_long_range",
)


@dataclass(frozen=True, slots=True)
class PairSeparation:
    """Raw and length-normalized separation of one canonical pair."""

    sequence_separation: int
    relative_separation: float


def pair_separation(pair: Pair, sequence_length: int) -> PairSeparation:
    """Return ``j-i`` and ``(j-i)/(L-1)`` for a canonical pair."""

    i, j = pair
    if sequence_length <= 1:
        raise ValueError("paired structures require sequence_length > 1")
    if i < 0 or i >= j or j >= sequence_length:
        raise ValueError(f"pair {pair} is not canonical for length {sequence_length}")
    raw = j - i
    relative = raw / (sequence_length - 1)
    if raw <= 0 or not isfinite(relative) or not 0 < relative <= 1:
        raise ValueError("invalid pair separation")
    return PairSeparation(raw, relative)


def assign_legacy121_separation_bin(relative_separation: float) -> str:
    """Assign a relative separation to the frozen Legacy121 v1 binning."""

    if not isfinite(relative_separation) or not 0 < relative_separation <= 1:
        raise ValueError("relative_separation must be finite and in (0, 1]")
    for threshold, label in zip(
        LEGACY121_RELATIVE_THRESHOLDS,
        LEGACY121_SEPARATION_BINS,
    ):
        if relative_separation <= threshold:
            return label
    return LEGACY121_SEPARATION_BINS[-1]
