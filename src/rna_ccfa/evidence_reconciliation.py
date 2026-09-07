"""Frozen R4 Evidence Reconciliation Network implementation primitives.

This module implements the prospectively frozen R4 contract.  It deliberately
contains no path discovery: callers must pass explicitly allowlisted Legacy121,
clean-evidence, R2, and R3 paths through :func:`guard_r4_path`.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

from .selective_refiner import CATEGORIES, NUMERIC, extract_feature_rows


R4_PROTOCOL_SHA256 = "81ce3923c19a99094418dc5fb568c7081192ac84c542b33dbb4bafa888c739e4"
FROZEN_SPLIT_SHA256 = "810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f"
FROZEN_CLEAN_MANIFEST_SHA256 = "c743913d8d0b44cbccaba74b68bebaeb1551a4095d1ae51782435c12e96d11ca"
MODEL_SEEDS = (17, 29, 41, 53, 67)
FOLDS = (0, 1, 2, 3, 4)
CONDITIONS = ("ERN", "B4_EVIDENCE_MASKED")
CHANNELS = ("positive_pair", "unpaired")
CHANNEL_TO_MANIFEST = {
    "positive_pair": "POSITIVE_PAIR_EVIDENCE",
    "unpaired": "UNPAIRED_NUCLEOTIDE_EVIDENCE",
}
MANIFEST_TO_CHANNEL = {value: key for key, value in CHANNEL_TO_MANIFEST.items()}
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")

TRAINING_CONFIG = {
    "loss": "BCEWithLogitsLoss",
    "pos_weight": "KEEP_train / DELETE_train",
    "optimizer": "AdamW",
    "learning_rate": 1e-3,
    "weight_decay": 1e-4,
    "batch_size": 256,
    "max_epochs": 100,
    "early_stopping_patience": 12,
    "gradient_clip": 5.0,
    "checkpoint_metric": "validation_unweighted_binary_log_loss",
    "checkpoint_tie_break": ["higher_validation_AUPRC", "earlier_epoch"],
}

BASE_CATEGORIES = tuple(name for name in CATEGORIES if name != "source_model")
CANDIDATE_78_NAMES = tuple(NUMERIC) + tuple(
    name
    for field in BASE_CATEGORIES
    for name in tuple(f"{field}={value}" for value in CATEGORIES[field])
    + (f"{field}=UNKNOWN",)
)
CANDIDATE_FEATURE_NAMES = CANDIDATE_78_NAMES + (
    "p2_support_other_count_div_2",
    "p4_rnafold_bpp",
)
CANDIDATE_STANDARDIZED_INDICES = tuple(range(len(NUMERIC))) + (78, 79)

PAIR_ITEM_FEATURE_NAMES = (
    "abs_i_a_norm", "abs_i_b_norm", "abs_j_a_norm", "abs_j_b_norm",
    "min_endpoint_distance_norm", "max_endpoint_distance_norm",
    "candidate_span_norm", "evidence_span_norm",
    "signed_span_difference_norm", "midpoint_distance_norm",
    "exact_same_pair", "shared_endpoint", "direct_conflict",
    "relation_CONTAINING", "relation_NESTED", "relation_CROSSING",
    "relation_DISJOINT",
)
UNPAIRED_ITEM_FEATURE_NAMES = (
    "abs_i_k_norm", "abs_j_k_norm", "min_endpoint_distance_norm",
    "max_endpoint_distance_norm", "midpoint_distance_norm", "k_equals_i",
    "k_equals_j", "k_strictly_inside_pair_interval",
)
ITEM_CONTINUOUS_DIM = {"positive_pair": 10, "unpaired": 5}
ITEM_DIM = {"positive_pair": 17, "unpaired": 8}
DESCRIPTOR_NAMES = (
    "item_count", "item_count_div_sequence_length", "e1_local_conflict",
    "direct_pair_support",
)

MODEL_INPUT_COLUMNS = tuple(f"candidate_{index:02d}" for index in range(80))
DESCRIPTOR_COLUMNS = tuple(f"evidence_descriptor_{index:02d}" for index in range(4))
FORBIDDEN_MODEL_COLUMNS = {
    "rna_id", "source", "source_model", "fold", "partition", "density",
    "density_percent", "evidence_seed", "manifest_id",
    "manifest_payload_sha256", "source_gt_sha256", "label_delete",
    "original_pair_status", "scope", "gt_pair_count", "dataset", "family",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_sha256(payload: object) -> str:
    return sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def guard_r4_path(path: Path, *, allow_historical_contract: bool = False) -> Path:
    """Reject every out-of-scope path before it is opened by an R4 command."""
    lowered = str(path).lower()
    forbidden = ("external77", "shape", "dms", "pars", "real_evidence", "noisy_evidence")
    if any(token in lowered for token in forbidden):
        raise PermissionError(f"R4 forbidden path: {path}")
    historical_runner_tokens = (
        "run_evidence_guidance_stage_e2", "evidence_refiner.py",
        "results/evidence_guidance/stage_e2/",
    )
    if any(token in lowered for token in historical_runner_tokens):
        raise PermissionError(f"historical E2 execution path forbidden: {path}")
    if "stage_e2_protocol" in lowered and not allow_historical_contract:
        raise PermissionError(f"historical E2 contract requires explicit audit-only access: {path}")
    return path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    guard_r4_path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def encode_candidate_78(feature_values: Mapping[str, object]) -> np.ndarray:
    """Exact historical source-agnostic 78D encoder."""
    values: list[float] = [float(feature_values[name]) for name in NUMERIC]
    for field in BASE_CATEGORIES:
        vocabulary = CATEGORIES[field]
        default = "N/OTHER" if field.startswith("base") else "NONE"
        value = str(feature_values.get(field, default))
        values.extend(float(value == category) for category in vocabulary)
        values.append(float(value not in vocabulary))
    result = np.asarray(values, dtype=np.float32)
    if result.shape != (78,):
        raise AssertionError(f"historical candidate encoding is not 78D: {result.shape}")
    return result


def candidate_features_from_prediction(
    rna_id: str,
    sequence: str,
    predicted_pairs: Sequence[Sequence[int]],
    source_model: str,
) -> dict[tuple[int, int], np.ndarray]:
    """Extract 78D context without consulting GT labels."""
    rows = extract_feature_rows(
        rna_id,
        sequence,
        predicted_pairs,
        predicted_pairs,
        source_model,
        include_source=False,
    )
    return {row.pair: encode_candidate_78(row.features) for row in rows}


def append_frozen_reliability_signals(
    candidate_78: Sequence[float], support_other_count: int, rnafold_bpp: float
) -> np.ndarray:
    support = int(support_other_count)
    bpp = float(rnafold_bpp)
    if support not in (0, 1, 2):
        raise ValueError("support_other_count must be 0, 1, or 2")
    if not math.isfinite(bpp) or not 0.0 <= bpp <= 1.0:
        raise ValueError("RNAfold BPP must be finite in [0,1]")
    base = np.asarray(candidate_78, dtype=np.float32)
    if base.shape != (78,):
        raise ValueError("candidate base must be 78D")
    return np.concatenate([base, np.asarray([support / 2.0, bpp], dtype=np.float32)])


def _pair_relation(i: int, j: int, a: int, b: int) -> str:
    if i <= a and b <= j:
        return "CONTAINING"
    if a <= i and j <= b:
        return "NESTED"
    if (i < a < j < b) or (a < i < b < j):
        return "CROSSING"
    return "DISJOINT"


def positive_pair_item_features(
    candidate: tuple[int, int], evidence_pair: tuple[int, int], sequence_length: int
) -> np.ndarray:
    i, j = map(int, candidate)
    a, b = map(int, evidence_pair)
    if not (0 <= i < j < sequence_length and 0 <= a < b < sequence_length):
        raise ValueError("pair coordinates are invalid")
    denominator = float(max(sequence_length - 1, 1))
    distances = (abs(i - a), abs(i - b), abs(j - a), abs(j - b))
    same = (i, j) == (a, b)
    shared = bool({i, j} & {a, b})
    relation = _pair_relation(i, j, a, b)
    values = [
        *(distance / denominator for distance in distances),
        min(distances) / denominator,
        max(distances) / denominator,
        (j - i) / denominator,
        (b - a) / denominator,
        ((b - a) - (j - i)) / denominator,
        abs((i + j) - (a + b)) / (2.0 * denominator),
        float(same),
        float(shared),
        float(shared and not same),
        *(float(relation == name) for name in ("CONTAINING", "NESTED", "CROSSING", "DISJOINT")),
    ]
    result = np.asarray(values, dtype=np.float32)
    if result.shape != (17,) or not np.isfinite(result).all():
        raise AssertionError("positive-pair item must be finite 17D")
    return result


def unpaired_item_features(
    candidate: tuple[int, int], evidence_position: int, sequence_length: int
) -> np.ndarray:
    i, j = map(int, candidate)
    k = int(evidence_position)
    if not (0 <= i < j < sequence_length and 0 <= k < sequence_length):
        raise ValueError("unpaired coordinates are invalid")
    denominator = float(max(sequence_length - 1, 1))
    di, dj = abs(i - k), abs(j - k)
    result = np.asarray([
        di / denominator,
        dj / denominator,
        min(di, dj) / denominator,
        max(di, dj) / denominator,
        abs((i + j) - 2 * k) / (2.0 * denominator),
        float(k == i),
        float(k == j),
        float(i < k < j),
    ], dtype=np.float32)
    if result.shape != (8,) or not np.isfinite(result).all():
        raise AssertionError("unpaired item must be finite 8D")
    return result


def evidence_features_for_candidate(
    channel: str,
    candidate: tuple[int, int],
    delivered_items: Sequence[Mapping[str, int]],
    sequence_length: int,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Return item matrix, four raw descriptors, and exhaustive frozen scope."""
    if channel not in CHANNELS:
        raise ValueError(channel)
    if channel == "positive_pair":
        items = [
            positive_pair_item_features(candidate, (int(item["i"]), int(item["j"])), sequence_length)
            for item in delivered_items
        ]
        exact_support = any(candidate == (int(item["i"]), int(item["j"])) for item in delivered_items)
        local_conflict = any(
            candidate != (int(item["i"]), int(item["j"]))
            and bool(set(candidate) & {int(item["i"]), int(item["j"])})
            for item in delivered_items
        )
    else:
        items = [
            unpaired_item_features(candidate, int(item["i"]), sequence_length)
            for item in delivered_items
        ]
        exact_support = False
        local_conflict = any(int(item["i"]) in candidate for item in delivered_items)
    matrix = np.stack(items).astype(np.float32) if items else np.zeros((0, ITEM_DIM[channel]), dtype=np.float32)
    count = len(delivered_items)
    descriptors = np.asarray(
        [count, count / sequence_length, float(local_conflict), float(exact_support)],
        dtype=np.float32,
    )
    scope = "DIRECT" if exact_support else "LOCAL_CONFLICT" if local_conflict else "NON_EVIDENCED"
    return matrix, descriptors, scope


