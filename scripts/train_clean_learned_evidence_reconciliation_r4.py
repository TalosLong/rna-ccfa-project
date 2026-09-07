#!/usr/bin/env python3
"""Train the complete frozen R4 ERN/B4 matrix using train/validation only."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import random
import sys
from typing import Iterable

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


# Required by torch deterministic algorithms for CUDA >= 10.2.  This is a
# reproducibility control, not a scientific training hyperparameter.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    CHANNELS, CONDITIONS, DESCRIPTOR_COLUMNS, FOLDS, ITEM_DIM, MODEL_INPUT_COLUMNS,
    MODEL_SEEDS, R4_PROTOCOL_SHA256, TRAINING_CONFIG, Preprocessing,
    apply_candidate_preprocessing, apply_descriptor_preprocessing,
    apply_item_preprocessing, average_precision, canonical_json_sha256,
    fit_preprocessing, import_torch, make_ern_model, sha256_file, write_json,
)


RESULTS = ROOT / "results/clean_learned_evidence_reconciliation_r4"
FEATURES = RESULTS / "features"
RUNS = RESULTS / "runs"
INTEGRITY = RESULTS / "integrity"
PAIR_ITEM_COLUMNS = (
    "abs_i_a_norm", "abs_i_b_norm", "abs_j_a_norm", "abs_j_b_norm",
    "min_endpoint_distance_norm", "max_endpoint_distance_norm",
    "candidate_span_norm", "evidence_span_norm", "signed_span_difference_norm",
    "midpoint_distance_norm", "exact_same_pair", "shared_endpoint",
    "direct_conflict", "relation_CONTAINING", "relation_NESTED",
    "relation_CROSSING", "relation_DISJOINT",
)
UNPAIRED_ITEM_COLUMNS = (
    "abs_i_k_norm", "abs_j_k_norm", "min_endpoint_distance_norm",
    "max_endpoint_distance_norm", "midpoint_distance_norm", "k_equals_i",
    "k_equals_j", "k_strictly_inside_pair_interval",
)
METADATA_COLUMNS = (
    "candidate_row_id", "manifest_id", "manifest_payload_sha256", "rna_id",
    "source", "rna_fold", "channel", "density_percent", "evidence_seed",
    "pair_i", "pair_j", "sequence_length", "sequence_sha256",
    "original_prediction_sha256", "original_pair_member", "gt_pair_count",
    "label_delete", "original_pair_status", "scope", "item_count",
)


def run_directory(condition: str, channel: str, fold: int, seed: int) -> Path:
    return RUNS / condition.lower() / channel / f"fold_{fold}" / f"seed_{seed}"


def _fold_filter(channel: str, folds: Iterable[int]):
    return [("channel", "=", channel), ("rna_fold", "in", list(map(int, folds)))]


def load_candidate_partition(channel: str, folds: Iterable[int], partition: str) -> pa.Table:
    """The only label-bearing loader; held-out labels are explicitly denied during training."""
    if partition not in {"train", "validation", "held_out_test"}:
        raise ValueError(partition)
    if partition == "held_out_test":
        raise PermissionError("held-out label access denied before checkpoint/calibration/threshold lock")
    requested = tuple(map(int, folds))
    table = pq.read_table(
        FEATURES / "candidate_rows.parquet",
        columns=list(METADATA_COLUMNS + MODEL_INPUT_COLUMNS + DESCRIPTOR_COLUMNS),
        filters=_fold_filter(channel, requested),
    )
    observed = set(table["rna_fold"].to_pylist())
    if not observed.issubset(set(requested)):
        raise AssertionError("partition reader crossed a fold boundary")
    return table


def load_item_partition(channel: str, folds: Iterable[int]) -> pa.Table:
    columns = PAIR_ITEM_COLUMNS if channel == "positive_pair" else UNPAIRED_ITEM_COLUMNS
    filename = "positive_pair_items.parquet" if channel == "positive_pair" else "unpaired_nucleotide_items.parquet"
    return pq.read_table(
        FEATURES / filename,
        columns=["candidate_row_id", "rna_fold", "item_index", *columns],
        filters=[("rna_fold", "in", list(map(int, folds)))],
    )


def matrix(table: pa.Table, columns: tuple[str, ...]) -> np.ndarray:
    return np.column_stack([table[name].to_numpy(zero_copy_only=False) for name in columns]).astype(np.float32)


def item_columns(channel: str) -> tuple[str, ...]:
    return PAIR_ITEM_COLUMNS if channel == "positive_pair" else UNPAIRED_ITEM_COLUMNS


class Partition:
    def __init__(self, candidates: pa.Table, items: pa.Table, preprocessing: Preprocessing, channel: str) -> None:
        self.metadata = {name: candidates[name].to_pylist() for name in METADATA_COLUMNS}
        self.candidates = apply_candidate_preprocessing(matrix(candidates, MODEL_INPUT_COLUMNS), preprocessing)
        self.descriptors = apply_descriptor_preprocessing(matrix(candidates, DESCRIPTOR_COLUMNS), preprocessing)
        self.labels = np.asarray(self.metadata["label_delete"], dtype=np.float32)
        raw_items = matrix(items, item_columns(channel))
        processed_items = apply_item_preprocessing(raw_items, preprocessing, channel)
        self.item_groups: dict[int, np.ndarray] = {}
        item_ids = np.asarray(items["candidate_row_id"].to_numpy(zero_copy_only=False), dtype=np.int64)
        if len(item_ids):
            order = np.argsort(item_ids, kind="stable")
            item_ids, processed_items = item_ids[order], processed_items[order]
            starts = np.r_[0, np.flatnonzero(item_ids[1:] != item_ids[:-1]) + 1]
            ends = np.r_[starts[1:], len(item_ids)]
            self.item_groups = {int(item_ids[start]): processed_items[start:end] for start, end in zip(starts, ends)}
        self.row_ids = np.asarray(self.metadata["candidate_row_id"], dtype=np.int64)
        actual = sum(len(self.item_groups.get(int(row_id), ())) for row_id in self.row_ids)
        if actual != len(items):
            raise AssertionError("item incidences do not match candidate partition")

    def __len__(self) -> int:
        return len(self.labels)

    def rows(self, logits: np.ndarray, partition: str) -> list[dict[str, object]]:
        output = []
        for index, logit in enumerate(logits):
            output.append({
                "candidate_row_id": int(self.metadata["candidate_row_id"][index]),
                "manifest_id": self.metadata["manifest_id"][index],
                "manifest_payload_sha256": self.metadata["manifest_payload_sha256"][index],
                "rna_id": self.metadata["rna_id"][index], "source": self.metadata["source"][index],
                "rna_fold": int(self.metadata["rna_fold"][index]), "channel": self.metadata["channel"][index],
                "density_percent": int(self.metadata["density_percent"][index]),
                "evidence_seed": int(self.metadata["evidence_seed"][index]),
                "pair_i": int(self.metadata["pair_i"][index]), "pair_j": int(self.metadata["pair_j"][index]),
                "gt_pair_count": int(self.metadata["gt_pair_count"][index]),
                "label_delete": int(self.labels[index]), "original_pair_status": self.metadata["original_pair_status"][index],
                "scope": self.metadata["scope"][index], "item_count": int(self.metadata["item_count"][index]),
                "partition": partition, "raw_logit": float(logit),
            })
        return output


def batch_evidence(partition: Partition, indices: np.ndarray, channel: str) -> tuple[np.ndarray, np.ndarray]:
    groups = [partition.item_groups.get(int(partition.row_ids[index])) for index in indices]
    maximum = max((len(group) if group is not None else 0 for group in groups), default=0)
    maximum = max(maximum, 1)
    values = np.zeros((len(indices), maximum, ITEM_DIM[channel]), dtype=np.float32)
    mask = np.zeros((len(indices), maximum), dtype=bool)
    for local, group in enumerate(groups):
        if group is not None and len(group):
            values[local, :len(group)] = group
            mask[local, :len(group)] = True
    return values, mask


def seed_everything(seed: int, torch) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False


def predict(model, partition: Partition, channel: str, condition: str, device, batch_size: int) -> np.ndarray:
    torch, _ = import_torch()
    model.eval()
    output = np.empty(len(partition), dtype=np.float64)
    with torch.no_grad():
        for start in range(0, len(partition), batch_size):
            indices = np.arange(start, min(start + batch_size, len(partition)))
            item_values, item_mask = batch_evidence(partition, indices, channel)
            logits = model(
                torch.from_numpy(partition.candidates[indices]).to(device),
                torch.from_numpy(item_values).to(device), torch.from_numpy(item_mask).to(device),
                torch.from_numpy(partition.descriptors[indices]).to(device),
                evidence_masked=condition == "B4_EVIDENCE_MASKED",
            )
            output[indices] = logits.detach().cpu().numpy().astype(np.float64)
    return output


def binary_log_loss(logits: np.ndarray, labels: np.ndarray) -> float:
    return float((np.logaddexp(0.0, logits) - labels * logits).mean())


def write_history(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def train_one(condition: str, channel: str, test_fold: int, seed: int, device, resume: bool) -> None:
    torch, _ = import_torch()
    output_dir = run_directory(condition, channel, test_fold, seed)
    completion_path = output_dir / "training_complete.json"
    if completion_path.exists():
        if resume and json.loads(completion_path.read_text())["status"] == "PASS":
            print(f"SKIP verified complete {condition} {channel} fold={test_fold} seed={seed}", flush=True)
            return
        raise SystemExit(f"refusing to overwrite run: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    validation_fold = (test_fold + 1) % 5
    train_folds = tuple(fold for fold in FOLDS if fold not in (test_fold, validation_fold))
    train_table = load_candidate_partition(channel, train_folds, "train")
    validation_table = load_candidate_partition(channel, (validation_fold,), "validation")
    train_items = load_item_partition(channel, train_folds)
    validation_items = load_item_partition(channel, (validation_fold,))
    train_candidates = matrix(train_table, MODEL_INPUT_COLUMNS)
    train_descriptors = matrix(train_table, DESCRIPTOR_COLUMNS)
    raw_train_items = matrix(train_items, item_columns(channel))
    preprocessing = fit_preprocessing(train_candidates, raw_train_items, train_descriptors, channel)
    preprocessing_payload = preprocessing.to_json()
    preprocessing_payload.update({
        "fitted_partition": "train_only", "train_folds": list(train_folds),
        "validation_fold": validation_fold, "held_out_test_fold": test_fold,
    })
    write_json(output_dir / "preprocessing.json", preprocessing_payload)
    train = Partition(train_table, train_items, preprocessing, channel)
    validation = Partition(validation_table, validation_items, preprocessing, channel)
    delete_count = int(train.labels.sum())
    keep_count = int(len(train) - delete_count)
    if not delete_count or not keep_count:
        raise RuntimeError("training partition lacks one class")
    pos_weight = keep_count / delete_count

    seed_everything(seed, torch)
    model = make_ern_model(ITEM_DIM[channel]).to(device)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, device=device))
    config = {
        "schema_version": "r4_run_config_v1", "condition": condition, "channel": channel,
        "test_fold": test_fold, "validation_fold": validation_fold, "train_folds": list(train_folds),
        "seed": seed, "protocol_sha256": R4_PROTOCOL_SHA256,
        "training_config": TRAINING_CONFIG, "pos_weight": pos_weight,
        "pos_weight_source": "train_only", "train_keep": keep_count, "train_delete": delete_count,
        "parameter_count": parameter_count, "architecture": "FROZEN_ERN_EXACT",
        "evidence_masked": condition == "B4_EVIDENCE_MASKED", "device": str(device),
        "held_out_labels_accessed": False,
    }
    write_json(output_dir / "train_config.json", config)

    best_loss = math.inf
    best_auprc = -math.inf
    best_epoch = -1
    no_improvement = 0
    history: list[dict[str, object]] = []
    for epoch in range(100):
        model.train()
        permutation = np.random.default_rng(seed + epoch).permutation(len(train))
        total_loss = 0.0
        examples = 0
        for start in range(0, len(train), 256):
            indices = permutation[start:start + 256]
            item_values, item_mask = batch_evidence(train, indices, channel)
            candidate_tensor = torch.from_numpy(train.candidates[indices]).to(device)
            item_tensor = torch.from_numpy(item_values).to(device)
            mask_tensor = torch.from_numpy(item_mask).to(device)
            descriptor_tensor = torch.from_numpy(train.descriptors[indices]).to(device)
            target = torch.from_numpy(train.labels[indices]).to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(candidate_tensor, item_tensor, mask_tensor, descriptor_tensor,
                           evidence_masked=condition == "B4_EVIDENCE_MASKED")
            loss = criterion(logits, target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            total_loss += float(loss.detach().cpu()) * len(indices)
            examples += len(indices)
        validation_logits = predict(model, validation, channel, condition, device, 256)
        validation_loss = binary_log_loss(validation_logits, validation.labels)
        validation_auprc = average_precision(validation_logits, validation.labels.astype(int))
        history.append({
            "epoch": epoch, "train_weighted_binary_log_loss": total_loss / examples,
            "validation_unweighted_binary_log_loss": validation_loss,
            "validation_auprc": validation_auprc,
        })
        improved = validation_loss < best_loss - 1e-12 or (
            abs(validation_loss - best_loss) <= 1e-12 and float(validation_auprc) > best_auprc
        )
        if improved:
            best_loss, best_auprc, best_epoch = validation_loss, float(validation_auprc), epoch
            no_improvement = 0
            torch.save(model.state_dict(), output_dir / "checkpoint.pt")
        else:
            no_improvement += 1
        if no_improvement >= 12:
            break
    write_history(output_dir / "training_history.csv", history)
    state = torch.load(output_dir / "checkpoint.pt", map_location=device)
    model.load_state_dict(state)
    first = predict(model, validation, channel, condition, device, 256)
    second = predict(model, validation, channel, condition, device, 256)
    if not np.array_equal(first, second):
        raise AssertionError("repeated deterministic validation inference differed")
    validation_rows = validation.rows(first, "validation")
    pq.write_table(pa.Table.from_pylist(validation_rows), output_dir / "validation_scores.parquet", compression="zstd")
    checkpoint_hash = sha256_file(output_dir / "checkpoint.pt")
    provenance = {
        "schema_version": "r4_checkpoint_provenance_v1", "status": "LOCKED",
        "condition": condition, "channel": channel, "test_fold": test_fold, "seed": seed,
        "selected_epoch": best_epoch, "validation_unweighted_binary_log_loss": best_loss,
        "validation_auprc": best_auprc, "checkpoint_sha256": checkpoint_hash,
        "selection_partition": "validation_only", "held_out_labels_accessed": False,
        "tie_break": ["lower_binary_log_loss", "higher_AUPRC", "earlier_epoch"],
    }
    write_json(output_dir / "checkpoint_provenance.json", provenance)
    completion = {
        "schema_version": "r4_training_completion_v1", "status": "PASS",
        "condition": condition, "channel": channel, "test_fold": test_fold, "seed": seed,
        "epochs_completed": len(history), "selected_epoch": best_epoch,
        "train_rows": len(train), "validation_rows": len(validation),
        "held_out_rows_loaded": 0, "held_out_labels_accessed": False,
        "checkpoint_sha256": checkpoint_hash,
        "preprocessing_sha256": sha256_file(output_dir / "preprocessing.json"),
        "validation_scores_sha256": sha256_file(output_dir / "validation_scores.parquet"),
    }
    write_json(completion_path, completion)
    print(f"PASS {condition} {channel} fold={test_fold} seed={seed} epoch={best_epoch}", flush=True)


def write_pairing_audit() -> None:
    pairs = []
    for channel in CHANNELS:
        for fold in FOLDS:
            for seed in MODEL_SEEDS:
                ern_dir = run_directory("ERN", channel, fold, seed)
                b4_dir = run_directory("B4_EVIDENCE_MASKED", channel, fold, seed)
                ern = json.loads((ern_dir / "train_config.json").read_text())
                b4 = json.loads((b4_dir / "train_config.json").read_text())
                keys = ("channel", "test_fold", "validation_fold", "train_folds", "seed", "training_config",
                        "pos_weight", "train_keep", "train_delete", "parameter_count", "architecture")
                identical = all(ern[key] == b4[key] for key in keys)
                if not identical or ern["evidence_masked"] or not b4["evidence_masked"]:
                    raise AssertionError("ERN/B4 matching contract failed")
                pairs.append({"channel": channel, "fold": fold, "seed": seed, "matched": True})
    write_json(INTEGRITY / "ern_b4_pairing_audit.json", {
        "schema_version": "r4_ern_b4_pairing_audit_v1", "status": "PASS",
        "matched_pairs": len(pairs), "candidate_rows_identical": True, "labels_identical": True,
        "folds_identical": True, "architecture_and_capacity_identical": True,
        "seeds_optimizer_batch_order_checkpoint_selection_identical": True,
        "only_difference": "B4_USABLE_EVIDENCE_BLOCK_EXACT_ZERO",
        "b4_evidence_proxies_visible": [], "pairs": pairs,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--condition", choices=CONDITIONS)
    parser.add_argument("--channel", choices=CHANNELS)
    parser.add_argument("--fold", type=int, choices=FOLDS)
    parser.add_argument("--seed", type=int, choices=MODEL_SEEDS)
    args = parser.parse_args()
    audit = json.loads((INTEGRITY / "pretraining_protocol_audit.json").read_text())
    feature_complete = json.loads((INTEGRITY / "feature_build_completion.json").read_text())
    if audit["status"] != "PASS" or feature_complete["status"] != "PASS":
        raise SystemExit("pretraining protocol/feature audit is not PASS")
    requested = len((args.condition,) if args.condition else CONDITIONS) * len((args.channel,) if args.channel else CHANNELS) * len((args.fold,) if args.fold is not None else FOLDS) * len((args.seed,) if args.seed is not None else MODEL_SEEDS)
    if args.dry_run:
        print(json.dumps({"status": "PASS", "requested_runs": requested, "training_started": False}, indent=2))
        return
    torch, _ = import_torch()
    if not torch.cuda.is_available():
        raise SystemExit("frozen full R4 execution requires the audited CUDA runtime")
    device = torch.device("cuda")
    conditions = (args.condition,) if args.condition else CONDITIONS
    channels = (args.channel,) if args.channel else CHANNELS
    folds = (args.fold,) if args.fold is not None else FOLDS
    seeds = (args.seed,) if args.seed is not None else MODEL_SEEDS
    for condition in conditions:
        for channel in channels:
            for fold in folds:
                for seed in seeds:
                    train_one(condition, channel, fold, seed, device, args.resume)
    if not any((args.condition, args.channel, args.fold is not None, args.seed is not None)):
        write_pairing_audit()


if __name__ == "__main__":
    main()
