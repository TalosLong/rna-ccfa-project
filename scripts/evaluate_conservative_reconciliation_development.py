#!/usr/bin/env python3
"""Run the single sealed Legacy121 CER development-assessment pass."""
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

from rna_ccfa.conservative_reconciliation import (  # noqa: E402
    BRANCHES, CHANNELS, CONDITIONS, MODEL_SEEDS, ROTATIONS, action_accounting,
    apply_policy_platt, branch_uses_evidence, cceg_actions, corroborated_scores,
    operational_scope, scope_accounting,
)
from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    DESCRIPTOR_COLUMNS, ITEM_DIM, MODEL_INPUT_COLUMNS, Preprocessing, apply_platt,
    discrimination, fixed_bin_ece, import_torch, make_ern_model,
    rna_balanced_reliability, sha256_file, write_json,
)
from train_clean_learned_evidence_reconciliation_r4 import (  # noqa: E402
    METADATA_COLUMNS, Partition,
)
from train_conservative_reconciliation_development import (  # noqa: E402
    R4_FEATURES, load_item_development_partition, predict_branch, run_directory,
    seed_everything,
)
from calibrate_and_lock_conservative_reconciliation import (  # noqa: E402
    calibration_path, threshold_directory,
)


RESULTS = ROOT / "results/conservative_reconciliation_development"
INTEGRITY = RESULTS / "integrity"
PAIR_SCORES = RESULTS / "pair_scores"
EVALUATION = RESULTS / "evaluation"


def verify_assessment_unlock() -> dict[str, object]:
    path = INTEGRITY / "assessment_unlock.json"
    if not path.exists():
        raise PermissionError("development-assessment remains locked")
    unlock = json.loads(path.read_text())
    if unlock.get("status") != "DEVELOPMENT_ASSESSMENT_UNLOCKED_ONCE":
        raise PermissionError("invalid development-assessment unlock state")
    for name, key in (
        ("complete_matrix_audit.json", "complete_matrix_audit_sha256"),
        ("threshold_lock_audit.json", "threshold_lock_audit_sha256"),
    ):
        if sha256_file(INTEGRITY / name) != unlock[key]:
            raise RuntimeError("assessment unlock provenance mismatch")
    return unlock


def verify_policy_seal(
    condition: str, channel: str, rotation: int, seed: int
) -> tuple[dict[str, object], dict[str, object]]:
    directory = threshold_directory(condition, channel, rotation, seed)
    seal = json.loads((directory / "lock_seal.json").read_text())
    policy = json.loads((directory / "policy_calibration.json").read_text())
    threshold = json.loads((directory / "locked_threshold.json").read_text())
    checks = {
        "policy_calibration_sha256": sha256_file(directory / "policy_calibration.json"),
        "locked_threshold_sha256": sha256_file(directory / "locked_threshold.json"),
        "validation_cceg_scores_sha256": sha256_file(directory / "validation_cceg_scores.parquet"),
        "validation_risk_curve_sha256": sha256_file(directory / "validation_risk_curve.parquet"),
    }
    if seal.get("status") != "SEALED_BEFORE_DEVELOPMENT_ASSESSMENT":
        raise RuntimeError(f"invalid assessment seal: {directory}")
    if any(seal.get(key) != value for key, value in checks.items()):
        raise RuntimeError(f"assessment seal hash mismatch: {directory}")
    if policy.get("fit_role") != "development_validation_only":
        raise RuntimeError("policy calibration role mismatch")
    if threshold.get("selection_role") != "development_validation_only":
        raise RuntimeError("threshold selection role mismatch")
    return policy, threshold


def load_assessment_partition(
    channel: str, rotation: int, preprocessing: Preprocessing
) -> Partition:
    """The only CER reader allowed to materialize assessment labels."""
    table = pq.read_table(
        R4_FEATURES / "candidate_rows.parquet",
        columns=list(METADATA_COLUMNS + MODEL_INPUT_COLUMNS + DESCRIPTOR_COLUMNS),
        filters=[("channel", "=", channel), ("rna_fold", "=", int(rotation))],
    )
    if not len(table) or set(table["rna_fold"].to_pylist()) != {int(rotation)}:
        raise AssertionError("development-assessment reader crossed a rotation")
    items = load_item_development_partition(channel, (rotation,))
    return Partition(table, items, preprocessing, channel)