@dataclass(frozen=True)
class Preprocessing:
    candidate_mean: np.ndarray
    candidate_std: np.ndarray
    item_mean: np.ndarray
    item_std: np.ndarray
    count_mean: np.ndarray
    count_std: np.ndarray

    def to_json(self) -> dict[str, object]:
        return {
            "candidate_standardized_indices": list(CANDIDATE_STANDARDIZED_INDICES),
            "candidate_mean": self.candidate_mean.tolist(),
            "candidate_std": self.candidate_std.tolist(),
            "item_continuous_mean": self.item_mean.tolist(),
            "item_continuous_std": self.item_std.tolist(),
            "count_mean": self.count_mean.tolist(),
            "count_std": self.count_std.tolist(),
            "std_floor": 1e-8,
            "empty_evidence_override": "68_EXACT_ZEROS_AFTER_PREPROCESSING",
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, object]) -> "Preprocessing":
        return cls(*(
            np.asarray(payload[name], dtype=np.float32)
            for name in (
                "candidate_mean", "candidate_std", "item_continuous_mean",
                "item_continuous_std", "count_mean", "count_std",
            )
        ))


def fit_preprocessing(
    candidates: np.ndarray,
    item_values: np.ndarray,
    descriptors: np.ndarray,
    channel: str,
) -> Preprocessing:
    if candidates.ndim != 2 or candidates.shape[1] != 80:
        raise ValueError("candidate tensor must be [N,80]")
    numeric = candidates[:, CANDIDATE_STANDARDIZED_INDICES]
    candidate_mean = numeric.mean(axis=0, dtype=np.float64).astype(np.float32)
    candidate_std = np.maximum(numeric.std(axis=0, dtype=np.float64), 1e-8).astype(np.float32)
    continuous_dim = ITEM_CONTINUOUS_DIM[channel]
    if len(item_values):
        item_numeric = item_values[:, :continuous_dim]
        item_mean = item_numeric.mean(axis=0, dtype=np.float64).astype(np.float32)
        item_std = np.maximum(item_numeric.std(axis=0, dtype=np.float64), 1e-8).astype(np.float32)
    else:
        raise ValueError("training fold has no evidence-item incidences")
    nonempty = descriptors[:, 0] > 0
    if not nonempty.any():
        raise ValueError("training fold has no nonempty evidence sets")
    count_numeric = descriptors[nonempty, :2]
    count_mean = count_numeric.mean(axis=0, dtype=np.float64).astype(np.float32)
    count_std = np.maximum(count_numeric.std(axis=0, dtype=np.float64), 1e-8).astype(np.float32)
    return Preprocessing(candidate_mean, candidate_std, item_mean, item_std, count_mean, count_std)


