#!/usr/bin/env python3
"""Analyze Legacy121 pair sequence separation without changing pair semantics."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

import numpy as np

from rna_ccfa.metrics import metric_values_from_counts
from rna_ccfa.separation import (
    LEGACY121_RELATIVE_THRESHOLDS,
    LEGACY121_SEPARATION_BINS,
    assign_legacy121_separation_bin,
    pair_separation,
)


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
PARTITIONS = ROOT / "results/baseline_legacy121_v1/pair_partitions.jsonl"
PAIR_ERRORS = ROOT / "results/error_analysis/pair_errors.csv"
STEM_EVENTS = ROOT / "results/error_analysis/stem_error_events.jsonl"
OUTPUT = ROOT / "results/error_analysis"
MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")
EXPECTED_COUNTS = {
    "rnafold": (1473, 220, 203),
    "petfold": (1463, 241, 213),
    "trrosettarna2_native_ss": (1461, 432, 215),
}
QUANTILES = (0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 1.0)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _model(record: dict[str, Any]) -> str:
    value = record["source_model"]
    return value["name"] if isinstance(value, dict) else value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quantile_summary(values: list[float | int]) -> dict[str, float]:
    labels = ("min", "q10", "q25", "median", "q75", "q90", "q95", "max")
    return {
        label: float(np.quantile(values, quantile, method="linear"))
        for label, quantile in zip(labels, QUANTILES)
    }


def _candidate_bins(
    items: list[dict[str, Any]],
    *,
    variable: str,
    thresholds: Iterable[float],
) -> list[dict[str, Any]]:
    bounds = list(thresholds)
    result = []
    lower = None
    for index, upper in enumerate(bounds + [None]):
        selected = [
            item
            for item in items
            if (lower is None or item[variable] > lower)
            and (upper is None or item[variable] <= upper)
        ]
        result.append(
            {
                "bin_index": index,
                "lower_exclusive": lower,
                "upper_inclusive": upper,
                "gt_pair_count": len(selected),
                "rna_count": len({item["rna_id"] for item in selected}),
            }
        )
        lower = upper
    return result


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _load_inputs() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    records = _read_jsonl(NORMALIZED)
    partitions = {row["record_id"]: row for row in _read_jsonl(PARTITIONS)}
    if len(records) != 363 or len(partitions) != 363:
        raise RuntimeError("expected 363 normalized records and pair partitions")
    if {row["record_id"] for row in records} != set(partitions):
        raise RuntimeError("normalized records and pair partitions differ")
    return records, partitions


def _build_pair_inventory(
    records: list[dict[str, Any]], partitions: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, tuple[int, tuple[tuple[int, int], ...]]]]:
    rows: list[dict[str, Any]] = []
    unique_gt: dict[str, tuple[int, tuple[tuple[int, int], ...]]] = {}
    for record in sorted(records, key=lambda item: item["record_id"]):
        record_id = record["record_id"]
        part = partitions[record_id]
        model = _model(record)
        if part["source_model"] != model or part["rna_id"] != record["rna_id"]:
            raise RuntimeError(f"partition provenance mismatch for {record_id}")
        length = int(record["metadata"]["sequence_length"])
        gt = tuple(tuple(pair) for pair in record["ground_truth_structure"]["pairs"])
        predicted = tuple(tuple(pair) for pair in record["predicted_structure"]["pairs"])
        tp = {tuple(pair) for pair in part["true_positive_pairs"]}
        fp = {tuple(pair) for pair in part["false_positive_pairs"]}
        fn = {tuple(pair) for pair in part["false_negative_pairs"]}
        if set(gt) != tp | fn or set(predicted) != tp | fp:
            raise RuntimeError(f"frozen partition identity failed for {record_id}")
        signature = (length, tuple(sorted(gt)))
        previous = unique_gt.setdefault(record["rna_id"], signature)
        if previous != signature:
            raise RuntimeError(f"GT differs among predictors for {record['rna_id']}")
        base = {
            "record_id": record_id,
            "rna_id": record["rna_id"],
            "source_model": model,
            "sequence_length": length,
        }
        for role, pairs, positive, negative in (
            ("ground_truth", gt, tp, fn),
            ("prediction", predicted, tp, fp),
        ):
            for pair in sorted(pairs):
                status = "TP" if pair in positive else ("FN" if pair in negative and role == "ground_truth" else "FP")
                separation = pair_separation(pair, length)
                rows.append(
                    {
                        **base,
                        "pair_role": role,
                        "pair_status": status,
                        "i": pair[0],
                        "j": pair[1],
                        "sequence_separation": separation.sequence_separation,
                        "relative_separation": separation.relative_separation,
                        "separation_bin": assign_legacy121_separation_bin(
                            separation.relative_separation
                        ),
                    }
                )
    if len(unique_gt) != 121:
        raise RuntimeError(f"expected 121 unique GT structures, got {len(unique_gt)}")
    return rows, unique_gt


def _gt_distribution(
    unique_gt: dict[str, tuple[int, tuple[tuple[int, int], ...]]]
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for rna_id, (length, pairs) in sorted(unique_gt.items()):
        for pair in pairs:
            separation = pair_separation(pair, length)
            items.append(
                {
                    "rna_id": rna_id,
                    "sequence_length": length,
                    "sequence_separation": separation.sequence_separation,
                    "relative_separation": separation.relative_separation,
                }
            )
    raw = [item["sequence_separation"] for item in items]
    relative = [item["relative_separation"] for item in items]
    raw_thresholds = [float(np.quantile(raw, q, method="linear")) for q in (0.25, 0.5, 0.75, 0.9)]
    relative_thresholds = [float(np.quantile(relative, q, method="linear")) for q in (0.25, 0.5, 0.75, 0.9)]
    if tuple(relative_thresholds) != LEGACY121_RELATIVE_THRESHOLDS:
        raise RuntimeError("GT relative quantiles differ from the frozen bin constants")
    long_range = [item for item in items if item["relative_separation"] > relative_thresholds[-1]]
    hybrid_long = [
        item
        for item in items
        if item["relative_separation"] > relative_thresholds[-1]
        and item["sequence_separation"] > raw_thresholds[1]
    ]
    return {
        "dataset": "legacy121_v1",
        "normalized_input_path": str(NORMALIZED.relative_to(ROOT)),
        "normalized_input_sha256": _sha256(NORMALIZED),
        "unique_rna_count": len(unique_gt),
        "gt_pair_count": len(items),
        "quantile_method": "numpy_linear",
        "raw_sequence_separation": _quantile_summary(raw),
        "relative_separation": _quantile_summary(relative),
        "candidate_binning_strategies": {
            "raw_gt_quantiles": {
                "threshold_quantiles": [0.25, 0.5, 0.75, 0.9],
                "thresholds": raw_thresholds,
                "bins": _candidate_bins(
                    items, variable="sequence_separation", thresholds=raw_thresholds
                ),
            },
            "relative_gt_quantiles": {
                "threshold_quantiles": [0.25, 0.5, 0.75, 0.9],
                "thresholds": relative_thresholds,
                "bins": _candidate_bins(
                    items, variable="relative_separation", thresholds=relative_thresholds
                ),
            },
            "hybrid_relative_q90_and_raw_q50_long_range": {
                "relative_threshold_exclusive": relative_thresholds[-1],
                "raw_threshold_exclusive": raw_thresholds[1],
                "gt_pair_count": len(hybrid_long),
                "gt_pair_fraction": len(hybrid_long) / len(items),
                "rna_count": len({item["rna_id"] for item in hybrid_long}),
            },
        },
        "chosen_protocol": {
            "primary_variable": "relative_separation",
            "threshold_quantiles": [0.25, 0.5, 0.75, 0.9],
            "thresholds": relative_thresholds,
            "bin_labels": list(LEGACY121_SEPARATION_BINS),
            "boundary_rule": "lower_exclusive_upper_inclusive; final bin is > q90",
            "long_range_definition": "relative_separation > GT-only Q90",
            "long_range_threshold_exclusive": relative_thresholds[-1],
            "long_range_gt_pair_count": len(long_range),
            "long_range_gt_pair_fraction": len(long_range) / len(items),
            "long_range_rna_count": len({item["rna_id"] for item in long_range}),
        },
    }


def _pair_error_summary(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for model in MODELS:
        model_rows = [row for row in inventory if row["source_model"] == model]
        total_fp = sum(row["pair_role"] == "prediction" and row["pair_status"] == "FP" for row in model_rows)
        total_fn = sum(row["pair_role"] == "ground_truth" and row["pair_status"] == "FN" for row in model_rows)
        totals = Counter()
        for label in LEGACY121_SEPARATION_BINS:
            rows = [row for row in model_rows if row["separation_bin"] == label]
            gt_rows = [row for row in rows if row["pair_role"] == "ground_truth"]
            pred_rows = [row for row in rows if row["pair_role"] == "prediction"]
            tp = sum(row["pair_status"] == "TP" for row in gt_rows)
            fp = sum(row["pair_status"] == "FP" for row in pred_rows)
            fn = sum(row["pair_status"] == "FN" for row in gt_rows)
            precision, recall, f1 = metric_values_from_counts(tp, fp, fn)
            totals.update({"tp": tp, "fp": fp, "fn": fn})
            result.append(
                {
                    "source_model": model,
                    "separation_bin": label,
                    "gt_pair_count": len(gt_rows),
                    "predicted_pair_count": len(pred_rows),
                    "tp_count": tp,
                    "fp_count": fp,
                    "fn_count": fn,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "fp_fraction_within_model": fp / total_fp if total_fp else 0.0,
                    "fn_fraction_within_model": fn / total_fn if total_fn else 0.0,
                }
            )
        if (totals["tp"], totals["fp"], totals["fn"]) != EXPECTED_COUNTS[model]:
            raise RuntimeError(f"frozen TP/FP/FN regression failed for {model}: {totals}")
    return result


def _wrong_partner_summary(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relation: dict[tuple[str, int, int], bool] = {}
    with PAIR_ERRORS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["error_type"] == "false_positive_pair":
                relation[(row["record_id"], int(row["i"]), int(row["j"]))] = row[
                    "wrong_partner"
                ].lower() == "true"
    fp_rows = [
        row
        for row in inventory
        if row["pair_role"] == "prediction" and row["pair_status"] == "FP"
    ]
    if len(relation) != len(fp_rows):
        raise RuntimeError("FP relation map does not cover the frozen FP inventory")
    result = []
    for model in MODELS:
        rows = [row for row in fp_rows if row["source_model"] == model]
        total_wrong = sum(relation[(row["record_id"], row["i"], row["j"])] for row in rows)
        total_pure = len(rows) - total_wrong
        for label in LEGACY121_SEPARATION_BINS:
            selected = [row for row in rows if row["separation_bin"] == label]
            wrong = sum(
                relation[(row["record_id"], row["i"], row["j"])] for row in selected
            )
            pure = len(selected) - wrong
            result.append(
                {
                    "source_model": model,
                    "separation_bin": label,
                    "false_positive_pair_count": len(selected),
                    "wrong_partner_count": wrong,
                    "pure_false_positive_count": pure,
                    "wrong_partner_fraction_within_bin_fp": wrong / len(selected)
                    if selected
                    else 0.0,
                    "wrong_partner_fraction_within_model_wrong_partner": wrong / total_wrong
                    if total_wrong
                    else 0.0,
                    "pure_fp_fraction_within_model_pure_fp": pure / total_pure
                    if total_pure
                    else 0.0,
                }
            )
    return result


def _stem_profile(stem: dict[str, Any], length: int) -> tuple[float, float, int]:
    values = [pair_separation(tuple(pair), length) for pair in stem["pairs"]]
    return (
        float(median(item.sequence_separation for item in values)),
        float(median(item.relative_separation for item in values)),
        len(values),
    )


def _stem_separation_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lengths = {record["record_id"]: int(record["metadata"]["sequence_length"]) for record in records}
    values: defaultdict[tuple[str, str, str], list[tuple[float, float, int]]] = defaultdict(list)
    for event in _read_jsonl(STEM_EVENTS):
        model = event["source_model"]
        length = lengths[event["record_id"]]
        for match in event["isolated_matches"]:
            state = (
                "isolated_complex_mismatch"
                if match["state"] == "complex_mismatch"
                else match["state"]
            )
            values[(model, state, "ground_truth")].append(
                _stem_profile(match["gt_stem"], length)
            )
            values[(model, state, "prediction")].append(
                _stem_profile(match["predicted_stem"], length)
            )
        for stem in event["missing_gt_stems"]:
            values[(model, "stem_missing", "ground_truth")].append(
                _stem_profile(stem, length)
            )
        for stem in event["unmatched_predicted_stems"]:
            values[(model, "unmatched_predicted_stem", "prediction")].append(
                _stem_profile(stem, length)
            )
    result = []
    for (model, state, role), profiles in sorted(values.items()):
        raw = [profile[0] for profile in profiles]
        relative = [profile[1] for profile in profiles]
        result.append(
            {
                "source_model": model,
                "stem_state": state,
                "structure_role": role,
                "stem_count": len(profiles),
                "stem_pair_count": sum(profile[2] for profile in profiles),
                "mean_stem_median_sequence_separation": mean(raw),
                "median_stem_median_sequence_separation": median(raw),
                "min_stem_median_sequence_separation": min(raw),
                "max_stem_median_sequence_separation": max(raw),
                "mean_stem_median_relative_separation": mean(relative),
                "median_stem_median_relative_separation": median(relative),
                "min_stem_median_relative_separation": min(relative),
                "max_stem_median_relative_separation": max(relative),
            }
        )
    return result


def main() -> None:
    records, partitions = _load_inputs()
    inventory, unique_gt = _build_pair_inventory(records, partitions)
    distribution = _gt_distribution(unique_gt)
    pair_summary = _pair_error_summary(inventory)
    wrong_summary = _wrong_partner_summary(inventory)
    stem_summary = _stem_separation_summary(records)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    _write_csv(
        OUTPUT / "pair_separation_by_pair.csv",
        inventory,
        [
            "record_id",
            "rna_id",
            "source_model",
            "sequence_length",
            "pair_role",
            "pair_status",
            "i",
            "j",
            "sequence_separation",
            "relative_separation",
            "separation_bin",
        ],
    )
    (OUTPUT / "separation_distribution_gt.json").write_text(
        json.dumps(distribution, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_csv(
        OUTPUT / "pair_error_by_separation_bin.csv",
        pair_summary,
        list(pair_summary[0]),
    )
    _write_csv(
        OUTPUT / "wrong_partner_by_separation_bin.csv",
        wrong_summary,
        list(wrong_summary[0]),
    )
    _write_csv(
        OUTPUT / "stem_error_separation_summary.csv",
        stem_summary,
        list(stem_summary[0]),
    )
    print(
        json.dumps(
            {
                "records": len(records),
                "pair_inventory_rows": len(inventory),
                "unique_gt_rnas": len(unique_gt),
                "unique_gt_pairs": distribution["gt_pair_count"],
                "chosen_protocol": distribution["chosen_protocol"],
                "frozen_counts_preserved": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
