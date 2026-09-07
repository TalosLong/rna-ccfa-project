#!/usr/bin/env python3
"""One-shot held-out inference after checkpoint, calibrator, and threshold sealing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    CHANNELS, CONDITIONS, DESCRIPTOR_COLUMNS, FOLDS, ITEM_DIM, MODEL_INPUT_COLUMNS,
    MODEL_SEEDS, Preprocessing, apply_platt, apply_threshold, discrimination,
    fixed_bin_ece, import_torch, make_ern_model, rna_balanced_reliability,
    mean_defined, sha256_file, threshold_search, utility_metrics, write_json,
)
from train_clean_learned_evidence_reconciliation_r4 import (  # noqa: E402
    METADATA_COLUMNS, Partition, item_columns, load_item_partition, matrix, predict,
    run_directory, seed_everything,
)


RESULTS = ROOT / "results/clean_learned_evidence_reconciliation_r4"
FEATURES = RESULTS / "features"
RUNS = RESULTS / "runs"
INTEGRITY = RESULTS / "integrity"


def verify_seal(directory: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    seal = json.loads((directory / "lock_seal.json").read_text())
    calibration = json.loads((directory / "calibration.json").read_text())
    threshold = json.loads((directory / "locked_threshold.json").read_text())
    checks = {
        "checkpoint_sha256": sha256_file(directory / "checkpoint.pt"),
        "calibration_sha256": sha256_file(directory / "calibration.json"),
        "locked_threshold_sha256": sha256_file(directory / "locked_threshold.json"),
        "validation_risk_curve_sha256": sha256_file(directory / "validation_risk_curve.parquet"),
    }
    if seal.get("status") != "SEALED_BEFORE_HELD_OUT" or any(seal[key] != value for key, value in checks.items()):
        raise RuntimeError(f"invalid pre-held-out lock seal: {directory}")
    return seal, calibration, threshold


def load_held_out_partition(channel: str, fold: int, preprocessing: Preprocessing) -> Partition:
    """Label access is possible only through this post-seal evaluator."""
    table = pq.read_table(
        FEATURES / "candidate_rows.parquet",
        columns=list(METADATA_COLUMNS + MODEL_INPUT_COLUMNS + DESCRIPTOR_COLUMNS),
        filters=[("channel", "=", channel), ("rna_fold", "=", int(fold))],
    )
    if not len(table) or set(table["rna_fold"].to_pylist()) != {int(fold)}:
        raise AssertionError("held-out reader crossed the locked test fold")
    items = load_item_partition(channel, (fold,))
    return Partition(table, items, preprocessing, channel)


def subset_metrics(rows: list[dict[str, object]], delete: np.ndarray) -> dict[str, object]:
    utility = utility_metrics(rows, delete)
    reliability = {
        "event_pooled": discrimination(rows),
        "rna_balanced": rna_balanced_reliability(rows),
        "reliability_bins": fixed_bin_ece(
            [float(row["calibrated_probability"]) for row in rows],
            [int(row["label_delete"]) for row in rows],
        ),
    }
    return {"reliability": reliability, "utility": utility}


def scope_accounting(rows: list[dict[str, object]], delete: np.ndarray) -> dict[str, object]:
    output = {}
    total = 0
    for scope in ("DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED"):
        indices = [index for index, row in enumerate(rows) if row["scope"] == scope]
        selected = [rows[index] for index in indices]
        flags = delete[indices]
        labels = np.asarray([int(row["label_delete"]) for row in selected], dtype=np.int8)
        deleted = int(flags.sum())
        removed = int(((labels == 1) & flags).sum())
        lost = int(((labels == 0) & flags).sum())
        total += len(selected)
        output[scope] = {
            "opportunity_count": len(selected), "deleted_pair_count": deleted,
            "removed_fp": removed, "lost_tp": lost,
            "tp_preservation": None if not int((labels == 0).sum()) else 1 - lost / int((labels == 0).sum()),
            "fp_removal": None if not int((labels == 1).sum()) else removed / int((labels == 1).sum()),
            "modification_precision": None if not deleted else removed / deleted,
            "coverage": None if not len(selected) else deleted / len(selected),
            "delta_f1": utility_metrics(
                rows,
                np.asarray([
                    bool(delete[index]) if rows[index]["scope"] == scope else False
                    for index in range(len(rows))
                ], dtype=bool),
            )["event_pooled"]["delta_f1"],
        }
    if total != len(rows):
        raise AssertionError("scope partition is not exhaustive")
    return output


def evidence_efficiency(rows: list[dict[str, object]], utility: dict[str, object]) -> dict[str, object]:
    context_items: dict[tuple[str, str], int] = {}
    for row in rows:
        count = int(row["item_count"])
        key = (str(row["manifest_id"]), str(row["source"]))
        prior = context_items.setdefault(key, count)
        if prior != count:
            raise AssertionError("inconsistent evidence item count")
    denominator = sum(context_items.values())
    event = utility["event_pooled"]
    rna_contexts: dict[str, dict[tuple[str, str], int]] = {}
    for row in rows:
        rna_id = str(row["rna_id"])
        rna_contexts.setdefault(rna_id, {})[(str(row["manifest_id"]), str(row["source"]))] = int(row["item_count"])
    fp_values = []
    delta_values = []
    for rna_id, contexts in rna_contexts.items():
        count = sum(contexts.values())
        per_rna = utility["per_rna"][rna_id]
        fp_values.append(None if not count else per_rna["removed_fp"] / count)
        delta_values.append(
            None if not count or per_rna["delta_f1"] is None else per_rna["delta_f1"] / count
        )
    rna_fp, rna_fp_defined = mean_defined(fp_values)
    rna_delta, rna_delta_defined = mean_defined(delta_values)
    return {
        "evidence_item_count": denominator,
        "fp_removed_per_evidence_item": None if not denominator else event["removed_fp"] / denominator,
        "delta_f1_per_evidence_item": None if not denominator else event["delta_f1"] / denominator,
        "rna_balanced_fp_removed_per_evidence_item": rna_fp,
        "rna_balanced_fp_removed_per_evidence_item_defined_rnas": rna_fp_defined,
        "rna_balanced_delta_f1_per_evidence_item": rna_delta,
        "rna_balanced_delta_f1_per_evidence_item_defined_rnas": rna_delta_defined,
        "zero_denominator_is_na": True,
    }


def evaluate_one(condition: str, channel: str, fold: int, seed: int, device, resume: bool) -> None:
    torch, _ = import_torch()
    directory = run_directory(condition, channel, fold, seed)
    output_path = directory / "held_out_evaluation.json"
    if output_path.exists():
        if resume and json.loads(output_path.read_text())["status"] == "PASS":
            print(f"SKIP evaluated {condition} {channel} fold={fold} seed={seed}", flush=True)
            return
        raise SystemExit(f"refusing to repeat held-out evaluation: {directory}")
    seal, calibration, threshold = verify_seal(directory)
    preprocessing = Preprocessing.from_json(json.loads((directory / "preprocessing.json").read_text()))
    held_out = load_held_out_partition(channel, fold, preprocessing)
    seed_everything(seed, torch)
    model = make_ern_model(ITEM_DIM[channel]).to(device)
    model.load_state_dict(torch.load(directory / "checkpoint.pt", map_location=device))
    logits_first = predict(model, held_out, channel, condition, device, 256)
    logits_second = predict(model, held_out, channel, condition, device, 256)
    if not np.array_equal(logits_first, logits_second):
        raise AssertionError("deterministic repeated held-out inference differed")
    probabilities = apply_platt(logits_first, calibration["a"], calibration["b"])
    delete = apply_threshold(probabilities, threshold["threshold"])
    rows = held_out.rows(logits_first, "held_out_test")
    for row, probability, flag in zip(rows, probabilities, delete):
        row["calibrated_probability"] = float(probability)
        row["locked_threshold"] = threshold["threshold"]
        row["decision"] = "DELETE" if flag else "KEEP"
        row["condition"] = condition
        row["model_seed"] = seed
        row["test_fold"] = fold
    if any(row["decision"] == "DELETE" and not row.get("original_pair_status") for row in rows):
        raise AssertionError("deletion-only invariant failed")
    scores_path = directory / "held_out_pair_scores.parquet"
    pq.write_table(pa.Table.from_pylist(rows), scores_path, compression="zstd")
    descriptive_rows = [dict(row, partition="validation") for row in rows]
    _, curve = threshold_search(descriptive_rows)
    for point in curve:
        point.pop("selected", None)
        point["curve_role"] = "HELD_OUT_DESCRIPTIVE_NOT_FOR_SELECTION"
    curve_path = directory / "held_out_risk_curve.parquet"
    pq.write_table(pa.Table.from_pylist(curve), curve_path, compression="zstd")
    metrics = subset_metrics(rows, delete)
    utility = metrics["utility"]
    evaluation = {
        "schema_version": "r4_held_out_evaluation_v1", "status": "PASS",
        "condition": condition, "channel": channel, "test_fold": fold, "seed": seed,
        "held_out_one_shot_after_lock": True, "lock_seal_sha256": sha256_file(directory / "lock_seal.json"),
        "held_out_rows": len(rows), "threshold": threshold["threshold"],
        "decision_states_observed": sorted({row["decision"] for row in rows}),
        "abstain_used_to_avoid_failure": False, "deletion_only": True, "added_pairs": 0,
        **metrics,
        "scope": scope_accounting(rows, delete),
        "evidence_efficiency": evidence_efficiency(rows, utility),
        "pair_scores_sha256": sha256_file(scores_path),
        "risk_curve_sha256": sha256_file(curve_path),
        "checkpoint_sha256": seal["checkpoint_sha256"],
        "calibration_sha256": seal["calibration_sha256"],
        "locked_threshold_sha256": seal["locked_threshold_sha256"],
        "held_out_used_for_training_calibration_or_threshold": False,
    }
    write_json(output_path, evaluation)
    print(f"EVALUATED {condition} {channel} fold={fold} seed={seed}", flush=True)


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
        print(json.dumps({"status": "PASS", "requested_runs": requested, "held_out_accessed": False}, indent=2))
        return
    torch, _ = import_torch()
    if not torch.cuda.is_available():
        raise SystemExit("held-out evaluation requires the audited CUDA runtime")
    device = torch.device("cuda")
    for condition in conditions:
        for channel in channels:
            for fold in folds:
                for seed in seeds:
                    evaluate_one(condition, channel, fold, seed, device, args.resume)
    if requested == 100:
        evaluations = list(RUNS.glob("*/*/fold_*/seed_*/held_out_evaluation.json"))
        if len(evaluations) != 100:
            raise AssertionError(f"expected 100 held-out evaluations, found {len(evaluations)}")
        write_json(INTEGRITY / "held_out_execution_audit.json", {
            "schema_version": "r4_held_out_execution_audit_v1", "status": "PASS",
            "evaluated_runs": 100, "all_after_lock": True, "one_shot": True,
            "held_out_used_for_selection": False, "rescue_thresholds": False,
        })


if __name__ == "__main__":
    main()