def apply_candidate_preprocessing(values: np.ndarray, preprocessing: Preprocessing) -> np.ndarray:
    output = np.asarray(values, dtype=np.float32).copy()
    output[:, CANDIDATE_STANDARDIZED_INDICES] = (
        output[:, CANDIDATE_STANDARDIZED_INDICES] - preprocessing.candidate_mean
    ) / preprocessing.candidate_std
    return output


def apply_item_preprocessing(values: np.ndarray, preprocessing: Preprocessing, channel: str) -> np.ndarray:
    output = np.asarray(values, dtype=np.float32).copy()
    continuous_dim = ITEM_CONTINUOUS_DIM[channel]
    if len(output):
        output[:, :continuous_dim] = (
            output[:, :continuous_dim] - preprocessing.item_mean
        ) / preprocessing.item_std
    return output


def apply_descriptor_preprocessing(values: np.ndarray, preprocessing: Preprocessing) -> np.ndarray:
    output = np.asarray(values, dtype=np.float32).copy()
    nonempty = output[:, 0] > 0
    output[nonempty, :2] = (output[nonempty, :2] - preprocessing.count_mean) / preprocessing.count_std
    output[~nonempty, :] = 0.0
    return output


def split_roles(fold_by_rna: Mapping[str, int], test_fold: int) -> dict[str, set[str]]:
    test_fold = int(test_fold)
    validation_fold = (test_fold + 1) % 5
    roles = {
        "train": {rna for rna, fold in fold_by_rna.items() if fold not in (test_fold, validation_fold)},
        "validation": {rna for rna, fold in fold_by_rna.items() if fold == validation_fold},
        "held_out_test": {rna for rna, fold in fold_by_rna.items() if fold == test_fold},
    }
    if roles["train"] & roles["validation"] or roles["train"] & roles["held_out_test"] or roles["validation"] & roles["held_out_test"]:
        raise AssertionError("RNA split leakage")
    if set().union(*roles.values()) != set(fold_by_rna):
        raise AssertionError("RNA split is incomplete")
    return roles


def safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def mean_defined(values: Iterable[float | None]) -> tuple[float | None, int]:
    defined = [float(value) for value in values if value is not None]
    return ((sum(defined) / len(defined)), len(defined)) if defined else (None, 0)


def prf(tp: int, fp: int, fn: int) -> tuple[float | None, float | None, float | None]:
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def average_precision(scores: Iterable[float], labels: Iterable[int]) -> float | None:
    values = [(float(score), int(label)) for score, label in zip(scores, labels)]
    positives = sum(label == 1 for _, label in values)
    if positives == 0:
        return None
    groups: dict[float, list[int]] = defaultdict(list)
    for score, label in values:
        if not math.isfinite(score) or label not in (0, 1):
            raise ValueError("invalid AUPRC input")
        groups[score].append(label)
    cumulative_positive = cumulative_total = 0
    result = 0.0
    for score in sorted(groups, reverse=True):
        group = groups[score]
        group_positive = sum(group)
        cumulative_positive += group_positive
        cumulative_total += len(group)
        result += (cumulative_positive / cumulative_total) * (group_positive / positives)
    return result


def auroc(scores: Iterable[float], labels: Iterable[int]) -> float | None:
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


def fixed_bin_ece(scores: Sequence[float], labels: Sequence[int]) -> dict[str, object]:
    if len(scores) != len(labels) or not scores:
        raise ValueError("ECE requires equally sized nonempty arrays")
    bins: list[list[tuple[float, int]]] = [[] for _ in range(10)]
    for score, label in zip(scores, labels):
        value = float(score)
        target = int(label)
        if not math.isfinite(value) or not 0 <= value <= 1 or target not in (0, 1):
            raise ValueError("invalid ECE input")
        bins[min(int(value * 10), 9)].append((value, target))
    output = []
    ece = 0.0
    for index, members in enumerate(bins):
        weight = len(members) / len(scores)
        if members:
            mean_score = sum(score for score, _ in members) / len(members)
            observed = sum(label for _, label in members) / len(members)
            gap = abs(mean_score - observed)
        else:
            mean_score = observed = gap = None
        contribution = 0.0 if gap is None else weight * gap
        ece += contribution
        output.append({
            "bin_index": index, "bin_left": index / 10, "bin_right": (index + 1) / 10,
            "right_inclusive": index == 9, "count": len(members), "weight": weight,
            "mean_score": mean_score, "observed_delete_rate": observed,
            "absolute_gap": gap, "ece_contribution": contribution,
        })
    return {"ece": ece, "n_examples": len(scores), "bins": output}


