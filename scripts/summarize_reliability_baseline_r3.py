#!/usr/bin/env python3
"""Summarize the frozen R3 pair-reliability baselines.

The calibration helpers implement the prospective 2026-09-03 amendment.
Formal artifact summarization is added below these definition-level helpers.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ECE_BIN_COUNT = 10
ECE_BIN_EDGES = tuple(i / ECE_BIN_COUNT for i in range(ECE_BIN_COUNT + 1))


def _validated_scores_labels(
    scores: Iterable[float], labels: Iterable[int]
) -> tuple[list[float], list[int]]:
    score_values = [float(value) for value in scores]
    label_values = [int(value) for value in labels]
    if len(score_values) != len(label_values):
        raise ValueError("scores and labels must have equal length")
    if not score_values:
        raise ValueError("calibration metric requires at least one example")
    for score in score_values:
        if not math.isfinite(score) or score < 0.0 or score > 1.0:
            raise ValueError(f"invalid probability-like risk score: {score!r}")
    if any(label not in (0, 1) for label in label_values):
        raise ValueError("calibration labels must be binary DELETE-positive values")
    return score_values, label_values


def ece_bin_index(score: float) -> int:
    """Return the frozen equal-width bin index; score 1 belongs to bin 9."""
    value, _ = _validated_scores_labels([score], [0])
    return min(int(value[0] * ECE_BIN_COUNT), ECE_BIN_COUNT - 1)


def fixed_bin_ece(scores: Iterable[float], labels: Iterable[int]) -> dict:
    """Compute event-pooled ECE and retain all ten immutable bins."""
    score_values, label_values = _validated_scores_labels(scores, labels)
    members: list[list[tuple[float, int]]] = [[] for _ in range(ECE_BIN_COUNT)]
    for score, label in zip(score_values, label_values):
        members[ece_bin_index(score)].append((score, label))

    total = len(score_values)
    bins = []
    ece = 0.0
    for index, rows in enumerate(members):
        count = len(rows)
        weight = count / total
        if rows:
            mean_score = sum(row[0] for row in rows) / count
            observed = sum(row[1] for row in rows) / count
            gap = abs(mean_score - observed)
            contribution = weight * gap
        else:
            mean_score = None
            observed = None
            gap = None
            contribution = 0.0
        ece += contribution
        bins.append({
            "bin_index": index,
            "bin_left": ECE_BIN_EDGES[index],
            "bin_right": ECE_BIN_EDGES[index + 1],
            "right_inclusive": index == ECE_BIN_COUNT - 1,
            "count": count,
            "weight": weight,
            "mean_score": mean_score,
            "observed_delete_rate": observed,
            "absolute_gap": gap,
            "ece_contribution": contribution,
        })
    return {"ece": ece, "n_examples": total, "bins": bins}


def brier_score(scores: Iterable[float], labels: Iterable[int]) -> float:
    """Brier score for DELETE/FP-positive labels."""
    score_values, label_values = _validated_scores_labels(scores, labels)
    return sum((score - label) ** 2 for score, label in zip(score_values, label_values)) / len(score_values)


def rna_balanced_ece(rows: Sequence[Mapping[str, object]]) -> dict:
    """Mean per-RNA fixed-bin ECE, with each defined RNA weighted equally."""
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["rna_id"])].append(row)
    if not grouped:
        return {"ece": None, "number_of_defined_rnas": 0, "per_rna": []}
    per_rna = []
    for rna_id in sorted(grouped):
        subset = grouped[rna_id]
        result = fixed_bin_ece(
            [float(row["score"]) for row in subset],
            [int(row["label_delete"]) for row in subset],
        )
        per_rna.append({"rna_id": rna_id, "ece": result["ece"], "n_events": len(subset)})
    return {
        "ece": sum(row["ece"] for row in per_rna) / len(per_rna),
        "number_of_defined_rnas": len(per_rna),
        "per_rna": per_rna,
    }


def bpp_to_delete_risk(bpp: float) -> float:
    """Orient thermodynamic pair probability toward DELETE/FP-positive risk."""
    value, _ = _validated_scores_labels([bpp], [0])
    return 1.0 - value[0]


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/reliability_baseline_r3"
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
SEEDS = (17, 29, 41, 53, 67)


def average_precision(scores: Iterable[float], labels: Iterable[int]) -> float | None:
    """Frozen non-interpolated AP with equal scores handled as atomic groups."""
    values = [(float(score), int(label)) for score, label in zip(scores, labels)]
    if any(label not in (0, 1) for _, label in values):
        raise ValueError("labels must be binary")
    positives = sum(label for _, label in values)
    if positives == 0:
        return None
    groups: dict[float, list[int]] = defaultdict(list)
    for score, label in values:
        if not math.isfinite(score):
            raise ValueError("risk scores must be finite")
        groups[score].append(label)
    cumulative_positive = 0
    cumulative_total = 0
    result = 0.0
    for score in sorted(groups, reverse=True):
        group = groups[score]
        group_positive = sum(group)
        cumulative_positive += group_positive
        cumulative_total += len(group)
        result += (cumulative_positive / cumulative_total) * (group_positive / positives)
    return result


def auroc(scores: Iterable[float], labels: Iterable[int]) -> float | None:
    """Tie-aware AUROC using half credit for tied positive-negative pairs."""
    values = [(float(score), int(label)) for score, label in zip(scores, labels)]
    positives = sum(label == 1 for _, label in values)
    negatives = sum(label == 0 for _, label in values)
    if positives == 0 or negatives == 0:
        return None
    groups: dict[float, list[int]] = defaultdict(list)
    for score, label in values:
        if not math.isfinite(score) or label not in (0, 1):
            raise ValueError("invalid AUROC input")
        groups[score].append(label)
    negatives_below = 0
    favorable = 0.0
    for score in sorted(groups):
        group_positive = sum(groups[score])
        group_negative = len(groups[score]) - group_positive
        favorable += group_positive * negatives_below + 0.5 * group_positive * group_negative
        negatives_below += group_negative
    return favorable / (positives * negatives)


def safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def prf(tp: int, fp: int, fn: int) -> tuple[float | None, float | None, float | None]:
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def mean_defined(values: Iterable[float | None]) -> tuple[float | None, int]:
    defined = [float(value) for value in values if value is not None]
    return (sum(defined) / len(defined), len(defined)) if defined else (None, 0)


def discrimination(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    scores = [float(row["risk"]) for row in rows]
    labels = [int(row["label_delete"]) for row in rows]
    return {
        "n_events": len(rows), "positive_count": sum(labels),
        "positive_prevalence": safe_ratio(sum(labels), len(labels)),
        "auprc": average_precision(scores, labels), "auroc": auroc(scores, labels),
    }


def rna_balanced_discrimination(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["rna_id"])].append(row)
    ap, roc, prevalence = [], [], []
    for subset in grouped.values():
        result = discrimination(subset)
        ap.append(result["auprc"])
        roc.append(result["auroc"])
        prevalence.append(result["positive_prevalence"])
    mean_ap, n_ap = mean_defined(ap)
    mean_roc, n_roc = mean_defined(roc)
    mean_prev, n_prev = mean_defined(prevalence)
    return {
        "n_rnas": len(grouped), "auprc": mean_ap, "auprc_defined_rnas": n_ap,
        "auroc": mean_roc, "auroc_defined_rnas": n_roc,
        "positive_prevalence": mean_prev, "prevalence_defined_rnas": n_prev,
    }


def utility_metrics(
    rows: Sequence[Mapping[str, object]], delete_flags: Sequence[bool]
) -> dict[str, dict[str, object]]:
    if len(rows) != len(delete_flags):
        raise ValueError("rows/delete flags length mismatch")
    contexts: dict[tuple[str, str], dict[str, int | str]] = {}
    for row, delete in zip(rows, delete_flags):
        context_id = str(row.get("manifest_id", row["rna_id"]))
        key = (context_id, str(row["source"]))
        gt_count = int(row["gt_pair_count"])
        item = contexts.setdefault(key, {
            "rna_id": str(row["rna_id"]), "gt": gt_count, "tp": 0, "fp": 0,
            "lost_tp": 0, "removed_fp": 0, "pairs": 0, "deleted": 0,
        })
        if item["gt"] != gt_count or item["rna_id"] != str(row["rna_id"]):
            raise AssertionError(f"inconsistent context metadata: {key}")
        label = int(row["label_delete"])
        item["pairs"] = int(item["pairs"]) + 1
        item["tp" if label == 0 else "fp"] = int(item["tp" if label == 0 else "fp"]) + 1
        if delete:
            item["deleted"] = int(item["deleted"]) + 1
            target = "removed_fp" if label == 1 else "lost_tp"
            item[target] = int(item[target]) + 1

    def aggregate(items: Iterable[Mapping[str, int | str]]) -> dict[str, object]:
        values = list(items)
        tp0 = sum(int(item["tp"]) for item in values)
        fp0 = sum(int(item["fp"]) for item in values)
        fn0 = sum(int(item["gt"]) - int(item["tp"]) for item in values)
        lost = sum(int(item["lost_tp"]) for item in values)
        removed = sum(int(item["removed_fp"]) for item in values)
        deleted = lost + removed
        tp1, fp1, fn1 = tp0 - lost, fp0 - removed, fn0 + lost
        p0, r0, f0 = prf(tp0, fp0, fn0)
        p1, r1, f1 = prf(tp1, fp1, fn1)
        return {
            "context_count": len(values), "pair_event_count": tp0 + fp0,
            "tp_before": tp0, "fp_before": fp0, "fn_before": fn0,
            "lost_tp": lost, "removed_fp": removed, "deleted_pair_count": deleted,
            "tp_preservation": safe_ratio(tp1, tp0), "fp_removal": safe_ratio(removed, fp0),
            "modification_precision": safe_ratio(removed, deleted),
            "coverage": safe_ratio(deleted, tp0 + fp0),
            "delete_precision": safe_ratio(removed, deleted), "delete_recall": safe_ratio(removed, fp0),
            "resulting_precision": p1, "resulting_recall": r1, "resulting_f1": f1,
            "original_precision": p0, "original_recall": r0, "original_f1": f0,
            "delta_f1": None if f1 is None or f0 is None else f1 - f0,
        }

    event = aggregate(contexts.values())
    by_rna: dict[str, list[Mapping[str, int | str]]] = defaultdict(list)
    for item in contexts.values():
        by_rna[str(item["rna_id"])].append(item)
    per_rna = {rna_id: aggregate(items) for rna_id, items in by_rna.items()}
    fields = (
        "tp_preservation", "fp_removal", "modification_precision", "coverage",
        "delete_precision", "delete_recall", "resulting_precision", "resulting_recall",
        "resulting_f1", "original_precision", "original_recall", "original_f1", "delta_f1",
    )
    balanced: dict[str, object] = {"rna_count": len(per_rna)}
    for field in fields:
        balanced[field], balanced[f"{field}_defined_rnas"] = mean_defined(
            item[field] for item in per_rna.values()
        )
    balanced["deleted_pair_count"] = sum(int(item["deleted_pair_count"]) for item in per_rna.values())
    balanced["lost_tp"] = sum(int(item["lost_tp"]) for item in per_rna.values())
    balanced["removed_fp"] = sum(int(item["removed_fp"]) for item in per_rna.values())
    return {"event_pooled": event, "rna_balanced": balanced, "per_rna": per_rna}


def threshold_flags(rows: Sequence[Mapping[str, object]], threshold: float | None) -> list[bool]:
    return [False] * len(rows) if threshold is None else [float(row["risk"]) >= threshold for row in rows]


def select_high_preservation_threshold(
    rows: Sequence[Mapping[str, object]], safety: float = 0.99
) -> tuple[float | None, list[dict[str, object]]]:
    if any(str(row.get("partition", "validation")) != "validation" for row in rows):
        raise AssertionError("threshold selection accepts validation rows only")
    thresholds: list[float | None] = [None] + sorted({float(row["risk"]) for row in rows}, reverse=True)
    candidates = []
    for threshold in thresholds:
        metrics = utility_metrics(rows, threshold_flags(rows, threshold))
        event = metrics["event_pooled"]
        balanced = metrics["rna_balanced"]
        eligible = (
            event["tp_preservation"] is not None and balanced["tp_preservation"] is not None
            and float(event["tp_preservation"]) >= safety
            and float(balanced["tp_preservation"]) >= safety
        )
        candidates.append({
            "threshold": threshold, "threshold_semantics": "DELETE_NONE" if threshold is None else "DELETE_RISK_GTE",
            "eligible": eligible, **{f"event_{key}": value for key, value in event.items()},
            **{f"rna_balanced_{key}": value for key, value in balanced.items()},
        })
    eligible_rows = [row for row in candidates if row["eligible"]]
    if not eligible_rows:
        raise AssertionError("delete-none must satisfy the preservation gate")
    def key(row: Mapping[str, object]) -> tuple[float, float, int, float]:
        fp = float(row["rna_balanced_fp_removal"] or 0.0)
        mp = row["rna_balanced_modification_precision"]
        mp_key = -math.inf if mp is None else float(mp)
        deleted = int(row["event_deleted_pair_count"])
        threshold = math.inf if row["threshold"] is None else float(row["threshold"])
        return fp, mp_key, -deleted, threshold
    selected = max(eligible_rows, key=key)
    for row in candidates:
        row["selected"] = row is selected
    return selected["threshold"], candidates


def validate_single_historical_seed(
    rows: Sequence[Mapping[str, object]], expected_seed: int
) -> None:
    observed = {int(row["historical_seed"]) for row in rows}
    if observed != {expected_seed}:
        raise AssertionError(f"historical model seeds must remain separate: {observed}")


def risk_curve(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output = []
    for threshold in [None] + sorted({float(row["risk"]) for row in rows}, reverse=True):
        metrics = utility_metrics(rows, threshold_flags(rows, threshold))
        event, balanced = metrics["event_pooled"], metrics["rna_balanced"]
        output.append({
            "threshold": threshold, "threshold_semantics": "DELETE_NONE" if threshold is None else "DELETE_RISK_GTE",
            "one_minus_tp_preservation_event": None if event["tp_preservation"] is None else 1 - float(event["tp_preservation"]),
            "fp_removal_event": event["fp_removal"],
            "one_minus_tp_preservation_rna_balanced": None if balanced["tp_preservation"] is None else 1 - float(balanced["tp_preservation"]),
            "fp_removal_rna_balanced": balanced["fp_removal"],
            **{f"event_{key}": value for key, value in event.items()},
            **{f"rna_balanced_{key}": value for key, value in balanced.items()},
        })
    return output


def csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, bool):
        return int(value)
    return value


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        if fields:
            writer.writeheader()
            writer.writerows({key: csv_value(row.get(key)) for key in fields} for row in rows)


def write_csv_gz(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as zipped:
        with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as text:
            writer = csv.DictWriter(text, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows({key: csv_value(row.get(key)) for key in fields} for row in rows)
    path.write_bytes(buffer.getvalue())


def read_csv_gz(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def calibration_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    scores = [float(row["risk"]) for row in rows]
    labels = [int(row["label_delete"]) for row in rows]
    event = fixed_bin_ece(scores, labels)
    rna = rna_balanced_ece([
        {"rna_id": row["rna_id"], "score": row["risk"], "label_delete": row["label_delete"]}
        for row in rows
    ])
    by_rna: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        by_rna[str(row["rna_id"])].append(row)
    rna_brier, n_brier = mean_defined(
        brier_score([float(item["risk"]) for item in subset], [int(item["label_delete"]) for item in subset])
        for subset in by_rna.values()
    )
    return {
        "n_events": len(rows), "event_pooled_brier": brier_score(scores, labels),
        "event_pooled_ece": event["ece"], "rna_balanced_brier": rna_brier,
        "rna_balanced_brier_defined_rnas": n_brier, "rna_balanced_ece": rna["ece"],
        "rna_balanced_ece_defined_rnas": rna["number_of_defined_rnas"],
    }


def strata(rows: Sequence[Mapping[str, object]], include_fold: bool = True) -> list[tuple[dict[str, object], list[Mapping[str, object]]]]:
    result: list[tuple[dict[str, object], list[Mapping[str, object]]]] = [({"stratum": "POOLED", "source": "ALL", "fold": "ALL", "channel": "ALL"}, list(rows))]
    for source in SOURCES:
        result.append(({"stratum": "SOURCE", "source": source, "fold": "ALL", "channel": "ALL"}, [row for row in rows if row["source"] == source]))
    channels = sorted({str(row.get("channel", "")) for row in rows if row.get("channel")})
    for channel in channels:
        result.append(({"stratum": "CHANNEL", "source": "ALL", "fold": "ALL", "channel": channel}, [row for row in rows if row.get("channel") == channel]))
    if include_fold:
        for fold in sorted({int(row["fold"]) for row in rows}):
            result.append(({"stratum": "FOLD", "source": "ALL", "fold": fold, "channel": "ALL"}, [row for row in rows if int(row["fold"]) == fold]))
    return [(meta, subset) for meta, subset in result if subset]


def flatten_utility(prefix: str, result: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    return {
        **{f"{prefix}_event_{key}": value for key, value in result["event_pooled"].items()},
        **{f"{prefix}_rna_balanced_{key}": value for key, value in result["rna_balanced"].items()},
    }


def summarize() -> dict[str, object]:
    base = RESULTS / "pair_scores"
    if not (RESULTS / "integrity/runner_completion.json").is_file():
        raise FileNotFoundError("R3 runner completion gate is absent")
    p0 = read_csv_gz(base / "track_p_p0.csv.gz")
    p1 = {seed: read_csv_gz(base / f"track_p_p1_seed{seed}.csv.gz") for seed in SEEDS}
    p2 = read_csv_gz(base / "track_p_p2.csv.gz")
    p3 = {seed: read_csv_gz(base / f"track_p_p3_seed{seed}.csv.gz") for seed in SEEDS}
    p4 = read_csv_gz(base / "track_p_p4.csv.gz")
    e1 = read_csv_gz(base / "track_e_e1.csv.gz")
    e2 = read_csv_gz(base / "track_e_e2.csv.gz")

    if len([row for row in p2 if row["partition"] == "test"]) != 5290:
        raise AssertionError("Track P held-out universe mismatch during summarization")
    if len(e1) != len(e2) or not e1:
        raise AssertionError("Track E universe mismatch during summarization")
    for seed in SEEDS:
        validate_single_historical_seed(p1[seed], seed)
        validate_single_historical_seed(p3[seed], seed)

    discrimination_event, discrimination_rna = [], []
    datasets: list[tuple[str, str, int | None, str | None, list[dict[str, str]]]] = []
    for seed, rows in p1.items():
        datasets.append(("P", "R3-P1", seed, None, [row for row in rows if row["partition"] == "test"]))
    datasets.append(("P", "R3-P2", None, None, [row for row in p2 if row["partition"] == "test"]))
    for seed, rows in p3.items():
        datasets.append(("P", "R3-P3", seed, None, rows))
    datasets.append(("P", "R3-P4", None, None, [row for row in p4 if row["partition"] == "test"]))
    datasets.extend((("E", "R3-E1", None, None, e1), ("E", "R3-E2", None, None, e2)))
    for track, baseline, seed, variant, rows in datasets:
        for meta, subset in strata(rows):
            common = {"track": track, "baseline": baseline, "historical_seed": seed, "variant": variant, **meta}
            discrimination_event.append({**common, "aggregation": "EVENT_POOLED", **discrimination(subset)})
            discrimination_rna.append({**common, "aggregation": "RNA_BALANCED", **rna_balanced_discrimination(subset)})

    threshold_search, locked, track_p_curves = [], [], []
    selected: dict[tuple[str, int | None, int], float | None] = {}
    sortable = [("R3-P2", None, p2), ("R3-P4", None, p4)]
    sortable.extend(("R3-P1", seed, rows) for seed, rows in p1.items())
    for baseline, seed, rows in sortable:
        for fold in range(5):
            validation = [row for row in rows if row["partition"] == "validation" and int(row["fold"]) == fold]
            test = [row for row in rows if row["partition"] == "test" and int(row["fold"]) == fold]
            threshold, candidates = select_high_preservation_threshold(validation)
            selected[(baseline, seed, fold)] = threshold
            for row in candidates:
                threshold_search.append({"baseline": baseline, "historical_seed": seed, "fold": fold, **row})
            locked.append({
                "baseline": baseline, "historical_seed": seed, "fold": fold,
                "selected_threshold": threshold, "threshold_semantics": "DELETE_NONE" if threshold is None else "DELETE_RISK_GTE",
                "selected_on": "VALIDATION_ONLY", "test_labels_used_for_selection": False,
            })
            for curve_row in risk_curve(test):
                track_p_curves.append({"baseline": baseline, "historical_seed": seed, "fold": fold, "partition": "test", **curve_row})

    high_rows: list[dict[str, object]] = []
    candidate_points: dict[str, dict[str, object]] = {}
    source_points: dict[str, list[dict[str, object]]] = defaultdict(list)

    def add_point(
        track: str, baseline: str, rows: list[dict[str, str]], flags: list[bool],
        *, seed: int | None = None, level: str = "BASELINE", semantics: str,
    ) -> dict[str, object]:
        full = utility_metrics(rows, flags)
        event, balanced = full["event_pooled"], full["rna_balanced"]
        eligible = (
            event["tp_preservation"] is not None and balanced["tp_preservation"] is not None
            and float(event["tp_preservation"]) >= 0.99 and float(balanced["tp_preservation"]) >= 0.99
        )
        row = {
            "track": track, "baseline": baseline, "summary_level": level,
            "historical_seed": seed, "scope": "POOLED", "source": "ALL",
            "operating_semantics": semantics, "high_preservation_eligible": eligible,
            **flatten_utility("achieved", full),
        }
        high_rows.append(row)
        for source in SOURCES:
            indices = [index for index, item in enumerate(rows) if item["source"] == source]
            subset = [rows[index] for index in indices]
            subflags = [flags[index] for index in indices]
            metrics = utility_metrics(subset, subflags)
            source_row = {
                "track": track, "baseline": baseline, "summary_level": level,
                "historical_seed": seed, "scope": "SOURCE", "source": source,
                "operating_semantics": semantics,
                "high_preservation_eligible": (
                    float(metrics["event_pooled"]["tp_preservation"]) >= 0.99
                    and float(metrics["rna_balanced"]["tp_preservation"]) >= 0.99
                ),
                **flatten_utility("achieved", metrics),
            }
            high_rows.append(source_row)
            source_points[baseline].append(source_row)
        for channel in sorted({str(item.get("channel", "")) for item in rows if item.get("channel")}):
            indices = [index for index, item in enumerate(rows) if item.get("channel") == channel]
            subset = [rows[index] for index in indices]
            subflags = [flags[index] for index in indices]
            metrics = utility_metrics(subset, subflags)
            high_rows.append({
                "track": track, "baseline": baseline, "summary_level": level,
                "historical_seed": seed, "scope": "CHANNEL", "source": "ALL",
                "channel": channel, "operating_semantics": semantics,
                "high_preservation_eligible": (
                    float(metrics["event_pooled"]["tp_preservation"]) >= 0.99
                    and float(metrics["rna_balanced"]["tp_preservation"]) >= 0.99
                ),
                **flatten_utility("achieved", metrics),
            })
        return row

    per_seed_points: dict[str, list[dict[str, object]]] = defaultdict(list)
    for baseline, seed, rows in sortable:
        test = [row for row in rows if row["partition"] == "test"]
        flags = [
            False if selected[(baseline, seed, int(row["fold"]))] is None
            else float(row["risk"]) >= float(selected[(baseline, seed, int(row["fold"]))])
            for row in test
        ]
        level = "SEED" if seed is not None else "BASELINE"
        point = add_point("P", baseline, test, flags, seed=seed, level=level, semantics="VALIDATION_SELECTED_THRESHOLD_BY_FOLD")
        if seed is None:
            candidate_points[baseline] = point
        else:
            per_seed_points[baseline].append(point)

    for seed, rows in p3.items():
        point = add_point("P", "R3-P3", rows, [int(row["risk"]) == 1 for row in rows], seed=seed, level="SEED", semantics="IMMUTABLE_V3_VETO2_FIXED")
        per_seed_points["R3-P3"].append(point)

    def mean_seed_point(baseline: str) -> dict[str, object]:
        points = per_seed_points[baseline]
        event_fields = [key for key in points[0] if key.startswith("achieved_event_")]
        rna_fields = [key for key in points[0] if key.startswith("achieved_rna_balanced_")]
        row: dict[str, object] = {
            "track": "P", "baseline": baseline, "summary_level": "BASELINE",
            "historical_seed": "MEAN_ACROSS_5_SEEDS", "scope": "POOLED", "source": "ALL",
            "operating_semantics": points[0]["operating_semantics"],
        }
        for field in event_fields + rna_fields:
            row[field], _ = mean_defined(point[field] for point in points)
        row["high_preservation_eligible"] = (
            float(row["achieved_event_tp_preservation"]) >= 0.99
            and float(row["achieved_rna_balanced_tp_preservation"]) >= 0.99
        )
        high_rows.append(row)
        # Mean each source's seed-level result without pooling seed rows.
        for source in SOURCES:
            source_seed_rows = [
                item for item in high_rows if item["baseline"] == baseline and item["summary_level"] == "SEED"
                and item["scope"] == "SOURCE" and item["source"] == source
            ]
            source_row: dict[str, object] = {
                "track": "P", "baseline": baseline, "summary_level": "BASELINE",
                "historical_seed": "MEAN_ACROSS_5_SEEDS", "scope": "SOURCE", "source": source,
                "operating_semantics": row["operating_semantics"],
            }
            for field in event_fields + rna_fields:
                source_row[field], _ = mean_defined(item[field] for item in source_seed_rows)
            source_row["high_preservation_eligible"] = (
                float(source_row["achieved_event_tp_preservation"]) >= 0.99
                and float(source_row["achieved_rna_balanced_tp_preservation"]) >= 0.99
            )
            high_rows.append(source_row)
            source_points[baseline].append(source_row)
        return row

    candidate_points["R3-P1"] = mean_seed_point("R3-P1")
    candidate_points["R3-P3"] = mean_seed_point("R3-P3")
    e_points = {}
    for baseline, rows in (("R3-E1", e1), ("R3-E2", e2)):
        point = add_point("E", baseline, rows, [int(row["risk"]) == 1 for row in rows], semantics="FIXED_BINARY_POINT")
        candidate_points[baseline] = point
        e_points[baseline] = point

    binary_points = [
        row for row in high_rows if row["baseline"] in ("R3-P3", "R3-E1", "R3-E2")
        and row["summary_level"] in ("SEED", "BASELINE")
    ]

    p0_prevalence = []
    for scope in ("POOLED_TRAINING_PREVALENCE", "SOURCE_WISE_TRAINING_PREVALENCE"):
        rows = [row for row in p0 if row["reference_scope"] == scope]
        for fold in range(5):
            fold_rows = [row for row in rows if int(row["fold"]) == fold]
            reporting_sources = ("ALL",) + SOURCES if scope == "POOLED_TRAINING_PREVALENCE" else SOURCES
            for source in reporting_sources:
                subset = fold_rows if source == "ALL" else [row for row in fold_rows if row["source"] == source]
                p0_prevalence.append({
                    "reference_scope": scope, "fold": fold, "source": source,
                    "training_prevalence_score": float(subset[0]["risk"]),
                    "heldout_positive_prevalence": sum(int(row["label_delete"]) for row in subset) / len(subset),
                    "heldout_pair_count": len(subset),
                    "auprc_all_tied": sum(int(row["label_delete"]) for row in subset) / len(subset),
                    "auroc_all_tied": 0.5 if len({int(row["label_delete"]) for row in subset}) == 2 else None,
                    "ranking_utility": "NONE_ALL_TIED_WITHIN_ROTATION_STRATUM",
                })

    support_enrichment = []
    p2_test = [row for row in p2 if row["partition"] == "test"]
    for source in ("ALL",) + SOURCES:
        source_rows = p2_test if source == "ALL" else [row for row in p2_test if row["source"] == source]
        for support in (0, 1, 2):
            subset = [row for row in source_rows if int(row["support_other_count"]) == support]
            support_enrichment.append({
                "source": source, "support_other_count": support, "risk": 2 - support,
                "pair_count": len(subset), "fp_count": sum(int(row["label_delete"]) for row in subset),
                "fp_prevalence": safe_ratio(sum(int(row["label_delete"]) for row in subset), len(subset)),
            })

    calibration_summary, reliability_bins = [], []
    calibration_sets = []
    for scope in ("POOLED_TRAINING_PREVALENCE", "SOURCE_WISE_TRAINING_PREVALENCE"):
        calibration_sets.append(("R3-P0", None, scope, [row for row in p0 if row["reference_scope"] == scope], "CONSTANT_TRAINING_PREVALENCE_REFERENCE"))
    for seed, rows in p1.items():
        calibration_sets.append(("R3-P1", seed, None, [row for row in rows if row["partition"] == "test"], "RAW_UNCALIBRATED"))
    calibration_sets.append(("R3-P4", None, None, [row for row in p4 if row["partition"] == "test"], "THERMODYNAMIC_RISK_EMPIRICAL_RELATIONSHIP"))
    for baseline, seed, variant, rows, warning in calibration_sets:
        for meta, subset in strata(rows):
            metrics = calibration_metrics(subset)
            common = {
                "baseline": baseline,
                "track": "P",
                "historical_seed": seed,
                "seed_if_applicable": seed,
                "variant": variant,
                **meta,
                "semantic_warning": warning,
            }
            calibration_summary.append({**common, **metrics})
            result = fixed_bin_ece([float(row["risk"]) for row in subset], [int(row["label_delete"]) for row in subset])
            for bin_row in result["bins"]:
                reliability_bins.append({
                    **common, "aggregation": "EVENT_POOLED", "rna_id": "ALL",
                    **bin_row,
                })
            by_rna: dict[str, list[Mapping[str, object]]] = defaultdict(list)
            for item in subset:
                by_rna[str(item["rna_id"])].append(item)
            for rna_id in sorted(by_rna):
                rna_rows = by_rna[rna_id]
                rna_result = fixed_bin_ece(
                    [float(item["risk"]) for item in rna_rows],
                    [int(item["label_delete"]) for item in rna_rows],
                )
                for bin_row in rna_result["bins"]:
                    reliability_bins.append({
                        **common,
                        "aggregation": "RNA_COMPONENT_FOR_RNA_BALANCED_ECE",
                        "rna_id": rna_id,
                        **bin_row,
                    })

    # Attach RNA-balanced AUPRC to candidate points for frozen comparator selection.
    def candidate_auprc(baseline: str) -> float | None:
        rows = [row for row in discrimination_rna if row["baseline"] == baseline and row["stratum"] == "POOLED"]
        if baseline in ("R3-P1", "R3-P3"):
            value, _ = mean_defined(row["auprc"] for row in rows)
            return value
        if len(rows) != 1:
            raise AssertionError(f"unexpected pooled discrimination rows for {baseline}: {len(rows)}")
        return rows[0]["auprc"]

    for baseline, point in candidate_points.items():
        point["rna_balanced_auprc"] = candidate_auprc(baseline)

    def select_strongest(track: str, baselines: Sequence[str]) -> dict[str, object]:
        pool = [candidate_points[baseline] for baseline in baselines if candidate_points[baseline]["high_preservation_eligible"]]
        if not pool:
            return {"status": "NO_HIGH_PRESERVATION_ELIGIBLE_BASELINE", "track": track}
        winner = max(pool, key=lambda row: (
            float(row["achieved_rna_balanced_fp_removal"]),
            -math.inf if row["achieved_rna_balanced_modification_precision"] is None else float(row["achieved_rna_balanced_modification_precision"]),
            -math.inf if row["rna_balanced_auprc"] is None else float(row["rna_balanced_auprc"]),
            -float(row["achieved_event_deleted_pair_count"]),
        ))
        source_rows = [
            row for row in high_rows if row["baseline"] == winner["baseline"]
            and row["summary_level"] == "BASELINE" and row["scope"] == "SOURCE"
        ]
        source_delta_signs = {
            float(row["achieved_rna_balanced_delta_f1"]) > 0.0
            for row in source_rows if row["achieved_rna_balanced_delta_f1"] is not None
        }
        source_dependent = (
            any(not bool(row["high_preservation_eligible"]) for row in source_rows)
            or len(source_delta_signs) > 1
        )
        return {
            "status": "SELECTED", "track": track, "baseline_id": winner["baseline"],
            "selection_rule": [
                "highest_RNA_balanced_FP_removal_at_TP_preservation_ge_0.99",
                "higher_RNA_balanced_modification_precision", "higher_RNA_balanced_AUPRC",
                "fewer_deleted_pair_events",
            ],
            "operating_semantics": winner["operating_semantics"],
            "event_pooled": {key.removeprefix("achieved_event_"): value for key, value in winner.items() if key.startswith("achieved_event_")},
            "rna_balanced": {key.removeprefix("achieved_rna_balanced_"): value for key, value in winner.items() if key.startswith("achieved_rna_balanced_")},
            "rna_balanced_auprc": winner["rna_balanced_auprc"],
            "source_summaries": source_rows,
            "source_dependence_flag": "SOURCE_DEPENDENT_COMPARATOR" if source_dependent else "NO_SOURCE_SAFETY_FAILURE_AT_0.99",
        }

    strongest_p = select_strongest("P", ("R3-P1", "R3-P2", "R3-P3", "R3-P4"))
    strongest_e = select_strongest("E", ("R3-E1", "R3-E2"))
    strongest = {
        "STRONGEST_R3_PREDICTION_ONLY_BASELINE": strongest_p,
        "STRONGEST_R3_EVIDENCE_CONDITIONED_BASELINE": strongest_e,
    }

    summaries = RESULTS / "summaries"
    curves = RESULTS / "risk_curves"
    calibration = RESULTS / "calibration"
    write_csv(summaries / "discrimination_event_pooled.csv", discrimination_event)
    write_csv(summaries / "discrimination_rna_balanced.csv", discrimination_rna)
    write_csv(summaries / "p0_prevalence.csv", p0_prevalence)
    write_csv(summaries / "p2_support_enrichment.csv", support_enrichment)
    write_csv(summaries / "binary_operating_points.csv", binary_points)
    write_csv(summaries / "source_wise_summary.csv", [row for row in high_rows if row["scope"] == "SOURCE" and row["summary_level"] == "BASELINE"])
    write_csv(curves / "locked_thresholds.csv", locked)
    write_csv_gz(curves / "validation_threshold_search.csv.gz", threshold_search)
    write_csv_gz(curves / "track_p_risk_curves.csv.gz", track_p_curves)
    write_csv(curves / "high_preservation_summary.csv", high_rows)
    write_csv(calibration / "probability_like_metrics.csv", calibration_summary)
    write_csv_gz(calibration / "reliability_bins.csv.gz", reliability_bins)
    write_json(calibration / "calibration_scope_warnings.json", {
        "R3-P0": "constant training-prevalence reference; no ranking utility",
        "R3-P1": "RAW_UNCALIBRATED; no R3 recalibration",
        "R3-P4": "thermodynamic pair-probability-derived risk compared descriptively with empirical FP frequency",
        "prohibited": ["R3-P2", "R3-P3", "R3-E1", "R3-E2"],
    })
    write_json(summaries / "strongest_baselines.json", strongest)
    write_json(summaries / "strongest_prediction_only_baseline.json", strongest_p)
    write_json(summaries / "strongest_evidence_conditioned_baseline.json", strongest_e)
    r2_reference = {
        "label": "FULL_REFOLD_REFERENCE", "operation_space": "GLOBAL_REFOLD_NOT_DELETION_ONLY",
        "macro_tp_preservation": 0.975358, "micro_tp_preservation": 0.981767,
        "macro_fp_removal": 0.775728, "micro_fp_removal": 0.645883,
    }
    write_json(summaries / "r2_full_refold_reference.json", r2_reference)
    summary = {
        "status": "R3_RELIABILITY_BASELINE_SUITE_COMPLETE",
        "next_state": "READY_FOR_R3_INTERPRETATION_AND_R4_PROTOCOL_DECISION",
        "track_p_original_pairs": 5290, "track_e_pair_realizations_per_baseline": len(e1),
        "strongest_baselines": strongest, "r2_reference": r2_reference,
        "external77_accessed": False, "new_training_runs": 0, "historical_retuning": False,
        "r4_started": False,
    }
    write_json(summaries / "r3_summary.json", summary)
    return summary


def finalize_integrity(summary: Mapping[str, object]) -> None:
    integrity = RESULTS / "integrity"
    write_json(integrity / "threshold_selection_audit.json", {
        "status": "PASS", "selection_partition": "VALIDATION_ONLY",
        "event_and_rna_balanced_tp_preservation_minimum": 0.99,
        "objective": "MAXIMIZE_RNA_BALANCED_FP_REMOVAL",
        "tie_breaks": ["RNA_BALANCED_MODIFICATION_PRECISION", "FEWER_DELETIONS", "HIGHER_THRESHOLD"],
        "equal_score_groups_split": False, "test_label_thresholding": False,
    })
    write_json(integrity / "metric_definition_audit.json", {
        "status": "PASS", "positive_class": "DELETE_FP",
        "auprc": "NON_INTERPOLATED_AVERAGE_PRECISION_TIE_GROUPED",
        "auroc": "TIE_AWARE_HALF_CREDIT", "ece": "10_EQUAL_WIDTH_FIXED_BINS",
        "ece_amendment_frozen_before_performance": True,
        "risk_curve": "DELETION_ONLY_EQUAL_SCORE_GROUPS_ATOMIC",
        "calibration_eligible": ["R3-P0", "R3-P1", "R3-P4"],
        "calibration_prohibited": ["R3-P2", "R3-P3", "R3-E1", "R3-E2"],
    })
    versioned = sorted(
        path for path in RESULTS.rglob("*") if path.is_file()
        and path.name not in {"artifact_hashes.json", "execution_completion.json"}
    )
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in versioned}
    write_json(integrity / "artifact_hashes.json", {"hash_algorithm": "sha256", "files": hashes})
    write_json(integrity / "execution_completion.json", {
        "status": summary["status"], "all_mandatory_baselines_complete": True,
        "integrity_gates_passed": True, "metric_tests_required_before_execution": True,
        "strongest_comparators_frozen": True, "formal_summaries_reproducible_from_compact_artifacts": True,
        "external77_accessed": False, "new_training_runs": 0, "historical_v1_v3_retuned": False,
        "r4_started": False, "noise_or_real_evidence": False, "pseudoknot_branch": False,
        "two_d_to_three_d": False,
    })


def main() -> None:
    global RESULTS
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=RESULTS)
    args = parser.parse_args()
    RESULTS = args.results_root
    summary = summarize()
    finalize_integrity(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
