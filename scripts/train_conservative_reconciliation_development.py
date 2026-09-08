#!/usr/bin/env python3
"""Train the complete frozen 200-run CER branch matrix."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import sys
from typing import Iterable

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rna_ccfa.conservative_reconciliation import (  # noqa: E402
    BRANCHES, CER_PROTOCOL_SHA256, CHANNELS, CONDITIONS, MODEL_SEEDS, ROTATIONS,
    TRAINING_CONFIG, branch_uses_evidence, complete_run_keys, make_cer_branch_model,
)
from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    DESCRIPTOR_COLUMNS, ITEM_DIM, MODEL_INPUT_COLUMNS, Preprocessing,
    apply_candidate_preprocessing, apply_descriptor_preprocessing,
    apply_item_preprocessing, average_precision, canonical_json_sha256,
    fit_preprocessing, import_torch, sha256_file, write_json,
)
from train_clean_learned_evidence_reconciliation_r4 import (  # noqa: E402
    METADATA_COLUMNS, Partition, batch_evidence, binary_log_loss, item_columns,
    matrix, seed_everything,
)


RESULTS = ROOT / "results/conservative_reconciliation_development"
R4_FEATURES = ROOT / "results/clean_learned_evidence_reconciliation_r4/features"
RUNS = RESULTS / "runs"
INTEGRITY = RESULTS / "integrity"


def run_directory(condition: str, branch: str, channel: str, rotation: int, seed: int) -> Path:
    return RUNS / condition / branch / channel / f"rotation_{rotation}" / f"seed_{seed}"


def _fold_filter(channel: str, folds: Iterable[int]):
    return [("channel", "=", channel), ("rna_fold", "in", list(map(int, folds)))]


def load_candidate_development_partition(
    channel: str, folds: Iterable[int], role: str
) -> pa.Table:
    if role not in {"development_train", "development_validation"}:
        raise PermissionError("development-assessment label access denied before complete seal")
    requested = tuple(map(int, folds))
    table = pq.read_table(
        R4_FEATURES / "candidate_rows.parquet",
        columns=list(METADATA_COLUMNS + MODEL_INPUT_COLUMNS + DESCRIPTOR_COLUMNS),
        filters=_fold_filter(channel, requested),
    )
    if not set(table["rna_fold"].to_pylist()).issubset(set(requested)):
        raise AssertionError("development partition reader crossed a fold boundary")
    return table


def load_item_development_partition(channel: str, folds: Iterable[int]) -> pa.Table:
    columns = item_columns(channel)
    filename = "positive_pair_items.parquet" if channel == "positive_pair" else "unpaired_nucleotide_items.parquet"
    return pq.read_table(
        R4_FEATURES / filename,
        columns=["candidate_row_id", "rna_fold", "item_index", *columns],
        filters=[("rna_fold", "in", list(map(int, folds)))],
    )


def predict_branch(model, partition: Partition, channel: str, evidence_masked: bool, device) -> np.ndarray:
    torch, _ = import_torch()
    model.eval()
    output = np.empty(len(partition), dtype=np.float64)
    with torch.no_grad():
        for start in range(0, len(partition), 256):
            indices = np.arange(start, min(start + 256, len(partition)))
            item_values, item_mask = batch_evidence(partition, indices, channel)
            logits = model(
                torch.from_numpy(partition.candidates[indices]).to(device),
                torch.from_numpy(item_values).to(device),
                torch.from_numpy(item_mask).to(device),
                torch.from_numpy(partition.descriptors[indices]).to(device),
                evidence_masked=evidence_masked,
            )
            output[indices] = logits.detach().cpu().numpy().astype(np.float64)
    return output


def _write_history(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def train_one(
    condition: str, branch: str, channel: str, rotation: int, seed: int, device, resume: bool
) -> None:
    torch, _ = import_torch()
    output = run_directory(condition, branch, channel, rotation, seed)
    completion_path = output / "completion.json"
    if completion_path.exists():
        if resume and json.loads(completion_path.read_text()).get("status") == "PASS":
            print(f"SKIP {condition} {branch} {channel} rotation={rotation} seed={seed}", flush=True)
            return
        raise SystemExit(f"refusing to overwrite CER run: {output}")
    output.mkdir(parents=True, exist_ok=False)
    validation_fold = (rotation + 1) % 5
    train_folds = tuple(fold for fold in ROTATIONS if fold not in (rotation, validation_fold))
    train_table = load_candidate_development_partition(channel, train_folds, "development_train")
    validation_table = load_candidate_development_partition(channel, (validation_fold,), "development_validation")
    train_items = load_item_development_partition(channel, train_folds)
    validation_items = load_item_development_partition(channel, (validation_fold,))
    preprocessing = fit_preprocessing(
        matrix(train_table, MODEL_INPUT_COLUMNS), matrix(train_items, item_columns(channel)),
        matrix(train_table, DESCRIPTOR_COLUMNS), channel,
    )
    prep = preprocessing.to_json()
    prep.update({
        "fitted_role": "development_train_only", "development_train_folds": list(train_folds),
        "development_validation_fold": validation_fold, "development_assessment_fold": rotation,
    })
    write_json(output / "preprocessing.json", prep)
    train = Partition(train_table, train_items, preprocessing, channel)
    validation = Partition(validation_table, validation_items, preprocessing, channel)
    delete_count = int(train.labels.sum()); keep_count = int(len(train) - delete_count)
    if not delete_count or not keep_count:
        raise RuntimeError("development_train partition lacks one class")
    pos_weight = keep_count / delete_count
    uses_evidence = branch_uses_evidence(condition, branch)
    evidence_masked = not uses_evidence

    seed_everything(seed, torch)
    model = make_cer_branch_model(channel).to(device)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, device=device))
    config = {
        "schema_version": "conservative_reconciliation_run_config_v1",
        "condition": condition, "branch": branch, "channel": channel,
        "rotation": rotation, "development_assessment_fold": rotation,
        "development_validation_fold": validation_fold, "development_train_folds": list(train_folds),
        "model_seed": seed, "protocol_sha256": CER_PROTOCOL_SHA256,
        "training_config": TRAINING_CONFIG, "pos_weight": pos_weight,
        "pos_weight_source": "development_train_only", "train_keep": keep_count,
        "train_delete": delete_count, "parameter_count": parameter_count,
        "architecture": "EXACT_R4_ERN_BRANCH", "usable_evidence": uses_evidence,
        "evidence_block_exact_zero": evidence_masked, "device": str(device),
        "development_assessment_rows_loaded": 0,
        "development_assessment_labels_accessed": False,
        "r4_fitted_checkpoint_reused": False,
    }
    write_json(output / "run_config.json", config)

    best_loss = math.inf; best_auprc = -math.inf; best_epoch = -1
    no_improvement = 0; history: list[dict[str, object]] = []
    for epoch in range(100):
        model.train()
        permutation = np.random.default_rng(seed + epoch).permutation(len(train))
        total_loss = 0.0; examples = 0
        for start in range(0, len(train), 256):
            indices = permutation[start:start + 256]
            item_values, item_mask = batch_evidence(train, indices, channel)
            optimizer.zero_grad(set_to_none=True)
            logits = model(
                torch.from_numpy(train.candidates[indices]).to(device),
                torch.from_numpy(item_values).to(device),
                torch.from_numpy(item_mask).to(device),
                torch.from_numpy(train.descriptors[indices]).to(device),
                evidence_masked=evidence_masked,
            )
            targets = torch.from_numpy(train.labels[indices]).to(device)
            loss = criterion(logits, targets)
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); optimizer.step()
            total_loss += float(loss.detach().cpu()) * len(indices); examples += len(indices)
        validation_logits = predict_branch(model, validation, channel, evidence_masked, device)
        validation_loss = binary_log_loss(validation_logits, validation.labels)
        validation_auprc = float(average_precision(validation_logits, validation.labels.astype(int)))
        history.append({
            "epoch": epoch, "train_weighted_binary_log_loss": total_loss / examples,
            "validation_unweighted_binary_log_loss": validation_loss,
            "validation_auprc": validation_auprc,
        })
        improved = validation_loss < best_loss - 1e-12 or (
            abs(validation_loss - best_loss) <= 1e-12 and validation_auprc > best_auprc
        )
        if improved:
            best_loss, best_auprc, best_epoch = validation_loss, validation_auprc, epoch
            no_improvement = 0; torch.save(model.state_dict(), output / "checkpoint.pt")
        else:
            no_improvement += 1
        if no_improvement >= 12:
            break
    _write_history(output / "training_history.csv", history)
    model.load_state_dict(torch.load(output / "checkpoint.pt", map_location=device))
    first = predict_branch(model, validation, channel, evidence_masked, device)
    second = predict_branch(model, validation, channel, evidence_masked, device)
    if not np.array_equal(first, second):
        raise AssertionError("repeated deterministic validation inference differed")
    validation_rows = validation.rows(first, "development_validation")
    for row in validation_rows:
        row["condition"] = condition; row["branch"] = branch
        row["rotation"] = rotation; row["model_seed"] = seed
    pq.write_table(pa.Table.from_pylist(validation_rows), output / "validation_logits.parquet", compression="zstd")
    checkpoint_hash = sha256_file(output / "checkpoint.pt")
    provenance = {
        "schema_version": "conservative_reconciliation_checkpoint_provenance_v1",
        "status": "LOCKED", "condition": condition, "branch": branch,
        "channel": channel, "rotation": rotation, "model_seed": seed,
        "selected_epoch": best_epoch, "validation_unweighted_binary_log_loss": best_loss,
        "validation_auprc": best_auprc, "checkpoint_sha256": checkpoint_hash,
        "selection_role": "development_validation_only",
        "development_assessment_labels_accessed": False,
        "tie_break": ["lower_binary_log_loss", "higher_AUPRC", "earlier_epoch"],
        "r4_checkpoint_reused": False,
    }
    write_json(output / "checkpoint_provenance.json", provenance)
    completion = {
        "schema_version": "conservative_reconciliation_training_completion_v1",
        "status": "PASS", "condition": condition, "branch": branch,
        "channel": channel, "rotation": rotation, "model_seed": seed,
        "epochs_completed": len(history), "selected_epoch": best_epoch,
        "development_train_rows": len(train), "development_validation_rows": len(validation),
        "development_assessment_rows_loaded": 0,
        "development_assessment_labels_accessed": False,
        "checkpoint_sha256": checkpoint_hash,
        "preprocessing_sha256": sha256_file(output / "preprocessing.json"),
        "validation_logits_sha256": sha256_file(output / "validation_logits.parquet"),
    }
    write_json(completion_path, completion)
    print(f"PASS {condition} {branch} {channel} rotation={rotation} seed={seed} epoch={best_epoch}", flush=True)


def _state_equal(first: Path, second: Path) -> bool:
    torch, _ = import_torch()
    left = torch.load(first, map_location="cpu"); right = torch.load(second, map_location="cpu")
    return left.keys() == right.keys() and all(torch.equal(left[key], right[key]) for key in left)


def write_pairing_audits() -> None:
    expected = complete_run_keys()
    completions = list(RUNS.glob("*/*/*/rotation_*/seed_*/completion.json"))
    if len(completions) != 200:
        raise AssertionError(f"expected 200 completed branch runs, found {len(completions)}")
    pair_rows = []
    masked_equal = []
    for condition in CONDITIONS:
        for channel in CHANNELS:
            for rotation in ROTATIONS:
                for seed in MODEL_SEEDS:
                    dirs = {branch: run_directory(condition, branch, channel, rotation, seed) for branch in BRANCHES}
                    configs = {branch: json.loads((path / "run_config.json").read_text()) for branch, path in dirs.items()}
                    keys = (
                        "channel", "rotation", "development_assessment_fold",
                        "development_validation_fold", "development_train_folds", "model_seed",
                        "training_config", "pos_weight", "train_keep", "train_delete",
                        "parameter_count", "architecture",
                    )
                    if not all(configs[BRANCHES[0]][key] == configs[BRANCHES[1]][key] for key in keys):
                        raise AssertionError("within-condition branch pairing mismatch")
                    pair_rows.append({"condition": condition, "channel": channel, "rotation": rotation, "model_seed": seed, "matched": True})
                    if condition == "CER_EVIDENCE_MASKED":
                        comparison_columns = ("candidate_row_id", "label_delete", "raw_logit")
                        validation = {
                            branch: pq.read_table(path / "validation_logits.parquet", columns=list(comparison_columns)).to_pydict()
                            for branch, path in dirs.items()
                        }
                        logits_equal = all(
                            validation[BRANCHES[0]][column] == validation[BRANCHES[1]][column]
                            for column in comparison_columns
                        )
                        weights_equal = _state_equal(dirs[BRANCHES[0]] / "checkpoint.pt", dirs[BRANCHES[1]] / "checkpoint.pt")
                        if not logits_equal or not weights_equal:
                            raise AssertionError("fully masked deterministic branches differ")
                        masked_equal.append({"channel": channel, "rotation": rotation, "model_seed": seed, "weights_equal": True, "validation_logits_equal": True})
    write_json(INTEGRITY / "branch_pairing_audit.json", {
        "schema_version": "conservative_reconciliation_branch_pairing_audit_v1",
        "status": "PASS", "materialized_branch_runs": len(expected),
        "within_condition_pairs": len(pair_rows), "candidate_rows_labels_splits_identical": True,
        "architecture_capacity_optimizer_batch_checkpoint_rule_identical": True,
        "base_model_seeds_identical": True, "pairs": pair_rows,
    })
    write_json(INTEGRITY / "evidence_mask_audit.json", {
        "schema_version": "conservative_reconciliation_evidence_mask_audit_v1",
        "status": "PASS", "fully_masked_branch_pairs": len(masked_equal),
        "all_materialized": True, "all_weights_and_validation_numeric_outputs_equal": True,
        "comparison_columns": ["candidate_row_id", "label_delete", "raw_logit"],
        "branch_metadata_expected_to_differ": True,
        "zeroed_proxies": ["item_tensors", "masks", "item_count", "item_count_div_L", "LOCAL_CONFLICT", "DIRECT", "channel_evidence", "density", "evidence_seed"],
        "pairs": masked_equal,
    })
    write_json(INTEGRITY / "training_matrix_completion.json", {
        "schema_version": "conservative_reconciliation_training_matrix_v1",
        "status": "PASS", "expected_runs": 200, "completed_runs": len(completions),
        "all_runs_retained": True, "seed_or_channel_selected": False,
        "development_assessment_accessed": False,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--condition", choices=CONDITIONS)
    parser.add_argument("--branch", choices=BRANCHES)
    parser.add_argument("--channel", choices=CHANNELS)
    parser.add_argument("--rotation", type=int, choices=ROTATIONS)
    parser.add_argument("--seed", type=int, choices=MODEL_SEEDS)
    args = parser.parse_args()
    audit = json.loads((INTEGRITY / "pretraining_protocol_audit.json").read_text())
    references = json.loads((INTEGRITY / "feature_reference_completion.json").read_text())
    if audit.get("status") != "PASS" or references.get("status") != "PASS":
        raise SystemExit("CER protocol/reference audit is not PASS")
    conditions = (args.condition,) if args.condition else CONDITIONS
    branches = (args.branch,) if args.branch else BRANCHES
    channels = (args.channel,) if args.channel else CHANNELS
    rotations = (args.rotation,) if args.rotation is not None else ROTATIONS
    seeds = (args.seed,) if args.seed is not None else MODEL_SEEDS
    requested = len(conditions) * len(branches) * len(channels) * len(rotations) * len(seeds)
    if args.dry_run:
        print(json.dumps({"status": "PASS", "requested_runs": requested, "training_started": False}, indent=2))
        return
    torch, _ = import_torch()
    if not torch.cuda.is_available():
        raise SystemExit("frozen full CER execution requires CUDA")
    device = torch.device("cuda")
    for condition in conditions:
        for branch in branches:
            for channel in channels:
                for rotation in rotations:
                    for seed in seeds:
                        train_one(condition, branch, channel, rotation, seed, device, args.resume)
    if requested == 200:
        write_pairing_audits()


if __name__ == "__main__":
    main()