def discrimination(rows: Sequence[Mapping[str, object]], score_key: str = "calibrated_probability") -> dict[str, object]:
    scores = [float(row[score_key]) for row in rows]
    labels = [int(row["label_delete"]) for row in rows]
    return {
        "n_events": len(rows), "positive_count": sum(labels),
        "positive_prevalence": safe_ratio(sum(labels), len(labels)),
        "auprc": average_precision(scores, labels), "auroc": auroc(scores, labels),
        "brier": sum((score - label) ** 2 for score, label in zip(scores, labels)) / len(scores),
        "ece": fixed_bin_ece(scores, labels)["ece"],
    }


def rna_balanced_reliability(rows: Sequence[Mapping[str, object]], score_key: str = "calibrated_probability") -> dict[str, object]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["rna_id"])].append(row)
    per_rna = []
    for rna_id in sorted(grouped):
        result = discrimination(grouped[rna_id], score_key)
        result["rna_id"] = rna_id
        per_rna.append(result)
    output: dict[str, object] = {"rna_count": len(per_rna), "per_rna": per_rna}
    for field in ("positive_prevalence", "auprc", "auroc", "brier", "ece"):
        output[field], output[f"{field}_defined_rnas"] = mean_defined(row[field] for row in per_rna)
    return output


def utility_metrics(
    rows: Sequence[Mapping[str, object]], delete_flags: Sequence[bool]
) -> dict[str, object]:
    if len(rows) != len(delete_flags):
        raise ValueError("rows/delete flags length mismatch")
    contexts: dict[tuple[str, str], dict[str, int | str]] = {}
    for row, delete in zip(rows, delete_flags):
        key = (str(row["manifest_id"]), str(row["source"]))
        gt_count = int(row["gt_pair_count"])
        item = contexts.setdefault(key, {
            "rna_id": str(row["rna_id"]), "gt": gt_count, "tp": 0, "fp": 0,
            "lost_tp": 0, "removed_fp": 0, "pairs": 0,
        })
        if item["gt"] != gt_count or item["rna_id"] != str(row["rna_id"]):
            raise AssertionError("inconsistent context metadata")
        label = int(row["label_delete"])
        item["pairs"] = int(item["pairs"]) + 1
        item["fp" if label else "tp"] = int(item["fp" if label else "tp"]) + 1
        if delete:
            field = "removed_fp" if label else "lost_tp"
            item[field] = int(item[field]) + 1

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
            "tp_after": tp1, "fp_after": fp1, "fn_after": fn1,
            "lost_tp": lost, "removed_fp": removed, "deleted_pair_count": deleted,
            "beneficial_edits": removed, "harmful_edits": lost,
            "tp_preservation": safe_ratio(tp1, tp0), "fp_removal": safe_ratio(removed, fp0),
            "modification_precision": safe_ratio(removed, deleted),
            "coverage": safe_ratio(deleted, tp0 + fp0),
            "resulting_precision": p1, "resulting_recall": r1, "resulting_f1": f1,
            "original_precision": p0, "original_recall": r0, "original_f1": f0,
            "delta_f1": None if f1 is None or f0 is None else f1 - f0,
        }

    event = aggregate(contexts.values())
    by_rna: dict[str, list[Mapping[str, int | str]]] = defaultdict(list)
    for item in contexts.values():
        by_rna[str(item["rna_id"])].append(item)
    per_rna = {rna: aggregate(items) for rna, items in by_rna.items()}
    fields = (
        "tp_preservation", "fp_removal", "modification_precision", "coverage",
        "resulting_precision", "resulting_recall", "resulting_f1",
        "original_precision", "original_recall", "original_f1", "delta_f1",
    )
    balanced: dict[str, object] = {"rna_count": len(per_rna)}
    for field in fields:
        balanced[field], balanced[f"{field}_defined_rnas"] = mean_defined(item[field] for item in per_rna.values())
    for field in ("deleted_pair_count", "lost_tp", "removed_fp", "beneficial_edits", "harmful_edits"):
        balanced[field] = sum(int(item[field]) for item in per_rna.values())
    return {"event_pooled": event, "rna_balanced": balanced, "per_rna": per_rna}


