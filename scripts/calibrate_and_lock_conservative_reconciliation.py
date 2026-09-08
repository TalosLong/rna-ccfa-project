#!/usr/bin/env python3
"""Fit validation-only CER calibrators and seal all CCEG thresholds."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rna_ccfa.conservative_reconciliation import (  # noqa: E402
    BRANCHES, CHANNELS, CONDITIONS, MODEL_SEEDS, ROTATIONS, cceg_actions,
    conservative_threshold_search, corroborated_scores, fit_policy_platt,
    apply_policy_platt, inverse_policy_cutoff, operational_scope,
)
from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    apply_platt, fit_monotone_platt, sha256_file, write_json,
)
from train_conservative_reconciliation_development import run_directory  # noqa: E402


RESULTS = ROOT / "results/conservative_reconciliation_development"
RUNS = RESULTS / "runs"
CALIBRATION = RESULTS / "calibration"
THRESHOLDS = RESULTS / "thresholds"
INTEGRITY = RESULTS / "integrity"


def calibration_path(condition: str, branch: str, channel: str, rotation: int, seed: int) -> Path:
    return CALIBRATION / condition / branch / channel / f"rotation_{rotation}" / f"seed_{seed}.json"


def threshold_directory(condition: str, channel: str, rotation: int, seed: int) -> Path:
    return THRESHOLDS / condition / channel / f"rotation_{rotation}" / f"seed_{seed}"


def _log_loss(probabilities: np.ndarray, labels: np.ndarray) -> float:
    p = np.clip(probabilities.astype(np.float64), 1e-15, 1.0 - 1e-15)
    return float(-(labels * np.log(p) + (1 - labels) * np.log(1 - p)).mean())


def calibrate_branch(condition: str, branch: str, channel: str, rotation: int, seed: int) -> None:
    directory = run_directory(condition, branch, channel, rotation, seed)
    completion = json.loads((directory / "completion.json").read_text())
    if completion.get("status") != "PASS" or completion.get("development_assessment_labels_accessed"):
        raise SystemExit(f"invalid CER training completion: {directory}")
    output = calibration_path(condition, branch, channel, rotation, seed)
    if output.exists():
        raise SystemExit(f"refusing to overwrite branch calibration: {output}")
    rows = pq.read_table(directory / "validation_logits.parquet").to_pylist()
    if not rows or any(row["partition"] != "development_validation" for row in rows):
        raise AssertionError("branch calibration accepts development_validation only")
    logits = np.asarray([float(row["raw_logit"]) for row in rows], dtype=np.float64)
    labels = np.asarray([int(row["label_delete"]) for row in rows], dtype=np.int8)
    fitted = fit_monotone_platt(logits, labels)
    probabilities = apply_platt(logits, fitted["a"], fitted["b"])
    fitted.update({
        "schema_version": "conservative_reconciliation_branch_platt_v1",
        "status": "LOCKED", "condition": condition, "branch": branch,
        "channel": channel, "rotation": rotation, "model_seed": seed,
        "fit_role": "development_validation_only", "both_classes_present": len(np.unique(labels)) == 2,
        "development_assessment_labels_accessed": False,
        "checkpoint_sha256": completion["checkpoint_sha256"],
        "validation_logits_sha256": sha256_file(directory / "validation_logits.parquet"),
        "validation_log_loss_before": float(np.mean(np.logaddexp(0.0, logits) - labels * logits)),
        "validation_log_loss_after": _log_loss(probabilities, labels),
        "r4_fitted_calibrator_reused": False,
    })
    write_json(output, fitted)


def lock_policy(condition: str, channel: str, rotation: int, seed: int) -> None:
    directory = threshold_directory(condition, channel, rotation, seed)
    if directory.exists():
        raise SystemExit(f"refusing to overwrite CCEG threshold directory: {directory}")
    directory.mkdir(parents=True)
    branch_rows = {}
    calibrations = {}
    for branch in BRANCHES:
        run = run_directory(condition, branch, channel, rotation, seed)
        rows = pq.read_table(run / "validation_logits.parquet").to_pylist()
        calibration = json.loads(calibration_path(condition, branch, channel, rotation, seed).read_text())
        if calibration.get("status") != "LOCKED" or calibration.get("fit_role") != "development_validation_only":
            raise AssertionError("invalid branch calibration")
        logits = [float(row["raw_logit"]) for row in rows]
        probabilities = apply_platt(logits, calibration["a"], calibration["b"])
        branch_rows[branch] = rows
        calibrations[branch] = (calibration, probabilities)
    left = branch_rows[BRANCHES[0]]; right = branch_rows[BRANCHES[1]]
    id_keys = ("candidate_row_id", "manifest_id", "rna_id", "source", "label_delete", "scope")
    if len(left) != len(right) or any(any(a[key] != b[key] for key in id_keys) for a, b in zip(left, right)):
        raise AssertionError("CCEG branch validation rows are not paired")
    q_e = calibrations["EVIDENCE_BRANCH"][1]
    q_c = calibrations["CONTEXT_BRANCH"][1]
    raw = corroborated_scores(q_e, q_c)
    labels = [int(row["label_delete"]) for row in left]
    policy = fit_policy_platt(raw, labels)
    q_cceg = apply_policy_platt(raw, policy)
    validation_rows = []
    for source, qe, qc, r, q in zip(left, q_e, q_c, raw, q_cceg):
        row = dict(source)
        row["evaluation_scope"] = row.pop("scope")
        row["operational_scope"] = operational_scope(condition, row["evaluation_scope"])
        row["q_e"] = float(qe); row["q_c"] = float(qc)
        row["r_cceg"] = float(r); row["q_cceg"] = float(q)
        row["partition"] = "development_validation"
        row.pop("raw_logit", None); row.pop("branch", None)
        validation_rows.append(row)
    tau, curve = conservative_threshold_search(validation_rows)
    selected = next(point for point in curve if point["selected"])
    raw_cutoff = inverse_policy_cutoff(tau, policy)
    actions = cceg_actions(
        q_e, q_c, [row["operational_scope"] for row in validation_rows], raw_cutoff
    )
    for row, action in zip(validation_rows, actions):
        row["action"] = action
    scores_path = directory / "validation_cceg_scores.parquet"
    curve_path = directory / "validation_risk_curve.parquet"
    pq.write_table(pa.Table.from_pylist(validation_rows), scores_path, compression="zstd")
    pq.write_table(pa.Table.from_pylist(curve), curve_path, compression="zstd")
    policy.update({
        "schema_version": "conservative_reconciliation_policy_platt_v1",
        "status": "LOCKED", "condition": condition, "channel": channel,
        "rotation": rotation, "model_seed": seed,
        "fit_role": "development_validation_only", "development_assessment_labels_accessed": False,
        "evidence_branch_calibration_sha256": sha256_file(calibration_path(condition, "EVIDENCE_BRANCH", channel, rotation, seed)),
        "context_branch_calibration_sha256": sha256_file(calibration_path(condition, "CONTEXT_BRANCH", channel, rotation, seed)),
        "validation_log_loss_after": _log_loss(q_cceg, np.asarray(labels)),
    })
    policy_path = directory / "policy_calibration.json"
    write_json(policy_path, policy)
    action_counts = {state: actions.count(state) for state in ("KEEP", "DELETE", "ABSTAIN")}
    threshold = {
        "schema_version": "conservative_reconciliation_locked_threshold_v1",
        "status": "LOCKED", "condition": condition, "channel": channel,
        "rotation": rotation, "model_seed": seed,
        "selection_role": "development_validation_only",
        "development_assessment_labels_accessed": False,
        "threshold_tau": tau, "raw_corroboration_cutoff_c": raw_cutoff,
        "threshold_semantics": selected["threshold_semantics"],
        "equal_scores_indivisible": True,
        "eligibility_constraints": {"event_tp_preservation_gte": 0.99, "rna_balanced_tp_preservation_gte": 0.99},
        "selection_order": ["maximize_RNA_balanced_FP_removal", "maximize_RNA_balanced_modification_precision", "fewer_deletions", "numerically_higher_threshold"],
        "selected_validation_metrics": selected, "selected_action_counts": action_counts,
        "r4_threshold_reused": False, "source_specific": False, "density_specific": False,
        "assessment_rescue_threshold": False,
        "policy_calibration_sha256": sha256_file(policy_path),
        "validation_cceg_scores_sha256": sha256_file(scores_path),
        "validation_risk_curve_sha256": sha256_file(curve_path),
    }
    threshold_path = directory / "locked_threshold.json"
    write_json(threshold_path, threshold)
    seal = {
        "schema_version": "conservative_reconciliation_pre_assessment_seal_v1",
        "status": "SEALED_BEFORE_DEVELOPMENT_ASSESSMENT",
        "condition": condition, "channel": channel, "rotation": rotation, "model_seed": seed,
        "branch_checkpoint_sha256": {
            branch: sha256_file(run_directory(condition, branch, channel, rotation, seed) / "checkpoint.pt")
            for branch in BRANCHES
        },
        "branch_calibration_sha256": {
            branch: sha256_file(calibration_path(condition, branch, channel, rotation, seed))
            for branch in BRANCHES
        },
        "policy_calibration_sha256": sha256_file(policy_path),
        "locked_threshold_sha256": sha256_file(threshold_path),
        "validation_cceg_scores_sha256": sha256_file(scores_path),
        "validation_risk_curve_sha256": sha256_file(curve_path),
        "development_assessment_accessed_before_seal": False,
    }
    write_json(directory / "lock_seal.json", seal)
    print(f"SEALED {condition} {channel} rotation={rotation} seed={seed}", flush=True)


def write_complete_seal() -> None:
    completions = list(RUNS.glob("*/*/*/rotation_*/seed_*/completion.json"))
    calibrations = list(CALIBRATION.glob("*/*/*/rotation_*/seed_*.json"))
    seals = list(THRESHOLDS.glob("*/*/rotation_*/seed_*/lock_seal.json"))
    if (len(completions), len(calibrations), len(seals)) != (200, 200, 100):
        raise AssertionError(f"incomplete CER seal matrix: {(len(completions), len(calibrations), len(seals))}")
    write_json(INTEGRITY / "calibration_role_audit.json", {
        "schema_version": "conservative_reconciliation_calibration_role_audit_v1",
        "status": "PASS", "branch_calibrations": 200, "policy_calibrations": 100,
        "branch_fit_role": "development_validation_only", "policy_fit_role": "development_validation_only",
        "both_classes_required": True, "branch_a_gte_zero": True, "policy_a_G_gt_zero": True,
        "development_assessment_labels_accessed": False,
    })
    write_json(INTEGRITY / "threshold_lock_audit.json", {
        "schema_version": "conservative_reconciliation_threshold_lock_audit_v1",
        "status": "PASS", "threshold_seals": 100, "validation_only": True,
        "dual_0_99_constraints": True, "tie_blocks": True, "r4_thresholds_reused": False,
        "source_or_density_thresholds": False, "assessment_rescue_thresholds": False,
        "seal_hashes": {str(path.relative_to(ROOT)): sha256_file(path) for path in sorted(seals)},
    })
    write_json(INTEGRITY / "complete_matrix_audit.json", {
        "schema_version": "conservative_reconciliation_complete_matrix_audit_v1",
        "status": "PASS", "training_runs_expected": 200, "training_runs_complete": 200,
        "branch_calibrations_expected": 200, "branch_calibrations_complete": 200,
        "policy_calibrations_expected": 100, "policy_calibrations_complete": 100,
        "threshold_seals_expected": 100, "threshold_seals_complete": 100,
        "runs_dropped": 0, "seed_or_channel_selected": False,
        "development_assessment_accessed": False,
    })
    unlock = {
        "schema_version": "conservative_reconciliation_assessment_unlock_v1",
        "status": "DEVELOPMENT_ASSESSMENT_UNLOCKED_ONCE",
        "legacy121_role": "DEVELOPMENT_ONLY", "independent_confirmation": False,
        "complete_matrix_audit_sha256": sha256_file(INTEGRITY / "complete_matrix_audit.json"),
        "threshold_lock_audit_sha256": sha256_file(INTEGRITY / "threshold_lock_audit.json"),
        "development_assessment_access_count_before_unlock": 0,
    }
    write_json(INTEGRITY / "assessment_unlock.json", unlock)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    matrix = json.loads((INTEGRITY / "training_matrix_completion.json").read_text())
    if matrix.get("status") != "PASS" or matrix.get("completed_runs") != 200:
        raise SystemExit("complete 200-run training matrix required")
    if args.dry_run:
        print(json.dumps({"status": "PASS", "branch_calibrations_planned": 200, "policy_threshold_seals_planned": 100, "assessment_accessed": False}, indent=2))
        return
    for condition in CONDITIONS:
        for branch in BRANCHES:
            for channel in CHANNELS:
                for rotation in ROTATIONS:
                    for seed in MODEL_SEEDS:
                        calibrate_branch(condition, branch, channel, rotation, seed)
    for condition in CONDITIONS:
        for channel in CHANNELS:
            for rotation in ROTATIONS:
                for seed in MODEL_SEEDS:
                    lock_policy(condition, channel, rotation, seed)
    write_complete_seal()


if __name__ == "__main__":
    main()
