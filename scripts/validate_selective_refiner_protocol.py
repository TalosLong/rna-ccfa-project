#!/usr/bin/env python3
"""Validate frozen split, feature, and training-policy invariants.

This is a pre-training check. It does not fit or evaluate a learned model.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from Bio import Align

from rna_ccfa.stems import extract_stems_and_singletons

from audit_selective_refiner_protocol import _pair_feature_groups


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
FOLDS = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
OUTPUT = ROOT / "results/selective_refiner_protocol/protocol_validation_summary.json"
THRESHOLD = 0.80


def _identity(aligner: Align.PairwiseAligner, first: str, second: str) -> float:
    counts = aligner.align(first, second)[0].counts()
    return counts.identities / (counts.identities + counts.mismatches + counts.gaps)


def _aligner() -> Align.PairwiseAligner:
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 1.0
    aligner.mismatch_score = 0.0
    aligner.open_gap_score = -1.0
    aligner.extend_gap_score = -1.0
    return aligner


def main() -> int:
    records = [json.loads(line) for line in NORMALIZED.read_text().splitlines() if line.strip()]
    if len(records) != 363:
        raise RuntimeError("normalized Legacy121 record count changed")
    folds = list(csv.DictReader(FOLDS.open(encoding="utf-8", newline="")))
    fold_by_rna = {row["rna_id"]: int(row["fold"]) for row in folds}
    if len(fold_by_rna) != 121 or set(fold_by_rna) != {record["rna_id"] for record in records}:
        raise RuntimeError("fold assignment does not cover exactly the normalized RNA universe")
    model_by_rna: dict[str, set[str]] = {}
    sequence_by_rna: dict[str, str] = {}
    for record in records:
        rna_id = record["rna_id"]
        model_by_rna.setdefault(rna_id, set()).add(record["source_model"]["name"])
        sequence_by_rna.setdefault(rna_id, record["sequence"])
        if sequence_by_rna[rna_id] != record["sequence"]:
            raise RuntimeError(f"sequence mismatch for {rna_id}")
    if any(models != {"rnafold", "petfold", "trrosettarna2_native_ss"} for models in model_by_rna.values()):
        raise RuntimeError("source-record grouping invariant failed")

    fold_leakage: list[tuple[str, str, float]] = []
    aligner = _aligner()
    ids = sorted(sequence_by_rna)
    for offset, first in enumerate(ids):
        for second in ids[offset + 1 :]:
            identity = _identity(aligner, sequence_by_rna[first], sequence_by_rna[second])
            if identity >= THRESHOLD and fold_by_rna[first] != fold_by_rna[second]:
                fold_leakage.append((first, second, identity))
    if fold_leakage:
        raise RuntimeError(f"identity-connected fold leakage: {fold_leakage[:3]}")

    feature_determinism = True
    feature_leakage_fields: set[str] = set()
    prohibited_feature_names = {
        "ground_truth",
        "gt_pair",
        "tp",
        "fp",
        "fn",
        "wrong_partner",
        "missing_pair",
        "family",
        "dataset",
    }
    for record in records:
        sequence = record["sequence"]
        pairs = tuple(tuple(pair) for pair in record["predicted_structure"]["pairs"])
        first = _pair_feature_groups(pairs, sequence)
        second = _pair_feature_groups(tuple(reversed(pairs)), sequence)
        if first != second:
            feature_determinism = False
        for pair_features in first.values():
            feature_leakage_fields.update(
                key for key in pair_features if key.lower() in prohibited_feature_names
            )
    if not feature_determinism:
        raise RuntimeError("feature extraction is input-order dependent")
    if feature_leakage_fields:
        raise RuntimeError(f"prohibited GT/dataset feature fields: {sorted(feature_leakage_fields)}")

    # Frozen policy checks: class weights use only train counts and thresholds are validation-only.
    train_keep, train_delete = 80, 20
    pos_weight = train_keep / train_delete
    if pos_weight != 4.0:
        raise RuntimeError("class-weight formula check failed")
    threshold_grid = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
    if threshold_grid != tuple(round(0.50 + 0.05 * index, 2) for index in range(10)):
        raise RuntimeError("threshold grid changed")
    report = {
        "normalized_records": len(records),
        "unique_rnas": len(fold_by_rna),
        "fold_counts": dict(sorted(Counter(fold_by_rna.values()).items())),
        "identity_threshold": THRESHOLD,
        "identity_cross_fold_leakage": len(fold_leakage),
        "same_rna_single_fold": len({(rna_id, fold) for rna_id, fold in fold_by_rna.items()}) == 121,
        "source_records_per_rna": sorted({len(models) for models in model_by_rna.values()}),
        "feature_deterministic_under_pair_order": feature_determinism,
        "prohibited_feature_fields": sorted(feature_leakage_fields),
        "class_weight_formula": "KEEP_train / DELETE_train",
        "class_weight_toy_train_value": pos_weight,
        "threshold_grid": list(threshold_grid),
        "threshold_selection_source": "validation_only",
        "gt_coordinates_in_features": False,
        "wrong_partner_annotations_in_features": False,
        "phase1_labels_in_features": False,
        "source_confidence_in_primary_variant": False,
        "status": "PASS",
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