def threshold_search(rows: Sequence[Mapping[str, object]]) -> tuple[float | None, list[dict[str, object]]]:
    """Frozen tie-block threshold search using validation rows only."""
    if not rows or any(str(row["partition"]) != "validation" for row in rows):
        raise AssertionError("threshold selection accepts validation rows only")
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[str(row["rna_id"])].append(index)
    rnas = sorted(grouped)
    rna_index = {rna: index for index, rna in enumerate(rnas)}
    labels = np.asarray([int(row["label_delete"]) for row in rows], dtype=np.int8)
    scores = np.asarray([float(row["calibrated_probability"]) for row in rows], dtype=np.float64)
    rna_ids = np.asarray([rna_index[str(row["rna_id"])] for row in rows], dtype=np.int32)
    tp_total = int((labels == 0).sum())
    fp_total = int((labels == 1).sum())
    tp_by_rna = np.bincount(rna_ids[labels == 0], minlength=len(rnas)).astype(np.int64)
    fp_by_rna = np.bincount(rna_ids[labels == 1], minlength=len(rnas)).astype(np.int64)
    lost_by_rna = np.zeros(len(rnas), dtype=np.int64)
    removed_by_rna = np.zeros(len(rnas), dtype=np.int64)
    lost = removed = 0
    candidates: list[dict[str, object]] = []

    def append_candidate(threshold: float | None) -> None:
        deleted_by_rna = lost_by_rna + removed_by_rna
        tp_values = 1.0 - np.divide(lost_by_rna, tp_by_rna, out=np.zeros(len(rnas)), where=tp_by_rna > 0)
        fp_values = np.divide(removed_by_rna, fp_by_rna, out=np.zeros(len(rnas)), where=fp_by_rna > 0)
        mp_values = np.divide(removed_by_rna, deleted_by_rna, out=np.zeros(len(rnas)), where=deleted_by_rna > 0)
        event_tp = 1.0 - lost / tp_total
        event_fp = removed / fp_total
        rna_tp = float(tp_values[tp_by_rna > 0].mean())
        rna_fp = float(fp_values[fp_by_rna > 0].mean())
        rna_mp = float(mp_values[deleted_by_rna > 0].mean()) if (deleted_by_rna > 0).any() else None
        candidates.append({
            "threshold": threshold,
            "threshold_semantics": "DELETE_NONE" if threshold is None else "DELETE_RISK_GTE",
            "eligible": event_tp >= 0.99 and rna_tp >= 0.99,
            "event_tp_preservation": event_tp,
            "event_fp_removal": event_fp,
            "event_modification_precision": safe_ratio(removed, lost + removed),
            "event_deleted_pair_count": lost + removed,
            "rna_balanced_tp_preservation": rna_tp,
            "rna_balanced_fp_removal": rna_fp,
            "rna_balanced_modification_precision": rna_mp,
        })

    append_candidate(None)
    order = np.argsort(-scores, kind="stable")
    start = 0
    while start < len(order):
        score = scores[order[start]]
        end = start + 1
        while end < len(order) and scores[order[end]] == score:
            end += 1
        block = order[start:end]
        block_labels = labels[block]
        lost += int((block_labels == 0).sum())
        removed += int((block_labels == 1).sum())
        np.add.at(lost_by_rna, rna_ids[block[block_labels == 0]], 1)
        np.add.at(removed_by_rna, rna_ids[block[block_labels == 1]], 1)
        append_candidate(float(score))
        start = end

    eligible = [row for row in candidates if row["eligible"]]
    if not eligible:
        raise AssertionError("delete-none must be eligible")

    def selection_key(row: Mapping[str, object]) -> tuple[float, float, int, float]:
        mp = row["rna_balanced_modification_precision"]
        threshold = math.inf if row["threshold"] is None else float(row["threshold"])
        return (
            float(row["rna_balanced_fp_removal"]),
            -math.inf if mp is None else float(mp),
            -int(row["event_deleted_pair_count"]),
            threshold,
        )

    selected = max(eligible, key=selection_key)
    for row in candidates:
        row["selected"] = row is selected
    return selected["threshold"], candidates


