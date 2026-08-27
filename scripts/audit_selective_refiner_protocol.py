#!/usr/bin/env python3
"""Generate frozen-data label balance and split-feasibility audit tables."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from Bio import Align

from rna_ccfa.metrics import evaluate_pairs
from rna_ccfa.stems import extract_stems_and_singletons
from rna_ccfa.structure import Pair, validate_pairs


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "normalized/legacy121_v1/predictions.jsonl"
OUTPUT = ROOT / "results/selective_refiner_protocol"
EXTERNAL_MANIFEST = Path(
    "/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1/data/"
    "NMRFOLD_external77_fullatom_3SS_v3/"
    "NMRFOLD_external77_fullatom_3SS_manifest.csv"
)
CASP18_MANIFEST = Path(
    "/root/autodl-tmp/data/TS87/GT-CIF/casp_fullatom_v2/"
    "casp_fullatom_v2_CODEX/casp_fullatom_v2_manifest.csv"
)
TS85_HOLDOUT_FASTA = Path("/root/autodl-tmp/data/TS87/Fasta/holdout")
MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")
IDENTITY_THRESHOLD = 0.80

LABEL_FIELDS = (
    "dataset",
    "source_model",
    "n_rnas",
    "total_predicted_pairs",
    "keep_count",
    "delete_count",
    "keep_fraction",
    "delete_fraction",
    "delete_to_keep_ratio",
    "rnas_with_delete",
    "fraction_rnas_with_delete",
)
FEATURE_FIELDS = (
    "dataset",
    "source_model",
    "feature_group_dimension",
    "feature_group_value",
    "predicted_pair_count",
    "keep_count",
    "delete_count",
    "keep_fraction",
    "delete_fraction",
    "n_rnas_represented",
    "n_rnas_with_delete",
)
SPLIT_FIELDS = (
    "dataset_candidate",
    "local_root",
    "observed_rnas",
    "sequences_ready_for_identity_audit",
    "explicit_2d_gt_records",
    "normalized_prediction_records_in_repo",
    "complete_three_model_prediction_matrix",
    "prior_project_use",
    "exact_sequence_matches_to_legacy121",
    "sequences_at_or_above_0_80_identity_to_legacy121",
    "nonredundant_acgu_candidates",
    "identity_audit_scope",
    "proposed_role",
    "independent_test_ready",
    "blockers",
    "required_next_action",
)
EXTERNAL_FIELDS = (
    "sequence_id",
    "length",
    "contains_ambiguous_n",
    "max_global_identity_to_legacy121",
    "nearest_legacy_rna_id",
    "exact_legacy_sequence_match",
    "at_or_above_0_80_identity",
    "eligible_external77_gt_con_v1_candidate",
    "exclusion_reason",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _load_records() -> list[dict[str, Any]]:
    records = [json.loads(line) for line in INPUT.read_text().splitlines() if line.strip()]
    if len(records) != 363:
        raise RuntimeError(f"expected 363 normalized records, observed {len(records)}")
    if Counter(record["source_model"]["name"] for record in records) != Counter(
        {model: 121 for model in MODELS}
    ):
        raise RuntimeError("unexpected Legacy121 source-model coverage")
    return records


def _pair_class(pair_type: str) -> str:
    if pair_type in {"AU", "UA", "GC", "CG"}:
        return "watson_crick"
    if pair_type in {"GU", "UG"}:
        return "wobble"
    return "other"


def _pair_feature_groups(
    pairs: tuple[Pair, ...], sequence: str
) -> dict[Pair, dict[str, str]]:
    extraction = extract_stems_and_singletons(pairs, sequence=sequence)
    groups: dict[Pair, dict[str, str]] = {}
    for pair in extraction.singleton_pairs:
        pair_type = sequence[pair[0]] + sequence[pair[1]]
        groups[pair] = {
            "structural_unit": "singleton",
            "stem_length": "not_in_stem",
            "stem_position": "singleton",
            "pair_class": _pair_class(pair_type),
            "pair_type": pair_type,
        }
    for stem in extraction.stems:
        if stem.n_pairs == 2:
            length_group = "length_2"
        elif stem.n_pairs == 3:
            length_group = "length_3"
        else:
            length_group = "length_4_plus"
        for position, pair in enumerate(stem.pairs):
            if position == 0:
                stem_position = "outer_boundary"
            elif position == stem.n_pairs - 1:
                stem_position = "inner_boundary"
            else:
                stem_position = "interior"
            pair_type = sequence[pair[0]] + sequence[pair[1]]
            groups[pair] = {
                "structural_unit": "strict_stem",
                "stem_length": length_group,
                "stem_position": stem_position,
                "pair_class": _pair_class(pair_type),
                "pair_type": pair_type,
            }
    if set(groups) != set(pairs):
        raise RuntimeError("feature groups do not account for every predicted pair")
    return groups


def _label_entries(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: item["record_id"]):
        sequence = record["sequence"]
        predicted = tuple(
            validate_pairs(record["predicted_structure"]["pairs"], sequence=sequence)
        )
        ground_truth = tuple(
            validate_pairs(record["ground_truth_structure"]["pairs"], sequence=sequence)
        )
        evaluation = evaluate_pairs(predicted, ground_truth, sequence=sequence)
        keep = set(evaluation.true_positive_pairs)
        delete = set(evaluation.false_positive_pairs)
        if keep | delete != set(predicted) or keep & delete:
            raise RuntimeError(f"label partition failed for {record['record_id']}")
        groups = _pair_feature_groups(predicted, sequence)
        for pair in predicted:
            entries.append(
                {
                    "record_id": record["record_id"],
                    "rna_id": record["rna_id"],
                    "source_model": record["source_model"]["name"],
                    "pair": pair,
                    "label": "KEEP" if pair in keep else "DELETE",
                    "groups": groups[pair],
                }
            )
    return entries


def _label_balance(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in (*MODELS, "ALL"):
        group = entries if model == "ALL" else [e for e in entries if e["source_model"] == model]
        counts = Counter(e["label"] for e in group)
        rnas = {e["rna_id"] for e in group}
        rnas_with_delete = {e["rna_id"] for e in group if e["label"] == "DELETE"}
        total = len(group)
        rows.append(
            {
                "dataset": "Legacy121_v1",
                "source_model": model,
                "n_rnas": len(rnas),
                "total_predicted_pairs": total,
                "keep_count": counts["KEEP"],
                "delete_count": counts["DELETE"],
                "keep_fraction": counts["KEEP"] / total,
                "delete_fraction": counts["DELETE"] / total,
                "delete_to_keep_ratio": counts["DELETE"] / counts["KEEP"],
                "rnas_with_delete": len(rnas_with_delete),
                "fraction_rnas_with_delete": len(rnas_with_delete) / len(rnas),
            }
        )
    expected = {
        "rnafold": (1693, 1473, 220),
        "petfold": (1704, 1463, 241),
        "trrosettarna2_native_ss": (1893, 1461, 432),
        "ALL": (5290, 4397, 893),
    }
    for row in rows:
        observed = (
            row["total_predicted_pairs"],
            row["keep_count"],
            row["delete_count"],
        )
        if observed != expected[row["source_model"]]:
            raise RuntimeError(
                f"frozen label regression failed for {row['source_model']}: {observed}"
            )
    return rows


def _feature_balance(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    dimensions = ("structural_unit", "stem_length", "stem_position", "pair_class", "pair_type")
    for model in (*MODELS, "ALL"):
        model_entries = (
            entries if model == "ALL" else [e for e in entries if e["source_model"] == model]
        )
        for dimension in dimensions:
            values = sorted({e["groups"][dimension] for e in model_entries})
            accounted = 0
            for value in values:
                group = [e for e in model_entries if e["groups"][dimension] == value]
                counts = Counter(e["label"] for e in group)
                rnas = {e["rna_id"] for e in group}
                rnas_with_delete = {e["rna_id"] for e in group if e["label"] == "DELETE"}
                total = len(group)
                accounted += total
                rows.append(
                    {
                        "dataset": "Legacy121_v1",
                        "source_model": model,
                        "feature_group_dimension": dimension,
                        "feature_group_value": value,
                        "predicted_pair_count": total,
                        "keep_count": counts["KEEP"],
                        "delete_count": counts["DELETE"],
                        "keep_fraction": counts["KEEP"] / total,
                        "delete_fraction": counts["DELETE"] / total,
                        "n_rnas_represented": len(rnas),
                        "n_rnas_with_delete": len(rnas_with_delete),
                    }
                )
            if accounted != len(model_entries):
                raise RuntimeError(f"{model}/{dimension}: subgroup accounting failed")
    return rows


def _global_identity_aligner() -> Align.PairwiseAligner:
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 1.0
    aligner.mismatch_score = 0.0
    aligner.open_gap_score = -1.0
    aligner.extend_gap_score = -1.0
    return aligner


def _global_identity(aligner: Align.PairwiseAligner, first: str, second: str) -> float:
    counts = aligner.align(first, second)[0].counts()
    denominator = counts.identities + counts.mismatches + counts.gaps
    if denominator == 0:
        raise RuntimeError("cannot calculate identity for two empty sequences")
    return counts.identities / denominator


def _nearest_legacy(
    aligner: Align.PairwiseAligner,
    sequence: str,
    legacy_sequences: dict[str, str],
) -> tuple[float, str]:
    scored = [
        (_global_identity(aligner, sequence, legacy_sequence), rna_id)
        for rna_id, legacy_sequence in sorted(legacy_sequences.items())
    ]
    best_identity = max(score for score, _ in scored)
    best_id = min(rna_id for score, rna_id in scored if score == best_identity)
    return best_identity, best_id


def _external_candidates(
    legacy_sequences: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    manifest = _read_csv(EXTERNAL_MANIFEST)
    if len(manifest) != 77:
        raise RuntimeError("external77 manifest count changed")
    aligner = _global_identity_aligner()
    rows: list[dict[str, Any]] = []
    for record in sorted(manifest, key=lambda item: item["sequence_id"]):
        sequence = record["sequence"]
        identity, nearest = _nearest_legacy(aligner, sequence, legacy_sequences)
        ambiguous = "N" in sequence
        redundant = identity >= IDENTITY_THRESHOLD
        eligible = not ambiguous and not redundant
        if ambiguous:
            reason = "contains_N"
        elif redundant:
            reason = "global_identity_to_Legacy121_ge_0.80"
        else:
            reason = ""
        rows.append(
            {
                "sequence_id": record["sequence_id"],
                "length": len(sequence),
                "contains_ambiguous_n": ambiguous,
                "max_global_identity_to_legacy121": identity,
                "nearest_legacy_rna_id": nearest,
                "exact_legacy_sequence_match": identity == 1.0,
                "at_or_above_0_80_identity": redundant,
                "eligible_external77_gt_con_v1_candidate": eligible,
                "exclusion_reason": reason,
            }
        )
    if sum(row["exact_legacy_sequence_match"] for row in rows) != 30:
        raise RuntimeError("external77 exact-overlap regression changed")
    if sum(row["at_or_above_0_80_identity"] for row in rows if not row["contains_ambiguous_n"]) != 31:
        raise RuntimeError("external77 identity-overlap regression changed")
    if sum(row["eligible_external77_gt_con_v1_candidate"] for row in rows) != 42:
        raise RuntimeError("external77 independent-candidate count changed")
    return rows, manifest


def _read_fasta(path: Path) -> str:
    return "".join(
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith(">")
    )


def _dataset_inventory(
    legacy_sequences: dict[str, str],
    external_rows: list[dict[str, Any]],
    external_manifest: list[dict[str, str]],
) -> list[dict[str, Any]]:
    aligner = _global_identity_aligner()
    casp_manifest = _read_csv(CASP18_MANIFEST)
    casp_sequences = [row["entity_sequence"] for row in casp_manifest if row["entity_sequence"]]
    casp_identities = [
        _nearest_legacy(aligner, sequence, legacy_sequences)[0]
        for sequence in casp_sequences
    ]
    holdout_sequences = {
        path.stem: _read_fasta(path) for path in sorted(TS85_HOLDOUT_FASTA.glob("*.fasta"))
    }
    legacy_values = set(legacy_sequences.values())
    holdout_exact = sum(sequence in legacy_values for sequence in holdout_sequences.values())
    external_exact = sum(row["exact_legacy_sequence_match"] for row in external_rows)
    external_ge80 = sum(
        row["at_or_above_0_80_identity"]
        for row in external_rows
        if not row["contains_ambiguous_n"]
    )
    external_eligible = sum(
        row["eligible_external77_gt_con_v1_candidate"] for row in external_rows
    )
    if len(casp_manifest) != 18 or len(casp_sequences) != 15:
        raise RuntimeError("CASP18 sequence audit regression changed")
    if len(holdout_sequences) != 67 or holdout_exact != 31:
        raise RuntimeError("TS85 holdout overlap regression changed")

    return [
        {
            "dataset_candidate": "Legacy121_v1",
            "local_root": str(INPUT.parent),
            "observed_rnas": 121,
            "sequences_ready_for_identity_audit": 121,
            "explicit_2d_gt_records": 121,
            "normalized_prediction_records_in_repo": 363,
            "complete_three_model_prediction_matrix": True,
            "prior_project_use": "Phase1 exploration and Phase2 rule selection/evaluation",
            "exact_sequence_matches_to_legacy121": 121,
            "sequences_at_or_above_0_80_identity_to_legacy121": 121,
            "nonredundant_acgu_candidates": 0,
            "identity_audit_scope": "self-reference",
            "proposed_role": "development and grouped internal CV only",
            "independent_test_ready": False,
            "blockers": "already used for exploratory analysis and rule selection",
            "required_next_action": "cluster into development folds; never relabel as final held-out test",
        },
        {
            "dataset_candidate": "external77_full_inventory",
            "local_root": str(EXTERNAL_MANIFEST.parent.parent.parent),
            "observed_rnas": len(external_manifest),
            "sequences_ready_for_identity_audit": len(external_manifest),
            "explicit_2d_gt_records": 77,
            "normalized_prediction_records_in_repo": 0,
            "complete_three_model_prediction_matrix": False,
            "prior_project_use": "inventory and downstream 3D assets only",
            "exact_sequence_matches_to_legacy121": external_exact,
            "sequences_at_or_above_0_80_identity_to_legacy121": external_ge80,
            "nonredundant_acgu_candidates": external_eligible,
            "identity_audit_scope": "73 ACGU-only sequences for >=0.80 count; all 77 for exact count",
            "proposed_role": "source pool for independent external77_GT_CON_v1 test",
            "independent_test_ready": False,
            "blockers": "GT target not frozen; 4 N sequences; 30 exact overlaps; no complete source predictions",
            "required_next_action": "select GT_CON; exclude N and >=0.80 Legacy clusters; run/freeze three predictors; normalize",
        },
        {
            "dataset_candidate": "external77_GT_CON_v1_nonredundant_candidate",
            "local_root": str(EXTERNAL_MANIFEST.parent),
            "observed_rnas": external_eligible,
            "sequences_ready_for_identity_audit": external_eligible,
            "explicit_2d_gt_records": external_eligible,
            "normalized_prediction_records_in_repo": 0,
            "complete_three_model_prediction_matrix": False,
            "prior_project_use": "not yet evaluated as a refiner dataset",
            "exact_sequence_matches_to_legacy121": 0,
            "sequences_at_or_above_0_80_identity_to_legacy121": 0,
            "nonredundant_acgu_candidates": external_eligible,
            "identity_audit_scope": "global identity screen against all 121 Legacy sequences",
            "proposed_role": "primary independent test candidate; test-only after freeze",
            "independent_test_ready": False,
            "blockers": "candidate manifest and GT_CON semantics not frozen; no three-model normalized predictions",
            "required_next_action": "freeze 42-row manifest before inference, generate three source predictions, normalize without inspection",
        },
        {
            "dataset_candidate": "TS85_CASP18",
            "local_root": str(CASP18_MANIFEST.parent),
            "observed_rnas": 18,
            "sequences_ready_for_identity_audit": len(casp_sequences),
            "explicit_2d_gt_records": 18,
            "normalized_prediction_records_in_repo": 0,
            "complete_three_model_prediction_matrix": False,
            "prior_project_use": "3D benchmark working set only",
            "exact_sequence_matches_to_legacy121": sum(identity == 1.0 for identity in casp_identities),
            "sequences_at_or_above_0_80_identity_to_legacy121": sum(
                identity >= IDENTITY_THRESHOLD for identity in casp_identities
            ),
            "nonredundant_acgu_candidates": sum(
                identity < IDENTITY_THRESHOLD for identity in casp_identities
            ),
            "identity_audit_scope": "15 manifest-level entity sequences; 3 rows have blank entity_sequence",
            "proposed_role": "secondary future independent test candidate",
            "independent_test_ready": False,
            "blockers": "3 sequence/coordinate mappings unresolved; no complete normalized three-model predictions",
            "required_next_action": "resolve all 18 sequence-coordinate mappings, freeze manifest, predict and normalize",
        },
        {
            "dataset_candidate": "TS85_holdout67",
            "local_root": str(TS85_HOLDOUT_FASTA.parent.parent),
            "observed_rnas": 67,
            "sequences_ready_for_identity_audit": 67,
            "explicit_2d_gt_records": 0,
            "normalized_prediction_records_in_repo": 0,
            "complete_three_model_prediction_matrix": False,
            "prior_project_use": "3D benchmark working set only",
            "exact_sequence_matches_to_legacy121": holdout_exact,
            "sequences_at_or_above_0_80_identity_to_legacy121": "NOT_AUDITED",
            "nonredundant_acgu_candidates": "NOT_AUDITED",
            "identity_audit_scope": "exact sequence audit only; 31 exact Legacy matches",
            "proposed_role": "ineligible until 2D GT is frozen",
            "independent_test_ready": False,
            "blockers": "no authoritative 2D GT manifest; substantial Legacy overlap",
            "required_next_action": "do not use for refiner evaluation without independent 2D GT protocol",
        },
        {
            "dataset_candidate": "CASP16_working_set",
            "local_root": "/root/autodl-tmp/data/casp16",
            "observed_rnas": "UNKNOWN",
            "sequences_ready_for_identity_audit": "UNKNOWN",
            "explicit_2d_gt_records": 14,
            "normalized_prediction_records_in_repo": 0,
            "complete_three_model_prediction_matrix": False,
            "prior_project_use": "provisional staging assets",
            "exact_sequence_matches_to_legacy121": "UNKNOWN",
            "sequences_at_or_above_0_80_identity_to_legacy121": "UNKNOWN",
            "nonredundant_acgu_candidates": "UNKNOWN",
            "identity_audit_scope": "not auditable from a frozen manifest",
            "proposed_role": "ineligible current inventory",
            "independent_test_ready": False,
            "blockers": "no authoritative sample/chain/sequence/GT manifest; partial files",
            "required_next_action": "freeze provenance and coordinate mapping before reconsideration",
        },
    ]


def main() -> int:
    records = _load_records()
    entries = _label_entries(records)
    label_rows = _label_balance(entries)
    feature_rows = _feature_balance(entries)
    legacy_sequences: dict[str, str] = {}
    for record in records:
        previous = legacy_sequences.setdefault(record["rna_id"], record["sequence"])
        if previous != record["sequence"]:
            raise RuntimeError(f"sequence mismatch for {record['rna_id']}")
    external_rows, external_manifest = _external_candidates(legacy_sequences)
    split_rows = _dataset_inventory(legacy_sequences, external_rows, external_manifest)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    _write_csv(OUTPUT / "label_balance_by_model.csv", LABEL_FIELDS, label_rows)
    _write_csv(
        OUTPUT / "label_balance_by_feature_group.csv",
        FEATURE_FIELDS,
        feature_rows,
    )
    _write_csv(OUTPUT / "dataset_split_inventory.csv", SPLIT_FIELDS, split_rows)
    _write_csv(
        OUTPUT / "external77_gt_con_candidate_ids.csv",
        EXTERNAL_FIELDS,
        external_rows,
    )
    print(
        json.dumps(
            {
                "predicted_pair_label_rows": len(entries),
                "label_balance_rows": len(label_rows),
                "feature_group_rows": len(feature_rows),
                "dataset_inventory_rows": len(split_rows),
                "external77_rows": len(external_rows),
                "eligible_external77_candidates": sum(
                    row["eligible_external77_gt_con_v1_candidate"]
                    for row in external_rows
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