def reliability(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "event_pooled": discrimination(rows, "q_cceg"),
        "rna_balanced": rna_balanced_reliability(rows, "q_cceg"),
        "reliability_bins": fixed_bin_ece(
            [float(row["q_cceg"]) for row in rows],
            [int(row["label_delete"]) for row in rows],
        ),
    }


def evaluate_one(
    condition: str, channel: str, rotation: int, seed: int, device, resume: bool
) -> None:
    output = PAIR_SCORES / condition / channel / f"rotation_{rotation}" / f"seed_{seed}.parquet"
    evaluation_path = EVALUATION / condition / channel / f"rotation_{rotation}" / f"seed_{seed}.json"
    if output.exists() or evaluation_path.exists():
        if resume and output.exists() and evaluation_path.exists():
            payload = json.loads(evaluation_path.read_text())
            if payload.get("status") == "PASS" and payload.get("pair_scores_sha256") == sha256_file(output):
                print(f"SKIP {condition} {channel} rotation={rotation} seed={seed}", flush=True)
                return
        raise SystemExit(f"refusing to repeat development-assessment: {output}")
    policy, threshold = verify_policy_seal(condition, channel, rotation, seed)
    branch_probabilities: dict[str, np.ndarray] = {}
    branch_logits: dict[str, np.ndarray] = {}
    assessment: Partition | None = None
    checkpoint_hashes = {}
    calibration_hashes = {}
    torch, _ = import_torch()
    for branch in BRANCHES:
        run = run_directory(condition, branch, channel, rotation, seed)
        preprocessing = Preprocessing.from_json(json.loads((run / "preprocessing.json").read_text()))
        current = load_assessment_partition(channel, rotation, preprocessing)
        if assessment is None:
            assessment = current
        elif not np.array_equal(assessment.row_ids, current.row_ids):
            raise AssertionError("assessment candidate rows differ between branches")
        model = make_ern_model(ITEM_DIM[channel]).to(device)
        model.load_state_dict(torch.load(run / "checkpoint.pt", map_location=device))
        seed_everything(seed, torch)
        masked = not branch_uses_evidence(condition, branch)
        first = predict_branch(model, current, channel, masked, device)
        second = predict_branch(model, current, channel, masked, device)
        if not np.array_equal(first, second):
            raise AssertionError("repeated CER assessment inference differed")
        calibration_file = calibration_path(condition, branch, channel, rotation, seed)
        calibration = json.loads(calibration_file.read_text())
        if calibration.get("fit_role") != "development_validation_only":
            raise AssertionError("branch calibrator is not validation-only")
        branch_logits[branch] = first
        branch_probabilities[branch] = apply_platt(first, calibration["a"], calibration["b"])
        checkpoint_hashes[branch] = sha256_file(run / "checkpoint.pt")
        calibration_hashes[branch] = sha256_file(calibration_file)
    assert assessment is not None
    q_e = branch_probabilities["EVIDENCE_BRANCH"]
    q_c = branch_probabilities["CONTEXT_BRANCH"]
    raw = corroborated_scores(q_e, q_c)
    q_cceg = apply_policy_platt(raw, policy)
    raw_cutoff = threshold["raw_corroboration_cutoff_c"]
    base = assessment.rows(branch_logits["EVIDENCE_BRANCH"], "development_assessment")
    evaluation_scopes = [str(row.pop("scope")) for row in base]
    operational_scopes = [operational_scope(condition, scope) for scope in evaluation_scopes]
    actions = cceg_actions(q_e, q_c, operational_scopes, raw_cutoff)
    rows = []
    for source, evaluation_scope, operational, qe, qc, r, q, action in zip(
        base, evaluation_scopes, operational_scopes, q_e, q_c, raw, q_cceg, actions
    ):
        row = dict(source)
        row.update({
            "condition": condition, "rotation": rotation, "model_seed": seed,
            "legacy121_role": "DEVELOPMENT_ONLY", "independent_test": False,
            "evaluation_scope": evaluation_scope, "operational_scope": operational,
            "q_e": float(qe), "q_c": float(qc), "r_cceg": float(r),
            "q_cceg": float(q), "threshold_tau": threshold["threshold_tau"],
            "raw_corroboration_cutoff_c": raw_cutoff, "action": action,
        })
        rows.append(row)
    if any(row["action"] == "DELETE" and not row["original_pair_status"] for row in rows):
        raise AssertionError("deletion-only invariant failed")
    output.parent.mkdir(parents=True, exist_ok=True)
    evaluation_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), output, compression="zstd")
    accounting = action_accounting(rows, actions)
    payload = {
        "schema_version": "conservative_reconciliation_development_evaluation_v1",
        "status": "PASS", "condition": condition, "channel": channel,
        "rotation": rotation, "model_seed": seed,
        "legacy121_role": "DEVELOPMENT_ONLY", "independent_confirmation": False,
        "one_sealed_development_assessment_pass": True,
        "assessment_used_for_selection": False, "rescue_tuning": False,
        "row_count": len(rows), "actions": accounting["actions"],
        "utility": accounting["utility"], "reliability": reliability(rows),
        "scope": scope_accounting(rows, actions),
        "checkpoint_sha256": checkpoint_hashes,
        "branch_calibration_sha256": calibration_hashes,
        "policy_calibration_sha256": sha256_file(threshold_directory(condition, channel, rotation, seed) / "policy_calibration.json"),
        "lock_seal_sha256": sha256_file(threshold_directory(condition, channel, rotation, seed) / "lock_seal.json"),
        "pair_scores_sha256": sha256_file(output),
    }
    write_json(evaluation_path, payload)
    print(f"ASSESSED {condition} {channel} rotation={rotation} seed={seed}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--condition", choices=CONDITIONS)
    parser.add_argument("--channel", choices=CHANNELS)
    parser.add_argument("--rotation", type=int, choices=ROTATIONS)
    parser.add_argument("--seed", type=int, choices=MODEL_SEEDS)
    args = parser.parse_args()
    verify_assessment_unlock()
    conditions = (args.condition,) if args.condition else CONDITIONS
    channels = (args.channel,) if args.channel else CHANNELS
    rotations = (args.rotation,) if args.rotation is not None else ROTATIONS
    seeds = (args.seed,) if args.seed is not None else MODEL_SEEDS
    requested = len(conditions) * len(channels) * len(rotations) * len(seeds)
    if args.dry_run:
        print(json.dumps({"status": "PASS", "planned_evaluations": requested, "legacy121_role": "DEVELOPMENT_ONLY"}, indent=2))
        return
    torch, _ = import_torch()
    if not torch.cuda.is_available():
        raise SystemExit("CER development assessment requires the audited CUDA runtime")
    device = torch.device("cuda")
    for condition in conditions:
        for channel in channels:
            for rotation in rotations:
                for seed in seeds:
                    evaluate_one(condition, channel, rotation, seed, device, args.resume)
    if requested == 100:
        evaluations = list(EVALUATION.glob("*/*/rotation_*/seed_*.json"))
        scores = list(PAIR_SCORES.glob("*/*/rotation_*/seed_*.parquet"))
        if len(evaluations) != 100 or len(scores) != 100:
            raise AssertionError("incomplete one-pass CER assessment matrix")
        write_json(INTEGRITY / "assessment_execution_audit.json", {
            "schema_version": "conservative_reconciliation_assessment_execution_audit_v1",
            "status": "PASS", "evaluations": 100, "pair_score_artifacts": 100,
            "all_after_complete_seal": True, "one_sealed_pass": True,
            "legacy121_role": "DEVELOPMENT_ONLY", "independent_confirmation": False,
            "assessment_used_for_selection": False, "rescue_tuning": False,
        })


if __name__ == "__main__":
    main()