def apply_threshold(probabilities: Sequence[float], threshold: float | None) -> np.ndarray:
    if threshold is None:
        return np.zeros(len(probabilities), dtype=bool)
    return np.asarray(probabilities, dtype=np.float64) >= float(threshold)


def decision_states(
    probabilities: Sequence[float], threshold: float | None, *, artifacts_valid: bool = True
) -> list[str]:
    if not artifacts_valid:
        return ["ABSTAIN_NO_REFINEMENT"] * len(probabilities)
    flags = apply_threshold(probabilities, threshold)
    return ["DELETE" if flag else "KEEP" for flag in flags]


def fit_monotone_platt(logits: Sequence[float], labels: Sequence[int]) -> dict[str, object]:
    """Fit the frozen validation-only sigmoid(a * logit + b), constrained a >= 0."""
    from scipy.optimize import minimize

    x = np.asarray(logits, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int8)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y) or not len(x):
        raise ValueError("Platt calibration requires equal nonempty one-dimensional arrays")
    if not np.isfinite(x).all() or not set(np.unique(y)).issubset({0, 1}):
        raise ValueError("invalid Platt calibration inputs")
    if len(np.unique(y)) != 2:
        raise RuntimeError("validation calibration partition lacks one class")

    def objective(parameters: np.ndarray) -> tuple[float, np.ndarray]:
        a, b = parameters
        z = a * x + b
        loss = np.logaddexp(0.0, z).sum() - np.dot(y, z)
        p = np.empty_like(z)
        nonnegative = z >= 0
        p[nonnegative] = 1.0 / (1.0 + np.exp(-z[nonnegative]))
        exp_z = np.exp(z[~nonnegative])
        p[~nonnegative] = exp_z / (1.0 + exp_z)
        residual = p - y
        gradient = np.asarray([np.dot(residual, x), residual.sum()], dtype=np.float64)
        return float(loss), gradient

    prevalence = float(y.mean())
    initial_b = math.log(prevalence / (1.0 - prevalence))
    fitted = minimize(
        objective, np.asarray([1.0, initial_b], dtype=np.float64), jac=True,
        method="L-BFGS-B", bounds=((0.0, None), (None, None)),
        options={"ftol": 1e-12, "gtol": 1e-8, "maxiter": 1000},
    )
    if not fitted.success or not np.isfinite(fitted.x).all() or fitted.x[0] < 0:
        raise RuntimeError(f"monotone Platt optimization failed: {fitted.message}")
    return {
        "a": float(fitted.x[0]), "b": float(fitted.x[1]),
        "optimization_success": True, "optimizer": "L-BFGS-B",
        "a_constraint": "a >= 0", "validation_example_count": int(len(y)),
        "validation_delete_count": int(y.sum()),
        "validation_keep_count": int(len(y) - y.sum()),
        "objective_sum_binary_log_loss": float(fitted.fun),
        "iterations": int(fitted.nit),
    }


def apply_platt(logits: Sequence[float], a: float, b: float) -> np.ndarray:
    if not math.isfinite(float(a)) or not math.isfinite(float(b)) or float(a) < 0:
        raise ValueError("invalid monotone Platt parameters")
    z = float(a) * np.asarray(logits, dtype=np.float64) + float(b)
    output = np.empty_like(z)
    nonnegative = z >= 0
    output[nonnegative] = 1.0 / (1.0 + np.exp(-z[nonnegative]))
    exp_z = np.exp(z[~nonnegative])
    output[~nonnegative] = exp_z / (1.0 + exp_z)
    return output


