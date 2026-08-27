"""Deterministic pair-level RNA secondary-structure error extraction.

``missing_pair`` and ``false_positive_pair`` are the exact FN and FP
partitions returned by the shared evaluator. ``wrong_partner`` is a relational
annotation on an FP pair, never a third mutually exclusive metric partition.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .metrics import evaluate_pairs
from .structure import Pair


@dataclass(frozen=True, slots=True)
class EndpointConflict:
    """One nucleotide paired to different partners in prediction and GT."""

    endpoint: int
    predicted_partner: int
    ground_truth_partner: int

    def as_dict(self) -> dict[str, int]:
        """Return a machine-readable conflict representation."""

        return {
            "endpoint": self.endpoint,
            "predicted_partner": self.predicted_partner,
            "ground_truth_partner": self.ground_truth_partner,
        }


@dataclass(frozen=True, slots=True)
class WrongPartnerEvent:
    """An FP pair whose endpoint(s) have different GT partners."""

    predicted_pair: Pair
    wrong_partner_degree: int
    conflicting_endpoints: tuple[EndpointConflict, ...]
    linked_missing_pairs: tuple[Pair, ...]

    def __post_init__(self) -> None:
        if self.wrong_partner_degree not in (1, 2):
            raise ValueError("wrong_partner_degree must be 1 or 2")
        if len(self.conflicting_endpoints) != self.wrong_partner_degree:
            raise ValueError("wrong_partner_degree must equal the endpoint-conflict count")
        if len(self.linked_missing_pairs) != self.wrong_partner_degree:
            raise ValueError("each conflicting endpoint must link to one unique missing pair")

    def as_dict(self) -> dict[str, object]:
        """Return canonical JSON-compatible event fields."""

        return {
            "predicted_pair": list(self.predicted_pair),
            "wrong_partner_degree": self.wrong_partner_degree,
            "conflicting_endpoints": [
                conflict.as_dict() for conflict in self.conflicting_endpoints
            ],
            "linked_missing_pairs": [list(pair) for pair in self.linked_missing_pairs],
        }


@dataclass(frozen=True, slots=True)
class MissingPairAnnotation:
    """Reverse wrong-partner relation for one exact missing GT pair."""

    missing_pair: Pair
    wrong_partner_degree: int
    conflicting_endpoints: tuple[EndpointConflict, ...]
    linked_false_positive_pairs: tuple[Pair, ...]

    def __post_init__(self) -> None:
        if self.wrong_partner_degree not in (0, 1, 2):
            raise ValueError("missing-pair wrong_partner_degree must be 0, 1, or 2")
        if len(self.conflicting_endpoints) != self.wrong_partner_degree:
            raise ValueError("wrong_partner_degree must equal the endpoint-conflict count")
        if len(self.linked_false_positive_pairs) != self.wrong_partner_degree:
            raise ValueError("each conflicting endpoint must link to one unique FP pair")

    @property
    def wrong_partner(self) -> bool:
        """Whether either missing-pair endpoint has another predicted partner."""

        return self.wrong_partner_degree >= 1

    def as_dict(self) -> dict[str, object]:
        """Return canonical JSON-compatible reverse-relation fields."""

        return {
            "missing_pair": list(self.missing_pair),
            "wrong_partner": self.wrong_partner,
            "wrong_partner_degree": self.wrong_partner_degree,
            "conflicting_endpoints": [
                conflict.as_dict() for conflict in self.conflicting_endpoints
            ],
            "linked_false_positive_pairs": [
                list(pair) for pair in self.linked_false_positive_pairs
            ],
        }


@dataclass(frozen=True, slots=True)
class PairErrorExtraction:
    """Complete exact pair errors and wrong-partner relations for one record."""

    missing_pairs: tuple[Pair, ...]
    false_positive_pairs: tuple[Pair, ...]
    wrong_partner_events: tuple[WrongPartnerEvent, ...]
    missing_pair_annotations: tuple[MissingPairAnnotation, ...]


def _partner_map(pairs: Iterable[Pair]) -> dict[int, int]:
    partners: dict[int, int] = {}
    for i, j in pairs:
        partners[i] = j
        partners[j] = i
    return partners


def _canonical_pair(first: int, second: int) -> Pair:
    return (first, second) if first < second else (second, first)


def extract_pair_errors(
    prediction: Iterable[Sequence[int]],
    ground_truth: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
) -> PairErrorExtraction:
    """Extract exact FP/FN partitions and deterministic partner relations.

    Inputs are canonical pair iterables. The shared evaluator performs the
    canonical validation and exact set partitioning; this module only adds the
    relational endpoint annotations.
    """

    evaluation = evaluate_pairs(
        prediction,
        ground_truth,
        sequence=sequence,
        sequence_length=sequence_length,
    )
    missing_pairs = evaluation.false_negative_pairs
    false_positive_pairs = evaluation.false_positive_pairs
    missing_set = set(missing_pairs)
    false_positive_set = set(false_positive_pairs)
    ground_truth_partners = _partner_map(
        (*evaluation.true_positive_pairs, *missing_pairs)
    )
    predicted_partners = _partner_map(
        (*evaluation.true_positive_pairs, *false_positive_pairs)
    )

    wrong_partner_events: list[WrongPartnerEvent] = []
    for predicted_pair in false_positive_pairs:
        i, j = predicted_pair
        conflicts: list[EndpointConflict] = []
        linked_missing_pairs: set[Pair] = set()
        for endpoint, predicted_partner in ((i, j), (j, i)):
            ground_truth_partner = ground_truth_partners.get(endpoint)
            if ground_truth_partner is None or ground_truth_partner == predicted_partner:
                continue
            conflict = EndpointConflict(
                endpoint=endpoint,
                predicted_partner=predicted_partner,
                ground_truth_partner=ground_truth_partner,
            )
            linked_pair = _canonical_pair(endpoint, ground_truth_partner)
            if linked_pair not in missing_set:
                raise RuntimeError("wrong-partner event linked outside the FN partition")
            conflicts.append(conflict)
            linked_missing_pairs.add(linked_pair)

        if conflicts:
            wrong_partner_events.append(
                WrongPartnerEvent(
                    predicted_pair=predicted_pair,
                    wrong_partner_degree=len(conflicts),
                    conflicting_endpoints=tuple(
                        sorted(conflicts, key=lambda item: item.endpoint)
                    ),
                    linked_missing_pairs=tuple(sorted(linked_missing_pairs)),
                )
            )

    missing_annotations: list[MissingPairAnnotation] = []
    for missing_pair in missing_pairs:
        i, j = missing_pair
        conflicts = []
        linked_false_positive_pairs: set[Pair] = set()
        for endpoint, ground_truth_partner in ((i, j), (j, i)):
            predicted_partner = predicted_partners.get(endpoint)
            if predicted_partner is None or predicted_partner == ground_truth_partner:
                continue
            conflict = EndpointConflict(
                endpoint=endpoint,
                predicted_partner=predicted_partner,
                ground_truth_partner=ground_truth_partner,
            )
            linked_pair = _canonical_pair(endpoint, predicted_partner)
            if linked_pair not in false_positive_set:
                raise RuntimeError("missing-pair annotation linked outside the FP partition")
            conflicts.append(conflict)
            linked_false_positive_pairs.add(linked_pair)

        missing_annotations.append(
            MissingPairAnnotation(
                missing_pair=missing_pair,
                wrong_partner_degree=len(conflicts),
                conflicting_endpoints=tuple(
                    sorted(conflicts, key=lambda item: item.endpoint)
                ),
                linked_false_positive_pairs=tuple(sorted(linked_false_positive_pairs)),
            )
        )

    return PairErrorExtraction(
        missing_pairs=missing_pairs,
        false_positive_pairs=false_positive_pairs,
        wrong_partner_events=tuple(wrong_partner_events),
        missing_pair_annotations=tuple(missing_annotations),
    )


def extract_missing_pairs(
    prediction: Iterable[Sequence[int]],
    ground_truth: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
) -> tuple[Pair, ...]:
    """Return every exact FN GT pair in canonical order."""

    return extract_pair_errors(
        prediction,
        ground_truth,
        sequence=sequence,
        sequence_length=sequence_length,
    ).missing_pairs


def extract_false_positive_pairs(
    prediction: Iterable[Sequence[int]],
    ground_truth: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
) -> tuple[Pair, ...]:
    """Return every exact FP predicted pair in canonical order."""

    return extract_pair_errors(
        prediction,
        ground_truth,
        sequence=sequence,
        sequence_length=sequence_length,
    ).false_positive_pairs


def extract_wrong_partner_events(
    prediction: Iterable[Sequence[int]],
    ground_truth: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
) -> tuple[WrongPartnerEvent, ...]:
    """Return FP pairs with one or two different GT-partner endpoints."""

    return extract_pair_errors(
        prediction,
        ground_truth,
        sequence=sequence,
        sequence_length=sequence_length,
    ).wrong_partner_events


def annotate_missing_pairs(
    prediction: Iterable[Sequence[int]],
    ground_truth: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
) -> tuple[MissingPairAnnotation, ...]:
    """Return the reverse wrong-partner annotation for each exact FN pair."""

    return extract_pair_errors(
        prediction,
        ground_truth,
        sequence=sequence,
        sequence_length=sequence_length,
    ).missing_pair_annotations
