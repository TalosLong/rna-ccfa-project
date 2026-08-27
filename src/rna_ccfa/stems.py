"""Deterministic strict stacked-stem extraction for canonical RNA pairs."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from statistics import mean, median

from .structure import Pair, validate_pairs

MINIMUM_STEM_PAIRS = 2


@dataclass(frozen=True, slots=True)
class Stem:
    """A maximal consecutive chain of directly stacked canonical pairs."""

    pairs: tuple[Pair, ...]
    n_pairs: int
    outer_pair: Pair
    inner_pair: Pair
    left_start: int
    left_end: int
    right_start: int
    right_end: int

    def __post_init__(self) -> None:
        if self.n_pairs < MINIMUM_STEM_PAIRS:
            raise ValueError("a strict stem must contain at least two pairs")
        if self.n_pairs != len(self.pairs):
            raise ValueError("n_pairs must equal the number of stem pairs")
        if not self.pairs:
            raise ValueError("a strict stem cannot be empty")
        if self.outer_pair != self.pairs[0] or self.inner_pair != self.pairs[-1]:
            raise ValueError("stem pairs must be ordered outermost to innermost")
        if self.left_start != self.outer_pair[0] or self.left_end != self.inner_pair[0]:
            raise ValueError("left bounds do not match the outer and inner pairs")
        if self.right_start != self.inner_pair[1] or self.right_end != self.outer_pair[1]:
            raise ValueError("right bounds do not match the inner and outer pairs")

    def as_dict(self) -> dict[str, object]:
        """Return canonical JSON-compatible stem fields."""

        return {
            "pairs": [list(pair) for pair in self.pairs],
            "n_pairs": self.n_pairs,
            "outer_pair": list(self.outer_pair),
            "inner_pair": list(self.inner_pair),
            "left_start": self.left_start,
            "left_end": self.left_end,
            "right_start": self.right_start,
            "right_end": self.right_end,
        }


@dataclass(frozen=True, slots=True)
class StemExtraction:
    """Strict stems, retained singleton pairs, and complete pair accounting."""

    stems: tuple[Stem, ...]
    singleton_pairs: tuple[Pair, ...]
    total_pair_count: int

    def __post_init__(self) -> None:
        stem_pair_count = sum(stem.n_pairs for stem in self.stems)
        if stem_pair_count + len(self.singleton_pairs) != self.total_pair_count:
            raise ValueError("strict stems and singleton pairs do not account for all pairs")


def _extract(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str | None,
    sequence_length: int | None,
    allow_multiple_partners: bool,
) -> StemExtraction:
    canonical = tuple(
        validate_pairs(
            pairs,
            sequence=sequence,
            sequence_length=sequence_length,
            allow_multiple_partners=allow_multiple_partners,
        )
    )
    pair_set = set(canonical)
    visited: set[Pair] = set()
    stems: list[Stem] = []
    singleton_pairs: list[Pair] = []

    for pair in canonical:
        if pair in visited:
            continue
        predecessor = (pair[0] - 1, pair[1] + 1)
        if predecessor in pair_set:
            continue

        chain: list[Pair] = []
        current = pair
        while current in pair_set and current not in visited:
            chain.append(current)
            visited.add(current)
            current = (current[0] + 1, current[1] - 1)

        if len(chain) >= MINIMUM_STEM_PAIRS:
            outer_pair = chain[0]
            inner_pair = chain[-1]
            stems.append(
                Stem(
                    pairs=tuple(chain),
                    n_pairs=len(chain),
                    outer_pair=outer_pair,
                    inner_pair=inner_pair,
                    left_start=outer_pair[0],
                    left_end=inner_pair[0],
                    right_start=inner_pair[1],
                    right_end=outer_pair[1],
                )
            )
        else:
            singleton_pairs.extend(chain)

    if visited != pair_set:
        raise RuntimeError("strict stem extraction failed to account for every pair")

    return StemExtraction(
        stems=tuple(sorted(stems, key=lambda stem: stem.outer_pair)),
        singleton_pairs=tuple(sorted(singleton_pairs)),
        total_pair_count=len(canonical),
    )


def extract_stems_and_singletons(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> StemExtraction:
    """Extract strict stems and singleton pairs with complete accounting."""

    return _extract(
        pairs,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=allow_multiple_partners,
    )


def extract_strict_stems(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> tuple[Stem, ...]:
    """Return maximal strict stacked stems, each containing at least two pairs."""

    return extract_stems_and_singletons(
        pairs,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=allow_multiple_partners,
    ).stems


def extract_singleton_pairs(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> tuple[Pair, ...]:
    """Return canonical pairs that have no directly stacked neighbor."""

    return extract_stems_and_singletons(
        pairs,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=allow_multiple_partners,
    ).singleton_pairs


def stem_lengths(extraction: StemExtraction) -> tuple[int, ...]:
    """Return sorted strict-stem lengths for descriptive aggregation."""

    return tuple(stem.n_pairs for stem in extraction.stems)


def summarize_stem_lengths(extractions: Iterable[StemExtraction]) -> dict[str, float | int]:
    """Aggregate descriptive stem lengths across structures.

    Mean and median are computed over all extracted strict stems, not over
    per-structure means. Empty groups use zero for all length summaries.
    """

    values = [length for extraction in extractions for length in stem_lengths(extraction)]
    if not values:
        return {"mean_stem_length": 0.0, "median_stem_length": 0.0, "max_stem_length": 0}
    return {
        "mean_stem_length": float(mean(values)),
        "median_stem_length": float(median(values)),
        "max_stem_length": max(values),
    }