def population_summary(values: Sequence[float | None]) -> dict[str, float | int | None]:
    clean = np.asarray([float(value) for value in values if value is not None], dtype=np.float64)
    if not len(clean):
        return {"mean": None, "population_sd": None, "min": None, "max": None, "n": 0}
    return {
        "mean": float(clean.mean()), "population_sd": float(clean.std(ddof=0)),
        "min": float(clean.min()), "max": float(clean.max()), "n": int(len(clean)),
    }


def evaluate_gate_b(
    primary_mean: Mapping[str, float], source_fp_removal: Mapping[str, float],
    p3_source_fp_removal: Mapping[str, float], complete_runs: bool,
) -> dict[str, object]:
    criteria = {
        "event_tp_preservation_gte_0_99": float(primary_mean["event_tp_preservation"]) >= 0.99,
        "rna_tp_preservation_gte_0_99": float(primary_mean["rna_tp_preservation"]) >= 0.99,
        "rna_fp_removal_gt_0_489748": float(primary_mean["rna_fp_removal"]) > 0.489748,
        "event_fp_removal_gt_0_347816": float(primary_mean["event_fp_removal"]) > 0.347816,
    }
    improvements = {
        source: float(source_fp_removal[source]) - float(p3_source_fp_removal[source])
        for source in SOURCES
    }
    positive = [source for source, value in improvements.items() if value > 0.0]
    source_consistent = len(positive) >= 2 and any(source in positive for source in ("rnafold", "petfold"))
    passed = complete_runs and all(criteria.values()) and source_consistent
    return {
        "status": "R4_GATE_B_PASS" if passed else "R4_GATE_B_FAIL",
        "held_out": True,
        "five_seed_mean": True,
        "primary_combined_track_e": True,
        "complete_run_matrix": bool(complete_runs),
        "criteria": criteria,
        "source_fp_removal_improvement_vs_p3": improvements,
        "positive_improvement_sources": positive,
        "source_consistency": source_consistent,
        "strict_fp_removal_inequalities": True,
        "rescue_tuning_performed": False,
    }


def import_torch():
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise RuntimeError("R4 requires an existing PyTorch runtime") from exc
    return torch, nn


def make_ern_model(item_dim: int):
    torch, nn = import_torch()

    class EvidenceReconciliationNetwork(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.item_dim = int(item_dim)
            self.candidate_encoder = nn.Sequential(nn.Linear(80, 64), nn.ReLU())
            self.evidence_item_encoder = nn.Sequential(
                nn.Linear(self.item_dim, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU()
            )
            self.fusion = nn.Sequential(
                nn.Linear(132, 128), nn.ReLU(), nn.Dropout(0.10),
                nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.10), nn.Linear(64, 1),
            )

        def forward(self, candidate, evidence_items, evidence_mask, descriptors, evidence_masked=False):
            candidate_encoded = self.candidate_encoder(candidate)
            batch_size = candidate.shape[0]
            if evidence_masked:
                evidence_block = torch.zeros((batch_size, 68), dtype=candidate.dtype, device=candidate.device)
            else:
                if evidence_items.ndim != 3 or evidence_items.shape[2] != self.item_dim:
                    raise ValueError("invalid padded evidence tensor")
                encoded = self.evidence_item_encoder(evidence_items)
                mask = evidence_mask.unsqueeze(-1)
                masked = encoded * mask
                counts = mask.sum(dim=1)
                mean_pool = masked.sum(dim=1) / counts.clamp(min=1)
                negative_inf = torch.finfo(encoded.dtype).min
                max_pool = encoded.masked_fill(~mask.bool(), negative_inf).max(dim=1).values
                empty = counts.squeeze(-1) == 0
                if empty.any():
                    mean_pool = mean_pool.clone()
                    max_pool = max_pool.clone()
                    mean_pool[empty] = 0.0
                    max_pool[empty] = 0.0
                evidence_block = torch.cat([mean_pool, max_pool, descriptors], dim=1)
                if empty.any():
                    evidence_block = evidence_block.clone()
                    evidence_block[empty] = 0.0
            return self.fusion(torch.cat([candidate_encoded, evidence_block], dim=1)).squeeze(1)

    return EvidenceReconciliationNetwork()
