#!/usr/bin/env python3
"""Audit the immutable v1 pooled BASE artifacts before v2 training."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from rna_ccfa.metrics import metric_values_from_counts
from rna_ccfa.selective_refiner import CATEGORIES, NUMERIC, extract_feature_rows

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "results/selective_refiner/v1"
NORM = ROOT / "normalized/legacy121_v1/predictions.jsonl"
FOLDS = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
OUT = ROOT / "results/selective_refiner/v2_protocol_audit"
SEEDS = (17, 29, 41, 53, 67)
VARIANTS = ("POOLED_SOURCE_AGNOSTIC", "POOLED_SOURCE_AWARE")
THRESHOLDS = (.5, .55, .6, .65, .7, .75, .8, .85, .9, .95)


class Net(torch.nn.Module):
    def __init__(self, n: int):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(n, 64), torch.nn.ReLU(), torch.nn.Dropout(.1),
            torch.nn.Linear(64, 64), torch.nn.ReLU(), torch.nn.Dropout(.1),
            torch.nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(1)


def vec(row, aware: bool) -> list[float]:
    values = [float(row.features[name]) for name in NUMERIC]
    for name, vocabulary in CATEGORIES.items():
        if name == "source_model" and not aware:
            continue
        value = row.features.get(name, "N/OTHER" if name.startswith("base") else "NONE")
        values.extend(float(value == category) for category in vocabulary)
        values.append(float(value not in vocabulary))
    return values


def select_threshold(rows, scores):
    candidates = []
    tp = sum(row.label == 0 for row in rows)
    for threshold in THRESHOLDS:
        deleted = [row for row, score in zip(rows, scores) if score >= threshold]
        harmful = sum(row.label == 0 for row in deleted)
        metric = metric_values_from_counts(
            sum(row.label == 1 for row in deleted),
            sum(row.label == 0 for row in deleted),
            sum(row.label == 1 for row in rows) - sum(row.label == 1 for row in deleted),
        )[2]
        candidates.append((threshold, 1 - harmful / tp if tp else 1., metric, len(deleted)))
    eligible = [item for item in candidates if item[1] >= .99]
    return max(eligible, key=lambda item: (item[2], item[0], -item[3]))[0] if eligible else None


def main() -> None:
    records = {}
    for line in NORM.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        records[(record["rna_id"], record["source_model"]["name"])] = record
    fold = {row["rna_id"]: int(row["fold"]) for row in csv.DictReader(FOLDS.open(encoding="utf-8"))}
    expected_hash = hashlib.sha256(json.dumps({"numeric": NUMERIC, "categories": CATEGORIES}, sort_keys=True).encode()).hexdigest()
    results = []
    for variant in VARIANTS:
        aware = variant == "POOLED_SOURCE_AWARE"
        for fold_id in range(5):
            train_ids = {rna for rna, value in fold.items() if value not in (fold_id, (fold_id + 1) % 5)}
            validation_ids = {rna for rna, value in fold.items() if value == (fold_id + 1) % 5}
            test_ids = {rna for rna, value in fold.items() if value == fold_id}
            for seed in SEEDS:
                base = V1 / variant / f"fold_{fold_id}" / f"seed_{seed}"
                config = json.loads((base / "config.json").read_text(encoding="utf-8"))
                required = {
                    "lr": 1e-3, "weight_decay": 1e-4, "batch_size": 256,
                    "max_epochs": 100, "patience": 12, "gradient_clip": 5.0,
                    "feature_schema_hash": expected_hash,
                }
                for key, value in required.items():
                    if config.get(key) != value:
                        raise AssertionError(f"{variant} fold {fold_id} seed {seed}: bad {key}")
                if config["fold"] != fold_id or config["seed"] != seed:
                    raise AssertionError("config fold/seed mismatch")
                for filename in ("checkpoint.pt", "per_pair_scores.csv", "selected_threshold.json"):
                    if not (base / filename).is_file():
                        raise FileNotFoundError(base / filename)
                checkpoint = torch.load(base / "checkpoint.pt", map_location="cpu", weights_only=False)
                if checkpoint["feature_schema_hash"] != expected_hash:
                    raise AssertionError("checkpoint feature schema mismatch")
                train = []
                validation = []
                test = []
                for (rna_id, source), record in records.items():
                    rows = extract_feature_rows(
                        rna_id, record["sequence"], record["predicted_structure"]["pairs"],
                        record["ground_truth_structure"]["pairs"], source, True,
                    )
                    train.extend(row for row in rows if rna_id in train_ids)
                    validation.extend(row for row in rows if rna_id in validation_ids)
                    test.extend(row for row in rows if rna_id in test_ids)
                X = np.asarray([vec(row, aware) for row in train], dtype="float32")
                V = np.asarray([vec(row, aware) for row in validation], dtype="float32")
                T = np.asarray([vec(row, aware) for row in test], dtype="float32")
                mean, std = np.asarray(checkpoint["mean"]), np.asarray(checkpoint["std"])
                if np.any(std <= 0) or mean.shape != (X.shape[1],) or std.shape != (X.shape[1],):
                    raise AssertionError("invalid serialized preprocessing statistics")
                model = Net(X.shape[1]); model.load_state_dict(checkpoint["model"]); model.eval()
                with torch.no_grad():
                    validation_scores = torch.sigmoid(model(torch.tensor((V - mean) / std))).numpy()
                    test_scores = torch.sigmoid(model(torch.tensor((T - mean) / std))).numpy()
                if len(validation_scores) != len(validation) or not np.isfinite(validation_scores).all():
                    raise AssertionError("validation probabilities cannot be reconstructed")
                expected_threshold = select_threshold(validation, validation_scores)
                selected = json.loads((base / "selected_threshold.json").read_text(encoding="utf-8"))["threshold"]
                if expected_threshold != selected:
                    raise AssertionError(f"threshold mismatch at {variant} fold {fold_id} seed {seed}: {expected_threshold} != {selected}")
                test_score_rows = list(csv.DictReader((base / "per_pair_scores.csv").open(encoding="utf-8")))
                if len(test_score_rows) != len(test) or len(test_scores) != len(test):
                    raise AssertionError("test score artifact length mismatch")
                results.append({
                    "variant": variant, "fold": fold_id, "seed": seed,
                    "train_pairs": len(train), "validation_pairs": len(validation), "test_pairs": len(test),
                    "selected_threshold": selected,
                    "status": "PASS" if selected is not None else "BASE_ABSTAIN_REFERENCE",
                })
    if len(results) != 50:
        raise AssertionError("expected 50 audited pooled BASE runs")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "v1_base_artifact_audit.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(results)
    (OUT / "v1_base_artifact_audit.json").write_text(json.dumps({
        "audited_runs": len(results), "failed_runs": 0,
        "validation_probabilities_reconstructed": True,
        "thresholds_reconstructed_exactly": True,
        "external77_accessed": False,
    }, indent=2) + "\n")
    print(json.dumps({"audited_runs": len(results), "failed_runs": 0, "validation_reconstruction": "PASS"}, indent=2))


if __name__ == "__main__": main()
