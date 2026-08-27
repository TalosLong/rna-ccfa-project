"""Frozen Phase 2 deletion-only rule refinement baseline v1.

Rule triggers inspect only the sequence and one immutable snapshot of the
predicted canonical pair set. Ground truth is intentionally absent from this
module.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from .stems import MINIMUM_STEM_PAIRS, StemExtraction, extract_stems_and_singletons
from .structure import Pair, StructureValidationError, validate_pairs


R1_SINGLETON_DELETE = "R1_SINGLETON_DELETE"
R2_TWO_PAIR_STEM_DELETE = "R2_TWO_PAIR_STEM_DELETE"
R3_OUTER_NONCANONICAL_TRIM = "R3_OUTER_NONCANONICAL_TRIM"

WATSON_CRICK_WOBBLE_TYPES = frozenset({"AU", "UA", "GC", "CG", "GU", "UG"})

CONDITION_RULES: dict[str, tuple[str, ...]] = {
    "ORIGINAL": (),
    "R1": (R1_SINGLETON_DELETE,),
    "R2": (R2_TWO_PAIR_STEM_DELETE,),
    "R3": (R3_OUTER_NONCANONICAL_TRIM,),
    "R1_R2": (R1_SINGLETON_DELETE, R2_TWO_PAIR_STEM_DELETE),
    "R1_R3": (R1_SINGLETON_DELETE, R3_OUTER_NONCANONICAL_TRIM),
}
PREREGISTERED_CONDITIONS = tuple(CONDITION_RULES)


@dataclass(frozen=True, slots=True)
class IncompatiblePairConflict:
    """One nucleotide assigned to more than one distinct partner."""

    nucleotide: int
    partners: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DeletionTrigger:
    """One inference-time rule selecting one pair from the original snapshot."""

    rule_id: str
    deleted_pair: Pair
    observable_trigger_features: dict[str, Any]
    stem_id: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "deleted_pair": list(self.deleted_pair),
            "observable_trigger_features": self.observable_trigger_features,
            "stem_id": self.stem_id,
        }


@dataclass(frozen=True, slots=True)
class RefinementEdit:
    """A unique deletion with every rule trigger that selected it."""

    deleted_pair: Pair
    triggering_rule_ids: tuple[str, ...]
    triggers: tuple[DeletionTrigger, ...]


@dataclass(frozen=True, slots=True)
class RuleRefinementResult:
    """Validated output of one frozen deployable condition."""

    condition: str
    original_pairs: tuple[Pair, ...]
    refined_pairs: tuple[Pair, ...]
    original_extraction: StemExtraction
    edits: tuple[RefinementEdit, ...]

    @property
    def modified_pair_count(self) -> int:
        return len(self.edits)


def detect_incompatible_pair_conflicts(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
) -> tuple[IncompatiblePairConflict, ...]:
    """Return deterministic one-partner conflicts after basic pair validation.

    ``allow_multiple_partners=True`` is used only to inspect the matching
    constraint. Reversed, duplicate, self, and out-of-range pairs remain fatal.
    """

    canonical = validate_pairs(
        pairs,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=True,
    )
    partners: defaultdict[int, set[int]] = defaultdict(set)
    for i, j in canonical:
        partners[i].add(j)
        partners[j].add(i)
    return tuple(
        IncompatiblePairConflict(nucleotide=index, partners=tuple(sorted(values)))
        for index, values in sorted(partners.items())
        if len(values) > 1
    )


def validate_original_prediction(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str,
) -> tuple[Pair, ...]:
    """Validate a source prediction and reject rather than repair conflicts."""

    materialized = tuple(tuple(pair) for pair in pairs)
    conflicts = detect_incompatible_pair_conflicts(materialized, sequence=sequence)
    if conflicts:
        details = "; ".join(
            f"nucleotide {item.nucleotide} has partners {item.partners}"
            for item in conflicts
        )
        raise StructureValidationError(
            f"incompatible-pair conflict: {details}",
            code="multiple_partners",
        )
    return tuple(validate_pairs(materialized, sequence=sequence))


def _pair_type(sequence: str, pair: Pair) -> str:
    return sequence[pair[0]] + sequence[pair[1]]


def _stem_id(index: int) -> str:
    return f"stem_{index:04d}"


def collect_rule_triggers(
    *,
    sequence: str,
    extraction: StemExtraction,
    rule_ids: Iterable[str],
) -> tuple[DeletionTrigger, ...]:
    """Collect rule candidates from one already-frozen original extraction."""

    selected = tuple(rule_ids)
    unknown = sorted(set(selected) - {
        R1_SINGLETON_DELETE,
        R2_TWO_PAIR_STEM_DELETE,
        R3_OUTER_NONCANONICAL_TRIM,
    })
    if unknown:
        raise ValueError(f"unknown rule IDs: {unknown}")

    triggers: list[DeletionTrigger] = []
    if R1_SINGLETON_DELETE in selected:
        for pair in extraction.singleton_pairs:
            triggers.append(
                DeletionTrigger(
                    rule_id=R1_SINGLETON_DELETE,
                    deleted_pair=pair,
                    observable_trigger_features={
                        "original_snapshot": True,
                        "pair": list(pair),
                        "pair_type": _pair_type(sequence, pair),
                        "singleton_pair": True,
                    },
                    stem_id=None,
                )
            )

    for index, stem in enumerate(extraction.stems):
        stem_id = _stem_id(index)
        if R2_TWO_PAIR_STEM_DELETE in selected and stem.n_pairs == MINIMUM_STEM_PAIRS:
            for pair in stem.pairs:
                triggers.append(
                    DeletionTrigger(
                        rule_id=R2_TWO_PAIR_STEM_DELETE,
                        deleted_pair=pair,
                        observable_trigger_features={
                            "minimum_stem_pairs": MINIMUM_STEM_PAIRS,
                            "original_snapshot": True,
                            "pair": list(pair),
                            "stem_n_pairs": stem.n_pairs,
                            "stem_outer_pair": list(stem.outer_pair),
                        },
                        stem_id=stem_id,
                    )
                )

        if R3_OUTER_NONCANONICAL_TRIM in selected and stem.n_pairs >= 3:
            outer_pair = stem.outer_pair
            inward_pair = stem.pairs[1]
            outer_type = _pair_type(sequence, outer_pair)
            inward_type = _pair_type(sequence, inward_pair)
            if (
                outer_type not in WATSON_CRICK_WOBBLE_TYPES
                and inward_type in WATSON_CRICK_WOBBLE_TYPES
            ):
                triggers.append(
                    DeletionTrigger(
                        rule_id=R3_OUTER_NONCANONICAL_TRIM,
                        deleted_pair=outer_pair,
                        observable_trigger_features={
                            "boundary": "outer",
                            "immediate_inward_pair": list(inward_pair),
                            "immediate_inward_pair_type": inward_type,
                            "minimum_remaining_stem_pairs": MINIMUM_STEM_PAIRS,
                            "original_snapshot": True,
                            "outer_pair": list(outer_pair),
                            "outer_pair_type": outer_type,
                            "stem_n_pairs": stem.n_pairs,
                            "watson_crick_wobble_types": sorted(WATSON_CRICK_WOBBLE_TYPES),
                        },
                        stem_id=stem_id,
                    )
                )

    return tuple(
        sorted(
            triggers,
            key=lambda item: (item.deleted_pair, item.rule_id, item.stem_id or ""),
        )
    )


def merge_deletion_triggers(
    triggers: Iterable[DeletionTrigger],
) -> tuple[RefinementEdit, ...]:
    """Deduplicate pair deletions while retaining every deterministic trigger."""

    by_pair: defaultdict[Pair, list[DeletionTrigger]] = defaultdict(list)
    for trigger in triggers:
        if not isinstance(trigger, DeletionTrigger):
            raise TypeError("all triggers must be DeletionTrigger instances")
        by_pair[trigger.deleted_pair].append(trigger)

    edits: list[RefinementEdit] = []
    for pair in sorted(by_pair):
        pair_triggers = tuple(
            sorted(
                by_pair[pair],
                key=lambda item: (item.rule_id, item.stem_id or ""),
            )
        )
        edits.append(
            RefinementEdit(
                deleted_pair=pair,
                triggering_rule_ids=tuple(sorted({item.rule_id for item in pair_triggers})),
                triggers=pair_triggers,
            )
        )
    return tuple(edits)


def refine_prediction(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str,
    condition: str,
) -> RuleRefinementResult:
    """Apply one preregistered condition to an immutable source prediction."""

    if condition not in CONDITION_RULES:
        raise ValueError(
            f"condition {condition!r} is not preregistered; expected one of "
            f"{PREREGISTERED_CONDITIONS}"
        )

    original_pairs = validate_original_prediction(pairs, sequence=sequence)
    extraction = extract_stems_and_singletons(original_pairs, sequence=sequence)
    triggers = collect_rule_triggers(
        sequence=sequence,
        extraction=extraction,
        rule_ids=CONDITION_RULES[condition],
    )
    edits = merge_deletion_triggers(triggers)
    deleted_pairs = {edit.deleted_pair for edit in edits}
    refined_pairs = tuple(pair for pair in original_pairs if pair not in deleted_pairs)
    validated_refined = tuple(validate_pairs(refined_pairs, sequence=sequence))
    if validated_refined != refined_pairs:
        raise RuntimeError("post-edit validation changed canonical pair ordering")
    if len(original_pairs) - len(refined_pairs) != len(edits):
        raise RuntimeError("unique deletion accounting failed")

    return RuleRefinementResult(
        condition=condition,
        original_pairs=original_pairs,
        refined_pairs=refined_pairs,
        original_extraction=extraction,
        edits=edits,
    )
