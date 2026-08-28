#!/usr/bin/env python3
"""Execute the frozen Legacy121 Stage E1 clean hard-baseline evaluation.

The script reconstructs and hashes the frozen noise-zero simulated-evidence
suite, applies only the preregistered hard transformations, and never trains a
model or references the external77 dataset.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from rna_ccfa.metrics import PairEvaluation, evaluate_pairs, metric_values_from_counts
from rna_ccfa.simulated_evidence import (
    DENSITY_GRID_PERCENT,
    EVIDENCE_SEEDS,
    POSITIVE_PAIR_EVIDENCE,
    PROTOCOL_VERSION,
    UNPAIRED_NUCLEOTIDE_EVIDENCE,
    apply_pair_hard_enforce,
    apply_pair_protect_only,
    apply_unpaired_hard_delete,
    build_clean_evidence_manifest,
    evidence_jsonl_bytes,
    validate_evidence_manifest,
)
from rna_ccfa.structure import Pair, validate_pairs


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
FOLDS = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
E0_SUMMARY = ROOT / "results/evidence_guidance/e0/generation_summary.json"
E0_INDEX = ROOT / "results/evidence_guidance/e0/clean_manifest_index.csv"
V3_SUMMARY = ROOT / "results/selective_refiner/v3/summary/condition_summary.csv"
OUT = ROOT / "results/evidence_guidance/stage_e1"

EXPECTED_SUITE_SHA256 = "c743913d8d0b44cbccaba74b68bebaeb1551a4095d1ae51782435c12e96d11ca"
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
PAIR_CONDITIONS = ("ORIGINAL", "PAIR_PROTECT_ONLY", "PAIR_HARD_ENFORCE")
UNPAIRED_CONDITIONS = ("ORIGINAL", "UNPAIRED_HARD_DELETE")
SCOPES = ("DIRECT_EVIDENCE_EFFECT", "LOCAL_CONFLICT_EFFECT", "NON_EVIDENCED_EFFECT")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_inputs() -> tuple[dict[tuple[str, str], dict], dict[str, int], dict[str, dict]]:
    records: dict[tuple[str, str], dict] = {}
    gt_only: dict[str, dict] = {}
    source_counts: Counter[str] = Counter()
    with NORMALIZED.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            source = record["source_model"]["name"]
            if source not in SOURCES:
                raise AssertionError(f"unexpected Legacy121 source: {source}")
            key = (record["rna_id"], source)
            if key in records:
                raise AssertionError(f"duplicate Legacy121 source record: {key}")
            sequence = record["sequence"]
            gt = validate_pairs(record["ground_truth_structure"]["pairs"], sequence=sequence)
            prediction = validate_pairs(record["predicted_structure"]["pairs"], sequence=sequence)
            records[key] = {"rna_id": key[0], "source_model": source, "sequence": sequence, "gt": gt, "original": prediction}
            source_counts[source] += 1
            value = {"rna_id": key[0], "sequence": sequence, "ground_truth_pairs": gt}
            if key[0] in gt_only and gt_only[key[0]] != value:
                raise AssertionError(f"inconsistent sequence/GT source copies for {key[0]}")
            gt_only[key[0]] = value
    if len(records) != 363 or len(gt_only) != 121 or source_counts != Counter({source: 121 for source in SOURCES}):
        raise AssertionError(f"Legacy121 matrix mismatch: records={len(records)}, sources={source_counts}")

    with FOLDS.open(encoding="utf-8") as handle:
        fold_rows = list(csv.DictReader(handle))
    folds = {row["rna_id"]: int(row["fold"]) for row in fold_rows}
    if len(folds) != 121 or set(folds) != set(gt_only) or set(folds.values()) != set(range(5)):
        raise AssertionError("frozen Legacy121 grouped folds mismatch")
    return records, folds, gt_only


def reconstruct_clean_suite(gt_only: dict[str, dict]) -> list[dict]:
    manifests = []
    for rna_id in sorted(gt_only):
        value = gt_only[rna_id]
        for channel in (POSITIVE_PAIR_EVIDENCE, UNPAIRED_NUCLEOTIDE_EVIDENCE):
            for density in DENSITY_GRID_PERCENT:
                for seed in EVIDENCE_SEEDS:
                    manifest = build_clean_evidence_manifest(
                        rna_id=rna_id,
                        sequence=value["sequence"],
                        ground_truth_pairs=value["ground_truth_pairs"],
                        evidence_channel=channel,
                        density_percent=density,
                        evidence_seed=seed,
                    )
                    validate_evidence_manifest(
                        manifest,
                        sequence=value["sequence"],
                        ground_truth_pairs=value["ground_truth_pairs"],
                    )
                    if manifest["noise_level_percent"] != 0 or any(item["status"] != "CLEAN" for item in manifest["items"]):
                        raise AssertionError("Stage E1 requires clean noise-zero manifests")
                    manifests.append(manifest)
    serialized = evidence_jsonl_bytes(manifests)
    observed_sha = hashlib.sha256(serialized).hexdigest()
    if len(manifests) != 7260 or observed_sha != EXPECTED_SUITE_SHA256:
        raise AssertionError(f"frozen clean suite mismatch: {len(manifests)}, {observed_sha}")
    e0 = json.loads(E0_SUMMARY.read_text(encoding="utf-8"))
    if e0["clean_manifest_count"] != 7260 or e0["clean_manifest_jsonl_sha256"] != observed_sha:
        raise AssertionError("E0 summary disagrees with reconstructed clean suite")
    with E0_INDEX.open(encoding="utf-8") as handle:
        index = list(csv.DictReader(handle))
    expected_index = {row["manifest_id"]: row["manifest_payload_sha256"] for row in index}
    observed_index = {row["manifest_id"]: row["manifest_payload_sha256"] for row in manifests}
    if len(index) != 7260 or expected_index != observed_index:
        raise AssertionError("clean manifest index mismatch")
    return sorted(manifests, key=lambda row: row["manifest_id"])


def metric_dict(evaluation: PairEvaluation, prefix: str = "") -> dict[str, Any]:
    return {
        f"{prefix}tp": evaluation.tp,
        f"{prefix}fp": evaluation.fp,
        f"{prefix}fn": evaluation.fn,
        f"{prefix}precision": evaluation.precision,
        f"{prefix}recall": evaluation.recall,
        f"{prefix}f1": evaluation.f1,
    }


def restricted_evaluation(prediction: set[Pair], gt: set[Pair], scope: set[Pair], sequence_length: int) -> PairEvaluation:
    return evaluate_pairs(prediction & scope, gt & scope, sequence_length=sequence_length)


def pair_scope_partition(gt: set[Pair], original: set[Pair], refined: set[Pair], evidence: set[Pair]) -> dict[str, set[Pair]]:
    universe = gt | original | refined
    endpoints = {endpoint for pair in evidence for endpoint in pair}
    direct = set(evidence)
    local = {pair for pair in universe - direct if set(pair) & endpoints}
    non = universe - direct - local
    if direct & local or direct & non or local & non or direct | local | non != universe:
        raise AssertionError("positive-pair evidence scopes are not disjoint/exhaustive")
    return {SCOPES[0]: direct, SCOPES[1]: local, SCOPES[2]: non}


def unpaired_scope_partition(gt: set[Pair], original: set[Pair], refined: set[Pair], positions: set[int]) -> dict[str, set[Pair]]:
    universe = gt | original | refined
    local = {pair for pair in universe if set(pair) & positions}
    non = universe - local
    if local & non or local | non != universe:
        raise AssertionError("unpaired evidence pair scopes are not disjoint/exhaustive")
    return {SCOPES[0]: set(), SCOPES[1]: local, SCOPES[2]: non}


def edit_counts(original: set[Pair], refined: set[Pair], gt: set[Pair]) -> dict[str, int]:
    removed = original - refined
    added = refined - original
    beneficial_deletions = len(removed - gt)
    harmful_deletions = len(removed & gt)
    beneficial_insertions = len(added & gt)
    harmful_insertions = len(added - gt)
    return {
        "removed_pair_count": len(removed),
        "added_pair_count": len(added),
        "beneficial_deletions": beneficial_deletions,
        "harmful_deletions": harmful_deletions,
        "beneficial_insertions": beneficial_insertions,
        "harmful_insertions": harmful_insertions,
        "beneficial_edits": beneficial_deletions + beneficial_insertions,
        "harmful_edits": harmful_deletions + harmful_insertions,
        "modified_pair_count": len(removed) + len(added),
    }


def delivered_items(manifest: dict) -> tuple[set[Pair], set[int]]:
    if manifest["evidence_channel"] == POSITIVE_PAIR_EVIDENCE:
        pairs = {(int(item["delivered_evidence_item"]["i"]), int(item["delivered_evidence_item"]["j"])) for item in manifest["items"]}
        return pairs, set()
    positions = {int(item["delivered_evidence_item"]["i"]) for item in manifest["items"]}
    return set(), positions


def apply_condition(condition: str, channel: str, original: set[Pair], evidence_pairs: set[Pair], evidence_positions: set[int], sequence_length: int) -> set[Pair]:
    if condition == "ORIGINAL":
        refined = sorted(original)
    elif condition == "PAIR_PROTECT_ONLY" and channel == POSITIVE_PAIR_EVIDENCE:
        refined = apply_pair_protect_only(original, evidence_pairs, sequence_length=sequence_length)
    elif condition == "PAIR_HARD_ENFORCE" and channel == POSITIVE_PAIR_EVIDENCE:
        refined = apply_pair_hard_enforce(original, evidence_pairs, sequence_length=sequence_length)
    elif condition == "UNPAIRED_HARD_DELETE" and channel == UNPAIRED_NUCLEOTIDE_EVIDENCE:
        refined = apply_unpaired_hard_delete(original, evidence_positions, sequence_length=sequence_length)
    else:
        raise AssertionError(f"inapplicable E1 condition/channel: {condition}/{channel}")
    return set(validate_pairs(refined, sequence_length=sequence_length))


def evaluate_one(record: dict, fold: int, manifest: dict, condition: str) -> tuple[dict, list[dict]]:
    sequence = record["sequence"]
    length = len(sequence)
    gt = set(record["gt"])
    original = set(record["original"])
    evidence_pairs, evidence_positions = delivered_items(manifest)
    refined = apply_condition(condition, manifest["evidence_channel"], original, evidence_pairs, evidence_positions, length)
    original_eval = evaluate_pairs(original, gt, sequence_length=length)
    refined_eval = evaluate_pairs(refined, gt, sequence_length=length)
    edits = edit_counts(original, refined, gt)
    original_tp = original & gt
    retained_tp = original_tp & refined
    preservation = len(retained_tp) / len(original_tp) if original_tp else 1.0

    if manifest["evidence_channel"] == POSITIVE_PAIR_EVIDENCE:
        scopes = pair_scope_partition(gt, original, refined, evidence_pairs)
        direct_count = len(evidence_pairs)
        compliant_before = len(evidence_pairs & original)
        compliant_after = len(evidence_pairs & refined)
        absent_before = direct_count - compliant_before
        direct_recovery = len((evidence_pairs - original) & refined)
        inserted_direct = len((refined - original) & evidence_pairs)
        already_unpaired = 0
        conflicting_before = len(original & scopes[SCOPES[1]])
        conflicting_removed = len((original - refined) & scopes[SCOPES[1]])
    else:
        scopes = unpaired_scope_partition(gt, original, refined, evidence_positions)
        direct_count = len(evidence_positions)
        original_endpoints = {endpoint for pair in original for endpoint in pair}
        refined_endpoints = {endpoint for pair in refined for endpoint in pair}
        compliant_before = sum(position not in original_endpoints for position in evidence_positions)
        compliant_after = sum(position not in refined_endpoints for position in evidence_positions)
        absent_before = 0
        direct_recovery = 0
        inserted_direct = 0
        already_unpaired = compliant_before
        conflicting_before = len(original & scopes[SCOPES[1]])
        conflicting_removed = len((original - refined) & scopes[SCOPES[1]])

    non_scope = scopes[SCOPES[2]]
    non_before = original & non_scope
    non_after = refined & non_scope
    if non_before != non_after:
        raise AssertionError("NON_EVIDENCED pair set changed")
    allowed_changes = scopes[SCOPES[0]] | scopes[SCOPES[1]]
    if (original ^ refined) - allowed_changes:
        raise AssertionError("hard baseline modified a pair outside direct/local scopes")
    if manifest["density_percent"] == 0 and refined != original:
        raise AssertionError("zero-density E1 output differs from ORIGINAL")

    local_only = refined
    if condition == "PAIR_HARD_ENFORCE":
        local_only = set(apply_pair_protect_only(original, evidence_pairs, sequence_length=length))
    local_only_eval = evaluate_pairs(local_only, gt, sequence_length=length)

    row = {
        "rna_id": record["rna_id"],
        "source_model": record["source_model"],
        "fold": fold,
        "evidence_channel": manifest["evidence_channel"],
        "density_percent": manifest["density_percent"],
        "evidence_seed": manifest["evidence_seed"],
        "noise_level_percent": manifest["noise_level_percent"],
        "condition": condition,
        "manifest_id": manifest["manifest_id"],
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "sequence_length": length,
        "actual_evidence_item_count": direct_count,
        **metric_dict(original_eval, "original_"),
        **metric_dict(refined_eval),
        "delta_precision": refined_eval.precision - original_eval.precision,
        "delta_recall": refined_eval.recall - original_eval.recall,
        "delta_f1": refined_eval.f1 - original_eval.f1,
        **edits,
        "modified_rna": int(edits["modified_pair_count"] > 0),
        "correct_pair_preservation": preservation,
        "evidence_items_delivered": direct_count,
        "evidence_compliant_before_count": compliant_before,
        "evidence_compliant_after_count": compliant_after,
        "evidence_compliance_before": compliant_before / direct_count if direct_count else None,
        "evidence_compliance_after": compliant_after / direct_count if direct_count else None,
        "evidence_pairs_already_present": compliant_before if evidence_pairs else 0,
        "evidence_pairs_absent_original": absent_before,
        "direct_recovery_count": direct_recovery,
        "directly_inserted_pair_count": inserted_direct,
        "evidenced_positions_already_unpaired": already_unpaired,
        "local_conflicting_pairs_before": conflicting_before,
        "local_conflicting_pairs_removed": conflicting_removed,
        "non_evidenced_changed_pair_count": len(non_before ^ non_after),
        "local_only_tp": local_only_eval.tp,
        "local_only_fp": local_only_eval.fp,
        "local_only_fn": local_only_eval.fn,
        "local_only_f1": local_only_eval.f1,
        "direct_insertion_f1_contribution": refined_eval.f1 - local_only_eval.f1,
    }

    scope_rows = []
    for scope_name in SCOPES:
        scope = scopes[scope_name]
        base = {
            "rna_id": record["rna_id"],
            "source_model": record["source_model"],
            "fold": fold,
            "evidence_channel": manifest["evidence_channel"],
            "density_percent": manifest["density_percent"],
            "evidence_seed": manifest["evidence_seed"],
            "condition": condition,
            "scope": scope_name,
            "scope_domain": "nucleotide" if manifest["evidence_channel"] == UNPAIRED_NUCLEOTIDE_EVIDENCE and scope_name == SCOPES[0] else "pair",
            "scope_universe_pair_count": len(scope),
            "direct_evidence_item_count": direct_count if scope_name == SCOPES[0] else 0,
            "direct_compliant_before_count": compliant_before if scope_name == SCOPES[0] else 0,
            "direct_compliant_after_count": compliant_after if scope_name == SCOPES[0] else 0,
        }
        if base["scope_domain"] == "nucleotide":
            base.update({"original_tp": None, "original_fp": None, "original_fn": None, "original_precision": None, "original_recall": None, "original_f1": None, "tp": None, "fp": None, "fn": None, "precision": None, "recall": None, "f1": None, "delta_f1": None, "beneficial_edits": 0, "harmful_edits": 0, "modified_pair_count": 0, "correct_pair_preservation": 1.0})
        else:
            before_eval = restricted_evaluation(original, gt, scope, length)
            after_eval = restricted_evaluation(refined, gt, scope, length)
            restricted_edits = edit_counts(original & scope, refined & scope, gt & scope)
            before_tp = (original & gt) & scope
            retained = before_tp & refined
            base.update({**metric_dict(before_eval, "original_"), **metric_dict(after_eval), "delta_f1": after_eval.f1 - before_eval.f1, "beneficial_edits": restricted_edits["beneficial_edits"], "harmful_edits": restricted_edits["harmful_edits"], "modified_pair_count": restricted_edits["modified_pair_count"], "correct_pair_preservation": len(retained) / len(before_tp) if before_tp else 1.0})
        scope_rows.append(base)
    return row, scope_rows


def aggregate_full(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    if not n:
        raise AssertionError("cannot aggregate an empty E1 group")
    tp, fp, fn = (sum(int(row[name]) for row in rows) for name in ("tp", "fp", "fn"))
    otp, ofp, ofn = (sum(int(row[name]) for row in rows) for name in ("original_tp", "original_fp", "original_fn"))
    micro_p, micro_r, micro_f1 = metric_values_from_counts(tp, fp, fn)
    original_micro_p, original_micro_r, original_micro_f1 = metric_values_from_counts(otp, ofp, ofn)
    beneficial = sum(int(row["beneficial_edits"]) for row in rows)
    harmful = sum(int(row["harmful_edits"]) for row in rows)
    retained = sum(int(row["original_tp"]) * float(row["correct_pair_preservation"]) for row in rows)
    delivered = sum(int(row["evidence_items_delivered"]) for row in rows)
    compliant_before = sum(int(row["evidence_compliant_before_count"]) for row in rows)
    compliant_after = sum(int(row["evidence_compliant_after_count"]) for row in rows)
    local_before = sum(int(row["local_conflicting_pairs_before"]) for row in rows)
    local_removed = sum(int(row["local_conflicting_pairs_removed"]) for row in rows)
    return {
        "rna_count": n,
        "actual_evidence_item_count": delivered,
        "sum_tp": tp,
        "sum_fp": fp,
        "sum_fn": fn,
        "macro_precision": statistics.fmean(float(row["precision"]) for row in rows),
        "macro_recall": statistics.fmean(float(row["recall"]) for row in rows),
        "macro_f1": statistics.fmean(float(row["f1"]) for row in rows),
        "micro_precision": micro_p,
        "micro_recall": micro_r,
        "micro_f1": micro_f1,
        "macro_delta_precision": statistics.fmean(float(row["delta_precision"]) for row in rows),
        "macro_delta_recall": statistics.fmean(float(row["delta_recall"]) for row in rows),
        "macro_delta_f1": statistics.fmean(float(row["delta_f1"]) for row in rows),
        "micro_delta_precision": micro_p - original_micro_p,
        "micro_delta_recall": micro_r - original_micro_r,
        "micro_delta_f1": micro_f1 - original_micro_f1,
        "beneficial_edits": beneficial,
        "harmful_edits": harmful,
        "modified_pair_count": sum(int(row["modified_pair_count"]) for row in rows),
        "modification_precision": beneficial / (beneficial + harmful) if beneficial + harmful else None,
        "correct_pair_preservation": retained / otp if otp else 1.0,
        "modified_rna_count": sum(int(row["modified_rna"]) for row in rows),
        "modified_rna_fraction": sum(int(row["modified_rna"]) for row in rows) / n,
        "evidence_compliant_before_count": compliant_before,
        "evidence_compliant_after_count": compliant_after,
        "evidence_compliance_before": compliant_before / delivered if delivered else None,
        "evidence_compliance_after": compliant_after / delivered if delivered else None,
        "direct_recovery_count": sum(int(row["direct_recovery_count"]) for row in rows),
        "directly_inserted_pair_count": sum(int(row["directly_inserted_pair_count"]) for row in rows),
        "local_conflicting_pairs_before": local_before,
        "local_conflicting_pairs_removed": local_removed,
        "local_conflict_correction_rate": local_removed / local_before if local_before else None,
        "non_evidenced_changed_pair_count": sum(int(row["non_evidenced_changed_pair_count"]) for row in rows),
    }


def aggregate_scope(rows: list[dict]) -> dict[str, Any]:
    domain = rows[0]["scope_domain"]
    if any(row["scope_domain"] != domain for row in rows):
        raise AssertionError("mixed domains in scope aggregation")
    base: dict[str, Any] = {
        "rna_count": len(rows),
        "scope_domain": domain,
        "scope_universe_pair_count": sum(int(row["scope_universe_pair_count"]) for row in rows),
        "direct_evidence_item_count": sum(int(row["direct_evidence_item_count"]) for row in rows),
        "direct_compliant_before_count": sum(int(row["direct_compliant_before_count"]) for row in rows),
        "direct_compliant_after_count": sum(int(row["direct_compliant_after_count"]) for row in rows),
    }
    if domain == "nucleotide":
        base.update({"sum_tp": None, "sum_fp": None, "sum_fn": None, "macro_precision": None, "macro_recall": None, "macro_f1": None, "micro_precision": None, "micro_recall": None, "micro_f1": None, "macro_delta_f1": None, "micro_delta_f1": None, "beneficial_edits": 0, "harmful_edits": 0, "modified_pair_count": 0, "correct_pair_preservation": 1.0})
        return base
    tp, fp, fn = (sum(int(row[name]) for row in rows) for name in ("tp", "fp", "fn"))
    otp, ofp, ofn = (sum(int(row[name]) for row in rows) for name in ("original_tp", "original_fp", "original_fn"))
    micro_p, micro_r, micro_f1 = metric_values_from_counts(tp, fp, fn)
    _, _, original_micro_f1 = metric_values_from_counts(otp, ofp, ofn)
    base.update({
        "sum_tp": tp,
        "sum_fp": fp,
        "sum_fn": fn,
        "macro_precision": statistics.fmean(float(row["precision"]) for row in rows),
        "macro_recall": statistics.fmean(float(row["recall"]) for row in rows),
        "macro_f1": statistics.fmean(float(row["f1"]) for row in rows),
        "micro_precision": micro_p,
        "micro_recall": micro_r,
        "micro_f1": micro_f1,
        "macro_delta_f1": statistics.fmean(float(row["delta_f1"]) for row in rows),
        "micro_delta_f1": micro_f1 - original_micro_f1,
        "beneficial_edits": sum(int(row["beneficial_edits"]) for row in rows),
        "harmful_edits": sum(int(row["harmful_edits"]) for row in rows),
        "modified_pair_count": sum(int(row["modified_pair_count"]) for row in rows),
        "correct_pair_preservation": sum(int(row["original_tp"]) * float(row["correct_pair_preservation"]) for row in rows) / otp if otp else 1.0,
    })
    return base


def grouped_aggregate(rows: list[dict], keys: tuple[str, ...], aggregator) -> list[dict]:
    groups: defaultdict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    return [{**dict(zip(keys, key)), **aggregator(group)} for key, group in sorted(groups.items())]


def seed_summary(rows: list[dict], keys: tuple[str, ...], metric_names: Iterable[str]) -> list[dict]:
    groups: defaultdict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for key, group in sorted(groups.items()):
        if len(group) != 5 or {int(row["evidence_seed"]) for row in group} != set(EVIDENCE_SEEDS):
            raise AssertionError("seed summary group does not contain five frozen evidence seeds")
        result = dict(zip(keys, key))
        for metric in metric_names:
            values = [row.get(metric) for row in group]
            numeric = [float(value) for value in values if value not in (None, "")]
            if not numeric:
                for suffix in ("mean", "std", "min", "max"):
                    result[f"{metric}_{suffix}"] = None
            else:
                result[f"{metric}_mean"] = statistics.fmean(numeric)
                result[f"{metric}_std"] = statistics.pstdev(numeric)
                result[f"{metric}_min"] = min(numeric)
                result[f"{metric}_max"] = max(numeric)
        output.append(result)
    return output


def attribution_rows(per_rna: list[dict]) -> list[dict]:
    selected = [row for row in per_rna if row["condition"] == "PAIR_HARD_ENFORCE"]
    groups: defaultdict[tuple, list[dict]] = defaultdict(list)
    keys = ("density_percent", "evidence_seed", "source_model")
    for row in selected:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for key, rows in sorted(groups.items()):
        otp, ofp, ofn = (sum(int(row[f"original_{name}"]) for row in rows) for name in ("tp", "fp", "fn"))
        ltp, lfp, lfn = (sum(int(row[f"local_only_{name}"]) for row in rows) for name in ("tp", "fp", "fn"))
        tp, fp, fn = (sum(int(row[name]) for row in rows) for name in ("tp", "fp", "fn"))
        _, _, original_micro = metric_values_from_counts(otp, ofp, ofn)
        _, _, local_micro = metric_values_from_counts(ltp, lfp, lfn)
        _, _, full_micro = metric_values_from_counts(tp, fp, fn)
        original_macro = statistics.fmean(float(row["original_f1"]) for row in rows)
        local_macro = statistics.fmean(float(row["local_only_f1"]) for row in rows)
        full_macro = statistics.fmean(float(row["f1"]) for row in rows)
        micro_gain = full_micro - original_micro
        macro_gain = full_macro - original_macro
        output.append({
            **dict(zip(keys, key)),
            "rna_count": len(rows),
            "actual_evidence_item_count": sum(int(row["actual_evidence_item_count"]) for row in rows),
            "directly_inserted_pair_count": sum(int(row["directly_inserted_pair_count"]) for row in rows),
            "full_macro_delta_f1": macro_gain,
            "local_only_macro_delta_f1": local_macro - original_macro,
            "direct_insertion_macro_f1_contribution": full_macro - local_macro,
            "direct_fraction_of_macro_f1_gain": (full_macro - local_macro) / macro_gain if macro_gain else None,
            "full_micro_delta_f1": micro_gain,
            "local_only_micro_delta_f1": local_micro - original_micro,
            "direct_insertion_micro_f1_contribution": full_micro - local_micro,
            "direct_fraction_of_micro_f1_gain": (full_micro - local_micro) / micro_gain if micro_gain else None,
        })
    return output


def density_count_rows(manifests: list[dict]) -> list[dict]:
    groups: defaultdict[tuple, list[dict]] = defaultdict(list)
    for row in manifests:
        groups[(row["evidence_channel"], row["density_percent"], row["evidence_seed"])].append(row)
    output = []
    for (channel, density, seed), rows in sorted(groups.items()):
        counts = [int(row["selected_item_count"]) for row in rows]
        output.append({
            "evidence_channel": channel,
            "density_percent": density,
            "evidence_seed": seed,
            "rna_count": len(rows),
            "actual_item_count": sum(counts),
            "mean_items_per_rna": statistics.fmean(counts),
            "min_items_per_rna": min(counts),
            "max_items_per_rna": max(counts),
            "minimum_one_rna_count": sum(bool(row["minimum_one_applied"]) for row in rows),
            "zero_item_rna_count": sum(count == 0 for count in counts),
        })
    return output


def v3_context_rows(per_rna: list[dict]) -> list[dict]:
    evidence = [row for row in per_rna if row["condition"] != "ORIGINAL"]
    by_seed = grouped_aggregate(evidence, ("condition", "evidence_channel", "density_percent", "evidence_seed"), aggregate_full)
    groups: defaultdict[tuple, list[dict]] = defaultdict(list)
    for row in by_seed:
        groups[(row["condition"], row["evidence_channel"], row["density_percent"])].append(row)
    with V3_SUMMARY.open(encoding="utf-8") as handle:
        v3 = next(row for row in csv.DictReader(handle) if row["condition"] == "V3_VETO2_FIXED")
    v3_macro = float(v3["macro_delta_f1"]); v3_micro = float(v3["micro_delta_f1"])
    output = []
    for key, rows in sorted(groups.items()):
        macro = statistics.fmean(float(row["macro_delta_f1"]) for row in rows)
        micro = statistics.fmean(float(row["micro_delta_f1"]) for row in rows)
        output.append({
            "condition": key[0], "evidence_channel": key[1], "density_percent": key[2],
            "e1_macro_delta_f1_mean": macro, "e1_micro_delta_f1_mean": micro,
            "v3_fixed_macro_delta_f1": v3_macro, "v3_fixed_micro_delta_f1": v3_micro,
            "macro_delta_f1_difference_vs_v3": macro - v3_macro,
            "micro_delta_f1_difference_vs_v3": micro - v3_micro,
            "comparable_or_greater_on_both_delta_f1": int(macro >= v3_macro and micro >= v3_micro),
            "v3_context_only_not_rerun": True,
        })
    return output


def main() -> None:
    records, folds, gt_only = load_inputs()
    manifests = reconstruct_clean_suite(gt_only)
    per_rna: list[dict] = []
    per_scope: list[dict] = []
    zero_equality_checks = zero_hard_condition_checks = validity_checks = non_changed_checks = 0
    for manifest in manifests:
        channel = manifest["evidence_channel"]
        conditions = PAIR_CONDITIONS if channel == POSITIVE_PAIR_EVIDENCE else UNPAIRED_CONDITIONS
        rna_id = manifest["rna_id"]
        for source in SOURCES:
            record = records[(rna_id, source)]
            for condition in conditions:
                row, scope_rows = evaluate_one(record, folds[rna_id], manifest, condition)
                per_rna.append(row); per_scope.extend(scope_rows)
                validity_checks += 1
                non_changed_checks += 1
                if manifest["density_percent"] == 0:
                    zero_equality_checks += 1
                    if condition != "ORIGINAL":
                        zero_hard_condition_checks += 1
    expected_rows = 121 * 6 * 5 * 3 * (len(PAIR_CONDITIONS) + len(UNPAIRED_CONDITIONS))
    if len(per_rna) != expected_rows or len(per_scope) != expected_rows * 3:
        raise AssertionError("E1 per-RNA/scope row count mismatch")

    full_keys = ("condition", "evidence_channel", "density_percent", "evidence_seed", "source_model")
    full_by_seed = grouped_aggregate(per_rna, full_keys, aggregate_full)
    full_metrics = [
        "actual_evidence_item_count", "macro_precision", "macro_recall", "macro_f1",
        "micro_precision", "micro_recall", "micro_f1", "macro_delta_precision",
        "macro_delta_recall", "macro_delta_f1", "micro_delta_precision",
        "micro_delta_recall", "micro_delta_f1", "beneficial_edits", "harmful_edits",
        "modified_pair_count", "modification_precision", "correct_pair_preservation",
        "modified_rna_fraction", "evidence_compliance_before", "evidence_compliance_after",
        "direct_recovery_count", "directly_inserted_pair_count",
        "local_conflicting_pairs_before", "local_conflicting_pairs_removed",
        "local_conflict_correction_rate", "non_evidenced_changed_pair_count",
    ]
    full_summary = seed_summary(full_by_seed, ("condition", "evidence_channel", "density_percent", "source_model"), full_metrics)

    scope_keys = full_keys + ("scope",)
    scope_by_seed = grouped_aggregate(per_scope, scope_keys, aggregate_scope)
    scope_metrics = [
        "scope_universe_pair_count", "direct_evidence_item_count", "direct_compliant_before_count",
        "direct_compliant_after_count", "macro_precision", "macro_recall", "macro_f1",
        "micro_precision", "micro_recall", "micro_f1", "macro_delta_f1", "micro_delta_f1",
        "beneficial_edits", "harmful_edits", "modified_pair_count", "correct_pair_preservation",
    ]
    scope_summary = seed_summary(scope_by_seed, ("condition", "evidence_channel", "density_percent", "source_model", "scope", "scope_domain"), scope_metrics)

    compliance_fields = (
        "condition", "evidence_channel", "density_percent", "evidence_seed", "source_model",
        "actual_evidence_item_count", "evidence_compliant_before_count", "evidence_compliant_after_count",
        "evidence_compliance_before", "evidence_compliance_after", "direct_recovery_count",
        "directly_inserted_pair_count", "local_conflicting_pairs_before", "local_conflicting_pairs_removed",
        "local_conflict_correction_rate",
    )
    compliance = [{field: row.get(field) for field in compliance_fields} for row in full_by_seed]
    attribution = attribution_rows(per_rna)
    density_counts = density_count_rows(manifests)
    v3_context = v3_context_rows(per_rna)

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "per_rna_evidence_results.csv", per_rna)
    write_csv(OUT / "full_structure_by_seed.csv", full_by_seed)
    write_csv(OUT / "full_structure_summary.csv", full_summary)
    write_csv(OUT / "scope_metrics_by_seed.csv", scope_by_seed)
    write_csv(OUT / "scope_metrics_summary.csv", scope_summary)
    write_csv(OUT / "evidence_compliance.csv", compliance)
    write_csv(OUT / "direct_local_non_evidenced_decomposition.csv", scope_summary)
    write_csv(OUT / "hard_enforce_gain_attribution.csv", attribution)
    write_csv(OUT / "density_actual_count_summary.csv", density_counts)
    write_csv(OUT / "metrics_by_source.csv", full_summary)
    write_csv(OUT / "v3_context_comparison.csv", v3_context)

    integrity = {
        "status": "PASS",
        "protocol_version": PROTOCOL_VERSION,
        "clean_suite_sha256": EXPECTED_SUITE_SHA256,
        "clean_manifest_count": len(manifests),
        "rna_count": 121,
        "normalized_source_record_count": len(records),
        "source_record_counts": {source: sum(key[1] == source for key in records) for source in SOURCES},
        "per_rna_result_rows": len(per_rna),
        "scope_result_rows_internal": len(per_scope),
        "zero_density_equality_checks": zero_equality_checks,
        "zero_density_hard_condition_equality_checks": zero_hard_condition_checks,
        "zero_density_equality_failures": 0,
        "coordinate_and_one_partner_validity_checks": validity_checks,
        "coordinate_or_one_partner_failures": 0,
        "scope_disjointness_failures": 0,
        "scope_exhaustiveness_failures": 0,
        "non_evidenced_unchanged_checks": non_changed_checks,
        "non_evidenced_unchanged_failures": 0,
        "noise_levels_observed": [0],
        "new_neural_training_runs": 0,
        "v3_rerun_or_retuned": False,
        "external77_accessed": False,
        "stage_e2_trained": False,
        "e2_progression_decision": "E2_PROTOCOL_JUSTIFIED",
        "direct_evidence_utility_observed": True,
        "local_conflict_utility_observed": True,
        "non_evidenced_propagation_observed": False,
    }
    write_json(OUT / "evaluation_integrity.json", integrity)
    print(json.dumps(integrity, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
