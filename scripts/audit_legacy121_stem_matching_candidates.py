#!/usr/bin/env python3
"""Audit candidate strict-stem relationships without assigning error labels."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from rna_ccfa.stems import Stem, extract_strict_stems


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RECORDS = 363
EXPECTED_MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")

VARIANTS = (
    "exact_only",
    "bilateral_at_least_1",
    "bilateral_at_least_2",
    "bilateral_2_and_half_shorter",
    "bilateral_all_but_one_shorter",
    "bilateral_full_shorter",
)
FINAL_CANDIDATE_FILTER = "bilateral_all_but_one_shorter"


class StemCandidateAuditError(RuntimeError):
    """A read-only stem candidate audit invariant failed."""


@dataclass(frozen=True, slots=True)
class CandidateMetrics:
    """Diagnostics for one GT-stem/predicted-stem pair."""

    exact_pair_overlap: int
    gt_pair_count: int
    pred_pair_count: int
    pair_union_size: int
    left_arm_overlap: int
    right_arm_overlap: int
    shorter_stem_pairs: int
    gt_register: int
    pred_register: int
    register_delta: int

    @property
    def minimum_arm_overlap(self) -> int:
        return min(self.left_arm_overlap, self.right_arm_overlap)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "normalized/legacy121_v1/predictions.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT
        / "results/error_analysis/stem_matching_candidate_audit.json",
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise StemCandidateAuditError(f"blank input line {line_number}")
            record = json.loads(line)
            if not isinstance(record, dict):
                raise StemCandidateAuditError(f"input line {line_number} is not an object")
            records.append(record)
    if len(records) != EXPECTED_RECORDS:
        raise StemCandidateAuditError(
            f"expected {EXPECTED_RECORDS} records, observed {len(records)}"
        )
    return records


def _arm_set(start: int, end: int) -> set[int]:
    return set(range(start, end + 1))


def candidate_metrics(gt: Stem, predicted: Stem) -> CandidateMetrics:
    """Compute exact-pair, arm-overlap, and register diagnostics."""

    gt_pairs = set(gt.pairs)
    pred_pairs = set(predicted.pairs)
    gt_left = _arm_set(gt.left_start, gt.left_end)
    pred_left = _arm_set(predicted.left_start, predicted.left_end)
    gt_right = _arm_set(gt.right_start, gt.right_end)
    pred_right = _arm_set(predicted.right_start, predicted.right_end)
    gt_register = sum(gt.outer_pair)
    pred_register = sum(predicted.outer_pair)
    return CandidateMetrics(
        exact_pair_overlap=len(gt_pairs & pred_pairs),
        gt_pair_count=gt.n_pairs,
        pred_pair_count=predicted.n_pairs,
        pair_union_size=len(gt_pairs | pred_pairs),
        left_arm_overlap=len(gt_left & pred_left),
        right_arm_overlap=len(gt_right & pred_right),
        shorter_stem_pairs=min(gt.n_pairs, predicted.n_pairs),
        gt_register=gt_register,
        pred_register=pred_register,
        register_delta=pred_register - gt_register,
    )


def potential_shift_evidence(metrics: CandidateMetrics, variant: str) -> bool:
    """Apply one audited no-exact-overlap bilateral-arm candidate rule."""

    if variant not in VARIANTS:
        raise ValueError(f"unknown candidate variant {variant!r}")
    if metrics.exact_pair_overlap != 0 or metrics.register_delta == 0:
        return False
    left = metrics.left_arm_overlap
    right = metrics.right_arm_overlap
    shorter = metrics.shorter_stem_pairs
    if variant == "exact_only":
        return False
    if variant == "bilateral_at_least_1":
        return left >= 1 and right >= 1
    if variant == "bilateral_at_least_2":
        return left >= 2 and right >= 2
    if variant == "bilateral_2_and_half_shorter":
        return (
            left >= 2
            and right >= 2
            and left * 2 >= shorter
            and right * 2 >= shorter
        )
    if variant == "bilateral_all_but_one_shorter":
        return (
            left >= 2
            and right >= 2
            and left >= shorter - 1
            and right >= shorter - 1
        )
    return left >= 2 and right >= 2 and left == shorter and right == shorter


def is_candidate(metrics: CandidateMetrics, variant: str) -> bool:
    """Whether one diagnostic edge enters the candidate graph."""

    return metrics.exact_pair_overlap > 0 or potential_shift_evidence(metrics, variant)


def _score_tuple(metrics: CandidateMetrics) -> tuple[int, int, int, int]:
    return (
        metrics.exact_pair_overlap,
        metrics.minimum_arm_overlap,
        1,
        -metrics.pair_union_size,
    )


def _scalar_weight(metrics: CandidateMetrics) -> int:
    """Encode the audited lexicographic assignment objective for comparison."""

    return (
        metrics.exact_pair_overlap * 1_000_000_000
        + metrics.minimum_arm_overlap * 1_000_000
        + 1_000
        - metrics.pair_union_size
    )


def _greedy_assignment(
    gt_stems: tuple[Stem, ...],
    pred_stems: tuple[Stem, ...],
    edges: list[tuple[int, int, CandidateMetrics]],
) -> set[tuple[int, int]]:
    matched_gt: set[int] = set()
    matched_pred: set[int] = set()
    selected: set[tuple[int, int]] = set()
    ordered = sorted(
        edges,
        key=lambda item: (
            -item[2].exact_pair_overlap,
            -item[2].minimum_arm_overlap,
            item[2].pair_union_size,
            gt_stems[item[0]].outer_pair,
            pred_stems[item[1]].outer_pair,
        ),
    )
    for gt_index, pred_index, _ in ordered:
        if gt_index in matched_gt or pred_index in matched_pred:
            continue
        matched_gt.add(gt_index)
        matched_pred.add(pred_index)
        selected.add((gt_index, pred_index))
    return selected


def _maximum_weight_assignment(
    n_gt: int,
    n_pred: int,
    edges: list[tuple[int, int, CandidateMetrics]],
) -> set[tuple[int, int]]:
    """Return a diagnostic global assignment while allowing unmatched stems."""

    size = n_gt + n_pred
    weights = np.zeros((size, size), dtype=np.int64)
    weights[:n_gt, :n_pred] = -1_000_000_000_000
    for gt_index, pred_index, metrics in edges:
        weights[gt_index, pred_index] = _scalar_weight(metrics)
    row_indices, column_indices = linear_sum_assignment(weights, maximize=True)
    return {
        (row, column)
        for row, column in zip(row_indices, column_indices)
        if row < n_gt and column < n_pred and weights[row, column] > 0
    }


def _ambiguous_component_counts(
    n_gt: int,
    n_pred: int,
    edges: list[tuple[int, int, CandidateMetrics]],
) -> tuple[int, set[int], set[int]]:
    gt_neighbors: defaultdict[int, set[int]] = defaultdict(set)
    pred_neighbors: defaultdict[int, set[int]] = defaultdict(set)
    for gt_index, pred_index, _ in edges:
        gt_neighbors[gt_index].add(pred_index)
        pred_neighbors[pred_index].add(gt_index)

    seen_gt: set[int] = set()
    seen_pred: set[int] = set()
    ambiguous_components = 0
    ambiguous_gt: set[int] = set()
    ambiguous_pred: set[int] = set()
    for start_gt in range(n_gt):
        if start_gt in seen_gt or start_gt not in gt_neighbors:
            continue
        component_gt: set[int] = set()
        component_pred: set[int] = set()
        queue: deque[tuple[str, int]] = deque([("gt", start_gt)])
        while queue:
            role, index = queue.popleft()
            if role == "gt":
                if index in seen_gt:
                    continue
                seen_gt.add(index)
                component_gt.add(index)
                queue.extend(("pred", item) for item in gt_neighbors[index])
            else:
                if index in seen_pred:
                    continue
                seen_pred.add(index)
                component_pred.add(index)
                queue.extend(("gt", item) for item in pred_neighbors[index])
        if len(component_gt) != 1 or len(component_pred) != 1:
            ambiguous_components += 1
            ambiguous_gt.update(component_gt)
            ambiguous_pred.update(component_pred)
    return ambiguous_components, ambiguous_gt, ambiguous_pred


def _edge_dict(
    record: dict[str, Any],
    gt_stem: Stem,
    pred_stem: Stem,
    metrics: CandidateMetrics,
    *,
    selected_globally: bool,
    isolated_one_to_one: bool,
) -> dict[str, Any]:
    return {
        "record_id": record["record_id"],
        "rna_id": record["rna_id"],
        "source_model": record["source_model"]["name"],
        "gt_outer_pair": list(gt_stem.outer_pair),
        "pred_outer_pair": list(pred_stem.outer_pair),
        **asdict(metrics),
        "selected_by_global_assignment": selected_globally,
        "isolated_one_to_one_candidate": isolated_one_to_one,
    }


def main() -> int:
    args = _parse_args()
    input_path = args.input.resolve()
    records = _load_records(input_path)
    normalized_sha = _sha256(input_path)

    variant_counts = {variant: Counter() for variant in VARIANTS}
    model_final_counts = {model: Counter() for model in EXPECTED_MODELS}
    assignment_counts: Counter[str] = Counter()
    greedy_global_differences: list[str] = []
    ambiguous_examples: list[dict[str, Any]] = []
    final_shift_candidates: list[dict[str, Any]] = []
    total_gt_stems = 0
    total_pred_stems = 0

    for record in records:
        model = record["source_model"]["name"]
        if model not in EXPECTED_MODELS:
            raise StemCandidateAuditError(f"unexpected source model {model!r}")
        sequence = record["sequence"]
        gt_stems = extract_strict_stems(
            record["ground_truth_structure"]["pairs"], sequence=sequence
        )
        pred_stems = extract_strict_stems(
            record["predicted_structure"]["pairs"], sequence=sequence
        )
        total_gt_stems += len(gt_stems)
        total_pred_stems += len(pred_stems)
        all_edges = [
            (gt_index, pred_index, candidate_metrics(gt_stem, pred_stem))
            for gt_index, gt_stem in enumerate(gt_stems)
            for pred_index, pred_stem in enumerate(pred_stems)
        ]

        final_edges: list[tuple[int, int, CandidateMetrics]] = []
        for variant in VARIANTS:
            edges = [edge for edge in all_edges if is_candidate(edge[2], variant)]
            gt_degree = Counter(gt_index for gt_index, _, _ in edges)
            pred_degree = Counter(pred_index for _, pred_index, _ in edges)
            counts = variant_counts[variant]
            counts["candidate_edges"] += len(edges)
            counts["exact_overlap_edges"] += sum(
                metrics.exact_pair_overlap > 0 for _, _, metrics in edges
            )
            counts["potential_shift_edges"] += sum(
                potential_shift_evidence(metrics, variant)
                for _, _, metrics in edges
            )
            counts["ambiguous_gt_stems"] += sum(value > 1 for value in gt_degree.values())
            counts["ambiguous_predicted_stems"] += sum(
                value > 1 for value in pred_degree.values()
            )
            counts["gt_stems_with_candidate"] += len(gt_degree)
            counts["predicted_stems_with_candidate"] += len(pred_degree)
            if variant == FINAL_CANDIDATE_FILTER:
                final_edges = edges

        gt_degree = Counter(gt_index for gt_index, _, _ in final_edges)
        pred_degree = Counter(pred_index for _, pred_index, _ in final_edges)
        greedy = _greedy_assignment(gt_stems, pred_stems, final_edges)
        global_assignment = _maximum_weight_assignment(
            len(gt_stems), len(pred_stems), final_edges
        )
        if greedy != global_assignment:
            greedy_global_differences.append(record["record_id"])
        assignment_counts["greedy_matches"] += len(greedy)
        assignment_counts["global_matches"] += len(global_assignment)

        ambiguous_components, complex_gt, complex_pred = _ambiguous_component_counts(
            len(gt_stems), len(pred_stems), final_edges
        )
        isolated_edges = [
            edge
            for edge in final_edges
            if gt_degree[edge[0]] == 1 and pred_degree[edge[1]] == 1
        ]
        counts = model_final_counts[model]
        counts["gt_stems"] += len(gt_stems)
        counts["predicted_stems"] += len(pred_stems)
        counts["candidate_edges"] += len(final_edges)
        counts["isolated_one_to_one_candidates"] += len(isolated_edges)
        counts["ambiguous_components"] += ambiguous_components
        counts["gt_stems_in_ambiguous_components"] += len(complex_gt)
        counts["predicted_stems_in_ambiguous_components"] += len(complex_pred)
        counts["zero_candidate_gt_stems"] += len(gt_stems) - len(gt_degree)
        counts["zero_candidate_predicted_stems"] += len(pred_stems) - len(pred_degree)

        for gt_index, pred_index, metrics in final_edges:
            isolated = gt_degree[gt_index] == 1 and pred_degree[pred_index] == 1
            if potential_shift_evidence(metrics, FINAL_CANDIDATE_FILTER):
                final_shift_candidates.append(
                    _edge_dict(
                        record,
                        gt_stems[gt_index],
                        pred_stems[pred_index],
                        metrics,
                        selected_globally=(gt_index, pred_index) in global_assignment,
                        isolated_one_to_one=isolated,
                    )
                )

        if ambiguous_components and len(ambiguous_examples) < 12:
            ambiguous_examples.append(
                {
                    "record_id": record["record_id"],
                    "rna_id": record["rna_id"],
                    "source_model": model,
                    "candidate_edges": [
                        _edge_dict(
                            record,
                            gt_stems[gt_index],
                            pred_stems[pred_index],
                            metrics,
                            selected_globally=(gt_index, pred_index)
                            in global_assignment,
                            isolated_one_to_one=False,
                        )
                        for gt_index, pred_index, metrics in final_edges
                        if gt_index in complex_gt or pred_index in complex_pred
                    ],
                }
            )

    overall_component_counts: Counter[str] = Counter()
    for counts in model_final_counts.values():
        overall_component_counts.update(counts)

    summary = {
        "dataset": "legacy121_v1",
        "audit_type": "candidate_diagnostics_only_no_final_stem_error_labels",
        "normalized_input_path": str(input_path),
        "normalized_input_sha256": normalized_sha,
        "records_audited": len(records),
        "repeated_gt_stem_instances_across_363_record_comparisons": total_gt_stems,
        "predicted_stem_instances": total_pred_stems,
        "candidate_variants": {
            variant: dict(sorted(counts.items()))
            for variant, counts in variant_counts.items()
        },
        "audited_final_candidate_filter": FINAL_CANDIDATE_FILTER,
        "assignment_comparison": {
            **dict(sorted(assignment_counts.items())),
            "greedy_vs_global_record_differences": len(greedy_global_differences),
            "differing_record_ids": greedy_global_differences,
            "global_objective": [
                "maximize total exact_pair_overlap",
                "maximize total minimum bilateral arm overlap",
                "maximize matched edge count",
                "minimize total pair_union_size",
            ],
        },
        "candidate_component_filter_diagnostics": {
            "overall": dict(sorted(overall_component_counts.items())),
            "by_model": {
                model: dict(sorted(model_final_counts[model].items()))
                for model in EXPECTED_MODELS
            },
        },
        "potential_shift_candidates": final_shift_candidates,
        "ambiguous_component_examples": ambiguous_examples,
        "final_error_labels_assigned": False,
    }
    if _sha256(input_path) != normalized_sha:
        raise StemCandidateAuditError("normalized input changed during read-only audit")

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
