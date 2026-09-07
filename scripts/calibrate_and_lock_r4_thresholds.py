#!/usr/bin/env python3
"""Fit validation-only monotone calibration and seal frozen R4 thresholds."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    CHANNELS, CONDITIONS, FOLDS, MODEL_SEEDS, apply_platt, fit_monotone_platt,
    sha256_file, threshold_search, write_json,
)


RESULTS = ROOT / "results/clean_learned_evidence_reconciliation_r4"
RUNS = RESULTS / "runs"
INTEGRITY = RESULTS / "integrity"


def run_directory(condition: str, channel: str, fold: int, seed: int) -> Path:
    return RUNS / condition.lower() / channel / f"fold_{fold}" / f"seed_{seed}"


def lock_one(condition: str, channel: str, fold: int, seed: int, resume: bool) -> None:
    directory = run_directory(condition, channel, fold, seed)
    completion = json.loads((directory / "training_complete.json").read_text())
    if completion["status"] != "PASS" or completion["held_out_labels_accessed"]:
        raise SystemExit(f"invalid training completion: {directory}")
    seal_path = directory / "lock_seal.json"
    if seal_path.exists():
        if resume and json.loads(seal_path.read_text())["status"] == "SEALED_BEFORE_HELD_OUT":
            print(f"SKIP sealed {condition} {channel} fold={fold} seed={seed}", flush=True)
            return
        raise SystemExit(f"refusing to overwrite locked run: {directory}")
    table = pq.read_table(directory / "validation_scores.parquet")
    rows = table.to_pylist()
    if not rows or any(row["partition"] != "validation" for row in rows):
        raise AssertionError("calibration accepts validation rows only")
    labels = [int(row["label_delete"]) for row in rows]
    logits = [float(row["raw_logit"]) for row in rows]
    calibration = fit_monotone_platt(logits, labels)
    uncalibrated_loss = sum(math.log1p(math.exp(-abs(value))) + max(value, 0.0) - label * value
                            for value, label in zip(logits, labels)) / len(labels)
    calibrated_preview = apply_platt(logits, calibration["a"], calibration["b"])
    calibrated_loss = -sum(
        label * math.log(min(max(float(probability), 1e-15), 1 - 1e-15))
        + (1 - label) * math.log(1 - min(max(float(probability), 1e-15), 1 - 1e-15))
        for probability, label in zip(calibrated_preview, labels)
    ) / len(labels)
    calibration.update({
        "schema_version": "r4_monotone_platt_calibration_v1", "status": "LOCKED",
        "condition": condition, "channel": channel, "test_fold": fold, "seed": seed,
        "fit_partition": "validation_only", "held_out_labels_accessed": False,
        "checkpoint_sha256": completion["checkpoint_sha256"],
        "validation_scores_sha256": sha256_file(directory / "validation_scores.parquet"),
        "validation_log_loss_before": uncalibrated_loss,
        "validation_log_loss_after": calibrated_loss,
    })
    calibration_path = directory / "calibration.json"
    write_json(calibration_path, calibration)
    probabilities = calibrated_preview
    for row, probability in zip(rows, probabilities):
        row["calibrated_probability"] = float(probability)
    threshold, curve = threshold_search(rows)
    selected = next(row for row in curve if row["selected"])
    risk_curve_path = directory / "validation_risk_curve.parquet"
    pq.write_table(pa.Table.from_pylist(curve), risk_curve_path, compression="zstd")
    threshold_payload = {
        "schema_version": "r4_locked_threshold_v1", "status": "LOCKED",
        "condition": condition, "channel": channel, "test_fold": fold, "seed": seed,
        "selection_partition": "validation_only", "held_out_labels_accessed": False,
        "threshold": threshold, "threshold_semantics": selected["threshold_semantics"],
        "equal_scores_handled_as_indivisible_blocks": True,
        "eligibility_constraints": {
            "event_tp_preservation_gte": 0.99, "rna_balanced_tp_preservation_gte": 0.99,
        },
        "selection_order": [
            "maximize_RNA-balanced_FP_removal", "maximize_RNA-balanced_modification_precision",
            "fewer_deletions", "numerically_higher_threshold",
        ],
        "selected_validation_metrics": selected,
        "checkpoint_sha256": completion["checkpoint_sha256"],
        "calibration_sha256": sha256_file(calibration_path),
        "validation_risk_curve_sha256": sha256_file(risk_curve_path),
        "rescue_threshold": False,
    }
    threshold_path = directory / "locked_threshold.json"
    write_json(threshold_path, threshold_payload)
    seal = {
        "schema_version": "r4_pre_held_out_lock_seal_v1", "status": "SEALED_BEFORE_HELD_OUT",
        "condition": condition, "channel": channel, "test_fold": fold, "seed": seed,
        "checkpoint_sha256": completion["checkpoint_sha256"],
        "calibration_sha256": sha256_file(calibration_path),
        "locked_threshold_sha256": sha256_file(threshold_path),
        "validation_risk_curve_sha256": sha256_file(risk_curve_path),
        "held_out_labels_accessed_before_seal": False,
    }
    write_json(seal_path, seal)
    print(f"SEALED {condition} {channel} fold={fold} seed={seed}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--condition", choices=CONDITIONS)
    parser.add_argument("--channel", choices=CHANNELS)
    parser.add_argument("--fold", type=int, choices=FOLDS)
    parser.add_argument("--seed", type=int, choices=MODEL_SEEDS)
    args = parser.parse_args()
    conditions = (args.condition,) if args.condition else CONDITIONS
    channels = (args.channel,) if args.channel else CHANNELS
    folds = (args.fold,) if args.fold is not None else FOLDS
    seeds = (args.seed,) if args.seed is not None else MODEL_SEEDS
    requested = len(conditions) * len(channels) * len(folds) * len(seeds)
    if args.dry_run:
        print(json.dumps({"status": "PASS", "requested_runs": requested, "calibration_started": False}, indent=2))
        return
    for condition in conditions:
        for channel in channels:
            for fold in folds:
                for seed in seeds:
                    lock_one(condition, channel, fold, seed, args.resume)
    if not any((args.condition, args.channel, args.fold is not None, args.seed is not None)):
        seals = list(RUNS.glob("*/*/fold_*/seed_*/lock_seal.json"))
        if len(seals) != 100:
            raise AssertionError(f"expected 100 lock seals, found {len(seals)}")
        write_json(INTEGRITY / "threshold_lock_audit.json", {
            "schema_version": "r4_threshold_lock_audit_v1", "status": "PASS",
            "sealed_runs": 100, "validation_only": True, "dual_preservation_constraints": True,
            "tie_blocks": True, "held_out_rescue_thresholds": False,
            "seal_inventory": {str(path.relative_to(ROOT)): sha256_file(path) for path in sorted(seals)},
        })


if __name__ == "__main__":
    main()
