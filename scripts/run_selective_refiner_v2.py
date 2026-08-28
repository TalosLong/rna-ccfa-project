#!/usr/bin/env python3
"""Run the preregistered Legacy121 selective-refiner v2 experiment.

Only the two CROSS backbones are trained. The two pooled v1 backbones are
reconstructed from their immutable local checkpoints and used as BASE.
external77 is intentionally outside every path read by this script.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch import nn

from rna_ccfa.cross_model import cross_model_agreement_features
from rna_ccfa.metrics import metric_values_from_counts
from rna_ccfa.selective_refiner import CATEGORIES, NUMERIC, extract_feature_rows

ROOT = Path(__file__).resolve().parents[1]
NORM = ROOT / "normalized/legacy121_v1/predictions.jsonl"
FOLDS = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
V1 = ROOT / "results/selective_refiner/v1"
V2 = ROOT / "results/selective_refiner/v2"
CONTRACT = ROOT / "results/selective_refiner/v2_protocol_audit/v2_feature_contract.json"
SEEDS = (17, 29, 41, 53, 67)
THRESHOLDS = (.50, .55, .60, .65, .70, .75, .80, .85, .90, .95)
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
CROSS_SYMMETRIC = (
    "exact_support_other_count", "any_other_exact_support", "all_three_exact_agreement",
    "endpoint_i_conflict_count", "endpoint_j_conflict_count", "any_partner_conflict",
    "local_inward_pair_support_count", "local_outward_pair_support_count",
    "strict_stem_supported_by_other_model", "fraction_source_stem_pairs_supported",
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
GPU_MODEL = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
torch.set_num_threads(1)
torch.set_num_interop_threads(1)


class Net(nn.Module):
    def __init__(self, n: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n, 64), nn.ReLU(), nn.Dropout(.10),
            nn.Linear(64, 64), nn.ReLU(), nn.Dropout(.10),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(1)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def load_data():
    records = {}
    predictions = defaultdict(dict)
    for line in NORM.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        source = record["source_model"]["name"]
        records[(record["rna_id"], source)] = record
        predictions[record["rna_id"]][source] = record["predicted_structure"]["pairs"]
    folds = {row["rna_id"]: int(row["fold"]) for row in csv.DictReader(FOLDS.open(encoding="utf-8"))}
    if len(records) != 363 or len(folds) != 121 or any(set(row) != set(SOURCES) for row in predictions.values()):
        raise AssertionError("Legacy121 v1 matrix/folds are incomplete")
    return records, predictions, folds


def base_vec(row, aware: bool) -> list[float]:
    values = [float(row.features[name]) for name in NUMERIC]
    for name, vocabulary in CATEGORIES.items():
        if name == "source_model" and not aware:
            continue
        value = row.features.get(name, "N/OTHER" if name.startswith("base") else "NONE")
        values.extend(float(value == category) for category in vocabulary)
        values.append(float(value not in vocabulary))
    return values


def build_examples(records, predictions):
    examples = []
    for (rna_id, source), record in sorted(records.items()):
        topology = extract_feature_rows(
            rna_id, record["sequence"], record["predicted_structure"]["pairs"],
            record["ground_truth_structure"]["pairs"], source, True,
        )
        for row in topology:
            cross = cross_model_agreement_features(
                source, row.pair, predictions[rna_id], sequence_length=len(record["sequence"]),
            )
            if cross != cross_model_agreement_features(
                source, row.pair, predictions[rna_id], sequence_length=len(record["sequence"]),
            ):
                raise AssertionError("cross-model feature extraction is nondeterministic")
            examples.append((row, cross))
    if len(examples) != 5290:
        raise AssertionError("v2 example count is not 5290")
    return examples


def choose_threshold(rows, scores):
    candidates = []
    tp = sum(row["label_delete"] == 0 for row in rows)
    for threshold in THRESHOLDS:
        deleted = [row for row, score in zip(rows, scores) if score >= threshold]
        harmful = sum(row["label_delete"] == 0 for row in deleted)
        delete_tp = sum(row["label_delete"] == 1 for row in deleted)
        delete_fp = harmful
        delete_fn = sum(row["label_delete"] == 1 for row in rows) - delete_tp
        _, _, delete_f1 = metric_values_from_counts(delete_tp, delete_fp, delete_fn)
        preservation = 1 - harmful / tp if tp else 1.0
        candidates.append((threshold, preservation, delete_f1, len(deleted)))
    eligible = [item for item in candidates if item[1] >= .99]
    if not eligible:
        return None
    return max(eligible, key=lambda item: (item[2], item[0], -item[3]))[0]


def topology_rows(records, ids):
    rows = []
    for (rna_id, source), record in sorted(records.items()):
        if rna_id not in ids:
            continue
        rows.extend({
            "rna_id": rna_id, "source_model": source, "i": pair.pair[0], "j": pair.pair[1],
            "label_delete": pair.label,
        } for pair in extract_feature_rows(
            rna_id, record["sequence"], record["predicted_structure"]["pairs"],
            record["ground_truth_structure"]["pairs"], source, True,
        ))
    return rows


def save_score_rows(path: Path, source_rows, scores, partition):
    write_csv(path, [
        {**row, "p_delete": float(score), "partition": partition}
        for row, score in zip(source_rows, scores)
    ])


def reconstruct_base(records, folds, aware: bool, base_name: str):
    output_root = V2 / "base_reconstructed" / ("POOLED_SOURCE_AWARE" if aware else "POOLED_SOURCE_AGNOSTIC")
    outputs = {}
    for fold_id in range(5):
        train_ids = {rna for rna, value in folds.items() if value not in (fold_id, (fold_id + 1) % 5)}
        validation_ids = {rna for rna, value in folds.items() if value == (fold_id + 1) % 5}
        test_ids = {rna for rna, value in folds.items() if value == fold_id}
        train_features = []
        for (rna_id, source), record in sorted(records.items()):
            train_features.extend(extract_feature_rows(
                rna_id, record["sequence"], record["predicted_structure"]["pairs"],
                record["ground_truth_structure"]["pairs"], source, True,
            ) if rna_id in train_ids else [])
        X = np.asarray([base_vec(row, aware) for row in train_features], dtype="float32")
        for seed in SEEDS:
            source_dir = output_root / f"fold_{fold_id}" / f"seed_{seed}"
            v1_dir = V1 / base_name / f"fold_{fold_id}" / f"seed_{seed}"
            config = json.loads((v1_dir / "config.json").read_text(encoding="utf-8"))
            checkpoint = torch.load(v1_dir / "checkpoint.pt", map_location="cpu", weights_only=False)
            model = Net(X.shape[1]); model.load_state_dict(checkpoint["model"]); model.eval()
            mean, std = np.asarray(checkpoint["mean"]), np.asarray(checkpoint["std"])
            validation_rows = topology_rows(records, validation_ids)
            test_rows = topology_rows(records, test_ids)
            validation_features = []
            test_features = []
            for row in validation_rows:
                record = records[(row["rna_id"], row["source_model"])]
                source_feature = next(x for x in extract_feature_rows(
                    row["rna_id"], record["sequence"], record["predicted_structure"]["pairs"],
                    record["ground_truth_structure"]["pairs"], row["source_model"], True
                ) if x.pair == (int(row["i"]), int(row["j"])))
                validation_features.append(base_vec(source_feature, aware))
            for row in test_rows:
                record = records[(row["rna_id"], row["source_model"])]
                source_feature = next(x for x in extract_feature_rows(
                    row["rna_id"], record["sequence"], record["predicted_structure"]["pairs"],
                    record["ground_truth_structure"]["pairs"], row["source_model"], True
                ) if x.pair == (int(row["i"]), int(row["j"])))
                test_features.append(base_vec(source_feature, aware))
            with torch.no_grad():
                validation_scores = torch.sigmoid(model(torch.tensor((np.asarray(validation_features) - mean) / std, dtype=torch.float32))).numpy()
                test_scores = torch.sigmoid(model(torch.tensor((np.asarray(test_features) - mean) / std, dtype=torch.float32))).numpy()
            global_threshold = choose_threshold(validation_rows, validation_scores)
            v1_threshold = json.loads((v1_dir / "selected_threshold.json").read_text(encoding="utf-8"))["threshold"]
            if global_threshold != v1_threshold:
                raise AssertionError(f"BASE global threshold mismatch: {base_name} fold {fold_id} seed {seed}")
            source_thresholds = {}
            for source in SOURCES:
                indices = [idx for idx, row in enumerate(validation_rows) if row["source_model"] == source]
                source_thresholds[source] = choose_threshold(
                    [validation_rows[idx] for idx in indices], validation_scores[indices]
                )
            source_dir.mkdir(parents=True, exist_ok=True)
            save_score_rows(source_dir / "validation_pair_scores.csv", validation_rows, validation_scores, "validation")
            save_score_rows(source_dir / "test_pair_scores.csv", test_rows, test_scores, "test")
            (source_dir / "global_threshold.json").write_text(json.dumps({
                "threshold": global_threshold, "status": "PASS" if global_threshold is not None else "ABSTAIN_NO_REFINEMENT",
                "validation_only": True, "v1_authoritative_threshold": v1_threshold,
            }, indent=2) + "\n")
            (source_dir / "source_conditional_thresholds.json").write_text(json.dumps({
                "thresholds": source_thresholds,
                "status": "PASS" if all(value is not None for value in source_thresholds.values()) else "ABSTAIN_NO_REFINEMENT",
                "validation_only": True,
            }, indent=2) + "\n")
            (source_dir / "config.json").write_text(json.dumps({
                "protocol_version": "selective_refiner_v2.0.1",
                "role": "AUTHORITATIVE_V1_BASE_RECONSTRUCTION",
                "source_v1_variant": base_name, "fold": fold_id, "seed": seed,
                "v1_checkpoint_sha256": hashlib.sha256((v1_dir / "checkpoint.pt").read_bytes()).hexdigest(),
                "train_pairs": len(train_features), "validation_pairs": len(validation_rows), "test_pairs": len(test_rows),
                "device": "cpu_reconstruction", "retrained": False,
            }, indent=2) + "\n")
            outputs[(fold_id, seed)] = source_dir
    return outputs


def train_cross(records, predictions, folds, aware: bool):
    variant = "CROSS_SOURCE_AWARE" if aware else "CROSS_SOURCE_AGNOSTIC"
    root = V2 / ("cross_source_aware" if aware else "cross_source_agnostic")
    examples = build_examples(records, predictions)
    feature_contract_hash = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    feature_hash = hashlib.sha256(json.dumps({"base_numeric": NUMERIC, "base_categories": CATEGORIES, "cross": CROSS_SYMMETRIC, "aware": aware}, sort_keys=True).encode()).hexdigest()
    outputs = {}
    for fold_id in range(5):
        train_ids = {rna for rna, value in folds.items() if value not in (fold_id, (fold_id + 1) % 5)}
        validation_ids = {rna for rna, value in folds.items() if value == (fold_id + 1) % 5}
        test_ids = {rna for rna, value in folds.items() if value == fold_id}
        train_examples = [item for item in examples if item[0].rna_id in train_ids]
        validation_examples = [item for item in examples if item[0].rna_id in validation_ids]
        test_examples = [item for item in examples if item[0].rna_id in test_ids]

        def vector(item):
            row, cross = item
            values = base_vec(row, aware)
            values.extend(float(cross[name]) for name in CROSS_SYMMETRIC)
            if aware:
                values.extend(float(cross[name]) for name in ("support_by_rnafold", "support_by_petfold", "support_by_trrosettarna2"))
            return values

        X = np.asarray([vector(item) for item in train_examples], dtype="float32")
        V = np.asarray([vector(item) for item in validation_examples], dtype="float32")
        T = np.asarray([vector(item) for item in test_examples], dtype="float32")
        y = np.asarray([item[0].label for item in train_examples], dtype="float32")
        yv = np.asarray([item[0].label for item in validation_examples], dtype="float32")
        mean, std = X.mean(axis=0), np.maximum(X.std(axis=0), 1e-8)
        X, V, T = (X - mean) / std, (V - mean) / std, (T - mean) / std
        validation_rows = [{
            "rna_id": item[0].rna_id, "source_model": item[0].source_model,
            "i": item[0].pair[0], "j": item[0].pair[1], "label_delete": item[0].label,
        } for item in validation_examples]
        test_rows = [{
            "rna_id": item[0].rna_id, "source_model": item[0].source_model,
            "i": item[0].pair[0], "j": item[0].pair[1], "label_delete": item[0].label,
        } for item in test_examples]
        for seed in SEEDS:
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
            model = Net(X.shape[1]).to(DEVICE)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
            loss_function = nn.BCEWithLogitsLoss(
                pos_weight=torch.tensor(float((y == 0).sum() / (y == 1).sum()), device=DEVICE)
            )
            tx, ty, vx = torch.tensor(X, device=DEVICE), torch.tensor(y, device=DEVICE), torch.tensor(V, device=DEVICE)
            best_key = None; best_state = None; best_epoch = None; patience = 0; curves = []
            for epoch in range(1, 101):
                model.train(); order = torch.randperm(len(tx), device=DEVICE); losses = []
                for start in range(0, len(order), 256):
                    batch = order[start:start + 256]; optimizer.zero_grad()
                    loss = loss_function(model(tx[batch]), ty[batch]); loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); optimizer.step(); losses.append(float(loss.detach().cpu()))
                model.eval()
                validation_scores = torch.sigmoid(model(vx)).detach().cpu().numpy()
                pseudo = [{"label_delete": int(label)} for label in yv]
                metrics = classification_metrics(pseudo, validation_scores, .5)
                harmful = sum(row["label_delete"] == 0 and score >= .5 for row, score in zip(validation_rows, validation_scores))
                tp = sum(row["label_delete"] == 0 for row in validation_rows)
                preservation = 1 - harmful / tp if tp else 1.0
                key = (metrics["delete_f1"], preservation, -epoch)
                curves.append({"epoch": epoch, "train_loss": statistics.fmean(losses), "validation_delete_f1": metrics["delete_f1"], "validation_preservation_at_0_5": preservation})
                if best_key is None or key > best_key:
                    best_key, best_state, best_epoch, patience = key, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}, epoch, 0
                else:
                    patience += 1
                if patience >= 12:
                    break
            model.load_state_dict(best_state); model.eval()
            with torch.no_grad():
                validation_scores = torch.sigmoid(model(torch.tensor(V, device=DEVICE))).detach().cpu().numpy()
                test_scores = torch.sigmoid(model(torch.tensor(T, device=DEVICE))).detach().cpu().numpy()
            global_threshold = choose_threshold(validation_rows, validation_scores)
            source_thresholds = {}
            for source in SOURCES:
                indices = [idx for idx, row in enumerate(validation_rows) if row["source_model"] == source]
                source_thresholds[source] = choose_threshold([validation_rows[idx] for idx in indices], validation_scores[indices])
            base = root / f"fold_{fold_id}" / f"seed_{seed}"; base.mkdir(parents=True, exist_ok=True)
            torch.save({"model": model.state_dict(), "mean": mean, "std": std, "feature_schema_hash": feature_hash}, base / "checkpoint.pt")
            save_score_rows(base / "validation_pair_scores.csv", validation_rows, validation_scores, "validation")
            save_score_rows(base / "test_pair_scores.csv", test_rows, test_scores, "test")
            write_csv(base / "train_ids.csv", [{"rna_id": value} for value in sorted(train_ids)])
            write_csv(base / "validation_ids.csv", [{"rna_id": value} for value in sorted(validation_ids)])
            write_csv(base / "test_ids.csv", [{"rna_id": value} for value in sorted(test_ids)])
            (base / "validation_curves.csv").write_text("epoch,train_loss,validation_delete_f1,validation_preservation_at_0_5\n" + "\n".join(
                f"{x['epoch']},{x['train_loss']},{x['validation_delete_f1']},{x['validation_preservation_at_0_5']}" for x in curves
            ) + "\n")
            (base / "global_threshold.json").write_text(json.dumps({
                "threshold": global_threshold, "status": "PASS" if global_threshold is not None else "ABSTAIN_NO_REFINEMENT", "validation_only": True,
            }, indent=2) + "\n")
            (base / "source_conditional_thresholds.json").write_text(json.dumps({
                "thresholds": source_thresholds, "status": "PASS" if all(value is not None for value in source_thresholds.values()) else "ABSTAIN_NO_REFINEMENT", "validation_only": True,
            }, indent=2) + "\n")
            (base / "config.json").write_text(json.dumps({
                "protocol_version": "selective_refiner_v2.0.1", "variant": variant, "fold": fold_id, "seed": seed,
                "feature_schema_hash": feature_hash, "feature_contract_hash": feature_contract_hash,
                "train_keep": int((y == 0).sum()), "train_delete": int((y == 1).sum()),
                "pos_weight": float((y == 0).sum() / (y == 1).sum()), "lr": 1e-3, "weight_decay": 1e-4,
                "batch_size": 256, "max_epochs": 100, "patience": 12, "gradient_clip": 5.0,
                "selected_checkpoint_epoch": best_epoch, "device": str(DEVICE), "gpu_model": GPU_MODEL,
                "cuda_version": torch.version.cuda, "pytorch_version": torch.__version__,
            }, indent=2) + "\n")
            outputs[(fold_id, seed)] = base
    return outputs


def classification_metrics(rows, scores, threshold):
    labels = np.asarray([int(row["label_delete"]) for row in rows])
    predicted = np.asarray(scores) >= threshold
    tp = int(((labels == 1) & predicted).sum()); fp = int(((labels == 0) & predicted).sum()); fn = int(((labels == 1) & ~predicted).sum())
    precision, recall, f1 = metric_values_from_counts(tp, fp, fn)
    return {"delete_precision": precision, "delete_recall": recall, "delete_f1": f1, "tp": tp, "fp": fp, "fn": fn}


def evaluate_structure(score_rows, records, thresholds):
    grouped = defaultdict(list)
    for row in score_rows:
        grouped[(row["rna_id"], row["source_model"])].append(row)
    per_rna = []; before_counts = [0, 0, 0]; after_counts = [0, 0, 0]; beneficial = harmful = modified = modified_rnas = 0
    for key, rows in grouped.items():
        record = records[key]; original = {tuple(pair) for pair in record["predicted_structure"]["pairs"]}; gt = {tuple(pair) for pair in record["ground_truth_structure"]["pairs"]}
        threshold = thresholds.get(key[1]); deleted = set() if threshold is None else {(int(row["i"]), int(row["j"])) for row in rows if float(row["p_delete"]) >= threshold}
        refined = original - deleted; before = (len(original & gt), len(original - gt), len(gt - original)); after = (len(refined & gt), len(refined - gt), len(gt - refined))
        b = len(deleted & (original - gt)); h = len(deleted & gt)
        if b + h != len(deleted) or after[0] != before[0] - h or after[1] != before[1] - b or after[2] != before[2] + h:
            raise AssertionError("v2 deletion accounting identity failed")
        for idx in range(3): before_counts[idx] += before[idx]; after_counts[idx] += after[idx]
        beneficial += b; harmful += h; modified += len(deleted); modified_rnas += bool(deleted)
        _, _, f_before = metric_values_from_counts(*before); _, _, f_after = metric_values_from_counts(*after)
        per_rna.append({"rna_id": key[0], "source_model": key[1], "original_pairs": sorted(original), "refined_pairs": sorted(refined), "original_f1": f_before, "refined_f1": f_after, "delta_f1": f_after - f_before, "beneficial_edits": b, "harmful_edits": h, "modified_pairs": len(deleted), "tp_before": before[0], "tp_after": after[0], "fp_before": before[1], "fp_after": after[1], "fn_before": before[2], "fn_after": after[2]})
    _, _, original_f1 = metric_values_from_counts(*before_counts); p, r, f1 = metric_values_from_counts(*after_counts)
    return {"macro_delta_f1": statistics.fmean(row["delta_f1"] for row in per_rna), "micro_delta_f1": f1 - original_f1, "modification_precision": beneficial / (beneficial + harmful) if beneficial + harmful else None, "delete_recall": beneficial / before_counts[1] if before_counts[1] else 0.0, "correct_pair_preservation": after_counts[0] / before_counts[0] if before_counts[0] else 1.0, "modified_pair_count": modified, "modified_rna_count": modified_rnas, "eligible_rna_count": len(per_rna), "beneficial_edit_count": beneficial, "harmful_edit_count": harmful, "original_tp_count": before_counts[0], "original_fp_count": before_counts[1], "original_fn_count": before_counts[2], "tp_after_count": after_counts[0], "fp_after_count": after_counts[1], "fn_after_count": after_counts[2], "per_rna": per_rna}


def aggregate_outcomes(rows):
    """Apply the frozen v2.0.1 aggregation semantics."""
    beneficial = sum(int(row["beneficial_edit_count"]) for row in rows)
    harmful = sum(int(row["harmful_edit_count"]) for row in rows)
    tp_before = sum(int(row["original_tp_count"]) for row in rows)
    tp_after = sum(int(row["tp_after_count"]) for row in rows)
    fp_before = sum(int(row["original_fp_count"]) for row in rows)
    return {"modification_precision": beneficial / (beneficial + harmful) if beneficial + harmful else None, "delete_recall": beneficial / fp_before if fp_before else 0.0, "correct_pair_preservation": tp_after / tp_before if tp_before else 1.0, "macro_delta_f1": statistics.fmean(float(row["macro_delta_f1"]) for row in rows), "micro_delta_f1": statistics.fmean(float(row["micro_delta_f1"]) for row in rows), "modified_pair_count": sum(int(row["modified_pair_count"]) for row in rows), "modified_rna_count": sum(int(row["modified_rna_count"]) for row in rows), "eligible_rna_count": sum(int(row["eligible_rna_count"]) for row in rows), "beneficial_edit_count": beneficial, "harmful_edit_count": harmful, "original_tp_count": tp_before, "tp_after_count": tp_after, "original_fp_count": fp_before}


def run_factorial(records, base_outputs, cross_outputs):
    conditions = {
        "V2A_BASE_SOURCE_AGNOSTIC_GLOBAL": ("base_agnostic", "global"),
        "V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL": ("cross_agnostic", "global"),
        "V2A_BASE_SOURCE_AWARE_GLOBAL": ("base_aware", "global"),
        "V2A_CROSS_SOURCE_AWARE_GLOBAL": ("cross_aware", "global"),
        "V2B_BASE_SOURCE_AGNOSTIC_SOURCE_CONDITIONAL": ("base_agnostic", "source"),
        "V2B_CROSS_SOURCE_AGNOSTIC_SOURCE_CONDITIONAL": ("cross_agnostic", "source"),
        "V2B_BASE_SOURCE_AWARE_SOURCE_CONDITIONAL": ("base_aware", "source"),
        "V2B_CROSS_SOURCE_AWARE_SOURCE_CONDITIONAL": ("cross_aware", "source"),
    }
    source_map = {"base_agnostic": base_outputs[False], "base_aware": base_outputs[True], "cross_agnostic": cross_outputs[False], "cross_aware": cross_outputs[True]}
    rows = []; pair_rows = []; source_metric_rows = []
    for condition, (kind, calibration) in conditions.items():
        for fold_id in range(5):
            for seed in SEEDS:
                base = source_map[kind][(fold_id, seed)]
                scores = list(csv.DictReader((base / "test_pair_scores.csv").open(encoding="utf-8")))
                if calibration == "global":
                    payload = json.loads((base / "global_threshold.json").read_text(encoding="utf-8")); threshold = payload["threshold"]
                    thresholds = {source: threshold for source in SOURCES}; deployable = threshold is not None
                else:
                    payload = json.loads((base / "source_conditional_thresholds.json").read_text(encoding="utf-8")); thresholds = payload["thresholds"]; deployable = all(value is not None for value in thresholds.values())
                    if not deployable: thresholds = {source: None for source in SOURCES}
                outcome = evaluate_structure(scores, records, thresholds)
                c = classification_metrics(scores, [float(row["p_delete"]) for row in scores], .5 if calibration == "global" else .5)
                outcome_row = {k: v for k, v in outcome.items() if k != "per_rna"}
                rows.append({"condition": condition, "scope": "pooled", "source_model": "ALL", "fold": fold_id, "seed": seed, "deployable": deployable, "deployment_status": "APPLY_THRESHOLD" if deployable else "ABSTAIN_NO_REFINEMENT", "global_or_source_thresholds": json.dumps(thresholds, sort_keys=True), **outcome_row})
                outdir = V2 / "factorial_evaluation" / condition / f"fold_{fold_id}" / f"seed_{seed}"; outdir.mkdir(parents=True, exist_ok=True)
                detailed = evaluate_structure(scores, records, thresholds)
                (outdir / "per_rna_edited_structures.jsonl").write_text("".join(json.dumps(x) + "\n" for x in detailed["per_rna"]))
                (outdir / "metrics.json").write_text(json.dumps({"condition": condition, "fold": fold_id, "seed": seed, "deployable": deployable, **outcome}, indent=2) + "\n")
                pair_rows.append({"condition": condition, "fold": fold_id, "seed": seed, **c})
                for source in SOURCES:
                    source_outcome = evaluate_structure([row for row in scores if row["source_model"] == source], records, {source: thresholds[source]})
                    source_metric_rows.append({"condition": condition, "scope": "source", "source_model": source, "fold": fold_id, "seed": seed, "deployable": deployable, **{k: v for k, v in source_outcome.items() if k != "per_rna"}})
    summary = V2 / "summary"; summary.mkdir(parents=True, exist_ok=True)
    write_csv(summary / "factorial_metrics.csv", rows); write_csv(summary / "pair_classification_metrics.csv", pair_rows)
    write_csv(summary / "metrics_by_source.csv", source_metric_rows)
    return rows, source_metric_rows


def summarize_gate(rows, source_rows):
    def subset(condition): return [row for row in rows if row["condition"] == condition]
    primary = subset("V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL"); base = subset("V2A_BASE_SOURCE_AGNOSTIC_GLOBAL")
    if len(primary) != 25 or len(base) != 25: raise AssertionError("primary/base factorial outcomes incomplete")
    primary_metrics = aggregate_outcomes(primary); base_metrics = aggregate_outcomes(base)
    paired_macro = statistics.fmean(float(c["macro_delta_f1"]) - float(b["macro_delta_f1"]) for c, b in zip(primary, base))
    paired_micro = statistics.fmean(float(c["micro_delta_f1"]) - float(b["micro_delta_f1"]) for c, b in zip(primary, base))
    paired_pres = statistics.fmean(float(c["correct_pair_preservation"]) - float(b["correct_pair_preservation"]) for c, b in zip(primary, base))
    source_aggregates = {}
    for source in SOURCES:
        cr = [r for r in source_rows if r["condition"] == "V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL" and r["source_model"] == source]
        br = [r for r in source_rows if r["condition"] == "V2A_BASE_SOURCE_AGNOSTIC_GLOBAL" and r["source_model"] == source]
        if len(cr) != 25 or len(br) != 25: raise AssertionError("source outcomes incomplete")
        source_aggregates[source] = {"cross": aggregate_outcomes(cr), "base": aggregate_outcomes(br)}
    positive_sources = sum(x["cross"]["macro_delta_f1"] > 0 and x["cross"]["micro_delta_f1"] > 0 for x in source_aggregates.values())
    useful_sources = sum(x["cross"]["modified_rna_count"] / x["cross"]["eligible_rna_count"] >= .10 for x in source_aggregates.values())
    non_trrosetta = any(
        source_aggregates[s]["cross"]["macro_delta_f1"] > 0 and source_aggregates[s]["cross"]["micro_delta_f1"] > 0
        and source_aggregates[s]["cross"]["macro_delta_f1"] > source_aggregates[s]["base"]["macro_delta_f1"]
        and source_aggregates[s]["cross"]["micro_delta_f1"] > source_aggregates[s]["base"]["micro_delta_f1"]
        for s in SOURCES[:2]
    )
    criteria = {
        "cross_threshold_deployability_25_of_25": all(bool(row["deployable"]) for row in primary),
        "pooled_modification_precision": primary_metrics["modification_precision"] is not None and primary_metrics["modification_precision"] >= .80,
        "pooled_delete_recall": primary_metrics["delete_recall"] >= .10,
        "pooled_preservation": primary_metrics["correct_pair_preservation"] >= .99,
        "per_source_preservation": all(x["cross"]["correct_pair_preservation"] >= .98 for x in source_aggregates.values()),
        "positive_macro_and_micro_for_at_least_two_sources": positive_sources >= 2,
        "useful_source_fraction_for_all_sources": useful_sources == 3,
        "paired_macro_gain": paired_macro > 0, "paired_micro_gain": paired_micro > 0,
        "precision_gain": primary_metrics["modification_precision"] is not None and base_metrics["modification_precision"] is not None and primary_metrics["modification_precision"] - base_metrics["modification_precision"] >= .02,
        "preservation_gain": paired_pres >= .002,
        "delete_recall_drop": primary_metrics["delete_recall"] - base_metrics["delete_recall"] >= -.02,
        "non_trrosetta_improvement": non_trrosetta,
        "no_catastrophic_degradation": all(
            x["cross"]["macro_delta_f1"] >= -.005 and x["cross"]["micro_delta_f1"] >= -.005
            and x["cross"]["correct_pair_preservation"] >= .98
            and x["cross"]["macro_delta_f1"] - x["base"]["macro_delta_f1"] >= -.005
            and x["cross"]["micro_delta_f1"] - x["base"]["micro_delta_f1"] >= -.005
            for x in source_aggregates.values()),
    }
    decision = "V2_DEVELOPMENT_GATE_PASS" if all(criteria.values()) else "V2_DEVELOPMENT_GATE_FAIL"
    payload = {"protocol_version": "selective_refiner_v2.0.1", "primary_condition": "V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL", "matched_baseline": "V2A_BASE_SOURCE_AGNOSTIC_GLOBAL", "decision": decision, "criteria": criteria, "primary_metrics": primary_metrics, "base_metrics": base_metrics, "source_aggregates": source_aggregates, "paired_mean_macro_delta_f1_gain": paired_macro, "paired_mean_micro_delta_f1_gain": paired_micro, "paired_mean_preservation_gain": paired_pres, "external77_evaluated": False, "v2_training_runs": 50}
    (V2 / "summary/primary_gate_metrics.json").write_text(json.dumps(payload, indent=2) + "\n")
    (V2 / "summary/primary_gate_decision.json").write_text(json.dumps({"decision": decision, "external77_evaluated": False}, indent=2) + "\n")
    return payload


def main():
    records, predictions, folds = load_data(); V2.mkdir(parents=True, exist_ok=True)
    base_outputs = {False: reconstruct_base(records, folds, False, "POOLED_SOURCE_AGNOSTIC"), True: reconstruct_base(records, folds, True, "POOLED_SOURCE_AWARE")}
    cross_outputs = {False: train_cross(records, predictions, folds, False), True: train_cross(records, predictions, folds, True)}
    rows, source_rows = run_factorial(records, base_outputs, cross_outputs); gate = summarize_gate(rows, source_rows)
    (V2 / "summary/training_run_summary.csv").write_text("variant,new_training_runs,failed_runs,device,gpu_model,cuda_version,pytorch_version\n" + "\n".join([
        f"CROSS_SOURCE_AGNOSTIC,25,0,{DEVICE},{GPU_MODEL},{torch.version.cuda},{torch.__version__}",
        f"CROSS_SOURCE_AWARE,25,0,{DEVICE},{GPU_MODEL},{torch.version.cuda},{torch.__version__}",
    ]) + "\n")
    print(json.dumps({"new_cross_training_runs": 50, "failed_runs": 0, "factorial_outcomes": len(rows), "device": str(DEVICE), "gate": gate["decision"], "external77_evaluated": False}, indent=2))


if __name__ == "__main__": main()
