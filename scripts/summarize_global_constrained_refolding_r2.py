#!/usr/bin/env python3
"""Run the first formal R2 B0/B1/B2 summary on the complete v1.0.2 universe."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from rna_ccfa.global_refolding_r2 import (
    PAIR_CHANNEL,
    R2_PROTOCOL_VERSION,
    UNPAIRED_CHANNEL,
    full_refold_edit_decomposition,
    pair_scope_partition,
    safe_ratio,
    unpaired_scope_partition,
)
from rna_ccfa.metrics import evaluate_pairs, metric_values_from_counts
from rna_ccfa.structure import Pair, validate_pairs


ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "results/global_constrained_refolding_r2"
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
MANIFESTS = ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl"
ELIGIBILITY = R2 / "integrity/r2_manifest_eligibility_v1_0_2.csv"
ELIGIBILITY_SUMMARY = R2 / "integrity/r2_eligibility_summary_v1_0_2.json"
MATCHED_B1 = R2 / "integrity/r2_matched_b1_view_v1_0_2.csv"
MATCHED_B0 = R2 / "integrity/r2_matched_b0_view_v1_0_2.csv"
MATCHED_SUMMARY = R2 / "integrity/r2_matched_universe_summary_v1_0_2.json"
COMPLETION = R2 / "integrity/execution_completion_v1_0_2.json"
B2_STRUCTURES = R2 / "parsed/b2_structures_v1_0_2.csv"
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
METHODS = ("B0_ORIGINAL", "B1_LOCAL_HARD", "B2_GLOBAL_REFOLD")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row)) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def load_records() -> dict[tuple[str, str], dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    with NORMALIZED.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            source = record["source_model"]["name"]
            if source not in SOURCES:
                raise AssertionError(f"unexpected source: {source}")
            sequence = record["sequence"]
            key = (record["rna_id"], source)
            records[key] = {
                "rna_id": record["rna_id"],
                "source_model": source,
                "sequence": sequence,
                "ground_truth": set(
                    validate_pairs(record["ground_truth_structure"]["pairs"], sequence=sequence)
                ),
                "original": set(
                    validate_pairs(record["predicted_structure"]["pairs"], sequence=sequence)
                ),
            }
    if len(records) != 363:
        raise AssertionError(f"expected 363 normalized source records, found {len(records)}")
    return records


def load_manifests() -> dict[str, dict[str, Any]]:
    manifests = {
        row["manifest_id"]: row
        for row in (json.loads(line) for line in MANIFESTS.open(encoding="utf-8") if line.strip())
    }
    if len(manifests) != 7260:
        raise AssertionError("clean manifest universe mismatch")
    return manifests


def delivered_items(manifest: dict[str, Any]) -> tuple[set[Pair], set[int]]:
    if manifest["evidence_channel"] == PAIR_CHANNEL:
        return {
            (
                int(item["delivered_evidence_item"]["i"]),
                int(item["delivered_evidence_item"]["j"]),
            )
            for item in manifest["items"]
        }, set()
    return set(), {
        int(item["delivered_evidence_item"]["i"]) for item in manifest["items"]
    }


def load_b2() -> dict[str, dict[str, Any]]:
    with B2_STRUCTURES.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    output = {}
    for row in rows:
        if row["status"] != "PASS" or row["constraint_satisfied"] != "True":
            raise AssertionError(f"non-PASS row in formal B2 structures: {row['manifest_id']}")
        row["pairs"] = {tuple(pair) for pair in json.loads(row["pairs_zero_based_json"])}
        output[row["manifest_id"]] = row
    if len(output) != 7153:
        raise AssertionError(f"expected 7153 complete eligible B2 structures, found {len(output)}")
    return output


def primary_b1_condition(channel: str) -> str:
    if channel == PAIR_CHANNEL:
        return "PAIR_HARD_ENFORCE"
    if channel == UNPAIRED_CHANNEL:
        return "UNPAIRED_HARD_DELETE"
    raise AssertionError(f"unexpected channel: {channel}")


def load_matched_rows() -> tuple[dict[tuple[str, str], dict[str, str]], set[str]]:
    with MATCHED_B1.open(encoding="utf-8", newline="") as handle:
        all_b1 = list(csv.DictReader(handle))
    primary = {
        (row["manifest_id"], row["source_model"]): row
        for row in all_b1
        if row["condition"] == primary_b1_condition(row["evidence_channel"])
    }
    with MATCHED_B0.open(encoding="utf-8", newline="") as handle:
        b0_rows = list(csv.DictReader(handle))
    b0_keys = {(row["manifest_id"], row["source_model"]) for row in b0_rows}
    if len(primary) != 21459 or len(b0_keys) != 21459 or set(primary) != b0_keys:
        raise AssertionError("formal matched B0/primary-B1 key universe mismatch")
    return primary, {manifest_id for manifest_id, _ in b0_keys}


def metric_fields(prefix: str, evaluation) -> dict[str, Any]:
    return {
        f"{prefix}tp": evaluation.tp,
        f"{prefix}fp": evaluation.fp,
        f"{prefix}fn": evaluation.fn,
        f"{prefix}precision": evaluation.precision,
        f"{prefix}recall": evaluation.recall,
        f"{prefix}f1": evaluation.f1,
    }


def count_parts(parts: dict[str, set[Pair]]) -> dict[str, int]:
    result = {key: len(value) for key, value in parts.items()}
    result["beneficial_changes"] = result["removed_fp"] + result["new_tp"]
    result["harmful_changes"] = result["lost_tp"] + result["new_fp"]
    result["modified_pair_count"] = result["beneficial_changes"] + result["harmful_changes"]
    return result


def method_row(
    base: dict[str, Any],
    method: str,
    *,
    tp: int,
    fp: int,
    fn: int,
    original_tp: int,
    original_fp: int,
    original_fn: int,
    preserved_tp: int,
    lost_tp: int,
    removed_fp: int,
    preserved_original_fp: int,
    new_tp: int,
    new_fp: int,
    unchanged_pairs: int,
    deleted_pairs: int,
    added_pairs: int,
    b0_f1: float,
) -> dict[str, Any]:
    precision, recall, f1 = metric_values_from_counts(tp, fp, fn)
    beneficial = removed_fp + new_tp
    harmful = lost_tp + new_fp
    modified = beneficial + harmful
    evidence_count = int(base["evidence_item_count"])
    return {
        **base,
        "method": method,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "original_tp": original_tp,
        "original_fp": original_fp,
        "original_fn": original_fn,
        "preserved_tp": preserved_tp,
        "lost_tp": lost_tp,
        "removed_fp": removed_fp,
        "preserved_original_fp": preserved_original_fp,
        "new_tp": new_tp,
        "new_fp": new_fp,
        "unchanged_pairs": unchanged_pairs,
        "deleted_pairs": deleted_pairs,
        "added_pairs": added_pairs,
        "beneficial_changes": beneficial,
        "harmful_changes": harmful,
        "modified_pair_count": modified,
        "tp_preservation": safe_ratio(preserved_tp, original_tp),
        "fp_removal": safe_ratio(removed_fp, original_fp),
        "modification_precision": safe_ratio(beneficial, modified),
        "fp_removed_per_evidence_item": safe_ratio(removed_fp, evidence_count),
        "delta_f1_vs_b0": f1 - b0_f1,
        "delta_f1_per_evidence_item": safe_ratio(f1 - b0_f1, evidence_count),
    }


COUNT_FIELDS = (
    "tp",
    "fp",
    "fn",
    "original_tp",
    "original_fp",
    "original_fn",
    "preserved_tp",
    "lost_tp",
    "removed_fp",
    "preserved_original_fp",
    "new_tp",
    "new_fp",
    "unchanged_pairs",
    "deleted_pairs",
    "added_pairs",
    "beneficial_changes",
    "harmful_changes",
    "modified_pair_count",
    "evidence_item_count",
)


def pooled_values(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sums = {field: sum(int(row[field]) for row in rows) for field in COUNT_FIELDS}
    precision, recall, f1 = metric_values_from_counts(sums["tp"], sums["fp"], sums["fn"])
    return {
        **sums,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp_preservation": safe_ratio(sums["preserved_tp"], sums["original_tp"]),
        "fp_removal": safe_ratio(sums["removed_fp"], sums["original_fp"]),
        "modification_precision": safe_ratio(
            sums["beneficial_changes"], sums["modified_pair_count"]
        ),
        "fp_removed_per_evidence_item": safe_ratio(
            sums["removed_fp"], sums["evidence_item_count"]
        ),
    }


def mean_defined(values: Iterable[float | None]) -> float | None:
    defined = [float(value) for value in values if value is not None]
    return statistics.fmean(defined) if defined else None


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    micro = pooled_values(rows)
    by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_rna[row["rna_id"]].append(row)
    rna_values = [pooled_values(group) for group in by_rna.values()]
    result: dict[str, Any] = {
        "eligible_realization_count": len(rows),
        "eligible_rna_count": len(by_rna),
        "missing_rna_count": 121 - len(by_rna),
    }
    for field in COUNT_FIELDS:
        result[f"sum_{field}"] = micro[field]
    for metric in (
        "precision",
        "recall",
        "f1",
        "tp_preservation",
        "fp_removal",
        "modification_precision",
        "fp_removed_per_evidence_item",
    ):
        result[f"micro_{metric}"] = micro[metric]
        result[f"macro_{metric}"] = mean_defined(value[metric] for value in rna_values)
        result[f"macro_{metric}_defined_rna_count"] = sum(
            value[metric] is not None for value in rna_values
        )
    return result


def grouped_summary(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: defaultdict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    output = [
        {**dict(zip(keys, key)), **summarize_group(group)}
        for key, group in sorted(groups.items())
    ]
    non_method_keys = tuple(key for key in keys if key != "method")
    if "method" in keys:
        baselines = {
            tuple(row[key] for key in non_method_keys): row
            for row in output
            if row["method"] == "B0_ORIGINAL"
        }
        b1 = {
            tuple(row[key] for key in non_method_keys): row
            for row in output
            if row["method"] == "B1_LOCAL_HARD"
        }
        for row in output:
            key = tuple(row[name] for name in non_method_keys)
            if key not in baselines or key not in b1:
                # Some diagnostic tables intentionally contain B2 rows only.
                continue
            row["macro_delta_f1_vs_b0"] = row["macro_f1"] - baselines[key]["macro_f1"]
            row["micro_delta_f1_vs_b0"] = row["micro_f1"] - baselines[key]["micro_f1"]
            row["macro_delta_f1_vs_b1"] = row["macro_f1"] - b1[key]["macro_f1"]
            row["micro_delta_f1_vs_b1"] = row["micro_f1"] - b1[key]["micro_f1"]
            row["micro_delta_f1_per_evidence_item"] = safe_ratio(
                row["micro_delta_f1_vs_b0"], row["sum_evidence_item_count"]
            )

            method_key = tuple(row[name] for name in keys)
            baseline_key = tuple(
                "B0_ORIGINAL" if name == "method" else row[name] for name in keys
            )
            method_by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
            baseline_by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
            for item in groups[method_key]:
                method_by_rna[item["rna_id"]].append(item)
            for item in groups[baseline_key]:
                baseline_by_rna[item["rna_id"]].append(item)
            per_rna_efficiency = []
            for rna_id, method_group in method_by_rna.items():
                method_pooled = pooled_values(method_group)
                baseline_pooled = pooled_values(baseline_by_rna[rna_id])
                per_rna_efficiency.append(
                    safe_ratio(
                        method_pooled["f1"] - baseline_pooled["f1"],
                        method_pooled["evidence_item_count"],
                    )
                )
            row["macro_delta_f1_per_evidence_item"] = mean_defined(per_rna_efficiency)
            row["macro_delta_f1_per_evidence_item_defined_rna_count"] = sum(
                value is not None for value in per_rna_efficiency
            )
    return output


def scope_row(
    base: dict[str, Any],
    scope_name: str,
    scope: set[Pair],
    *,
    sequence_length: int,
    original: set[Pair],
    truth: set[Pair],
    refolded: set[Pair],
    scope_domain: str,
    direct_compliance_before: int,
    direct_compliance_b2: int,
) -> dict[str, Any]:
    source = original & scope
    gt = truth & scope
    result = refolded & scope
    original_eval = evaluate_pairs(source, gt, sequence_length=sequence_length)
    result_eval = evaluate_pairs(result, gt, sequence_length=sequence_length)
    counts = count_parts(
        full_refold_edit_decomposition(source, gt, result, sequence_length=sequence_length)
    )
    row = {
        **base,
        "scope": scope_name,
        "scope_domain": scope_domain,
        "scope_universe_pair_count": len(scope),
        "direct_compliance_before_count": direct_compliance_before,
        "direct_compliance_b2_count": direct_compliance_b2,
        "original_tp": original_eval.tp,
        "original_fp": original_eval.fp,
        "original_fn": original_eval.fn,
        "tp": result_eval.tp,
        "fp": result_eval.fp,
        "fn": result_eval.fn,
        **counts,
    }
    row.update(
        {
            "precision": result_eval.precision,
            "recall": result_eval.recall,
            "f1": result_eval.f1,
            "tp_preservation": safe_ratio(counts["preserved_tp"], original_eval.tp),
            "fp_removal": safe_ratio(counts["removed_fp"], original_eval.fp),
            "modification_precision": safe_ratio(
                counts["beneficial_changes"], counts["modified_pair_count"]
            ),
            "fp_removed_per_evidence_item": safe_ratio(
                counts["removed_fp"], int(base["evidence_item_count"])
            ),
        }
    )
    if scope_domain == "nucleotide":
        for field in ("precision", "recall", "f1", "tp_preservation", "fp_removal", "modification_precision"):
            row[field] = None
    return row


def main() -> None:
    completion = json.loads(COMPLETION.read_text(encoding="utf-8"))
    eligibility_summary = json.loads(ELIGIBILITY_SUMMARY.read_text(encoding="utf-8"))
    matched_summary = json.loads(MATCHED_SUMMARY.read_text(encoding="utf-8"))
    if completion["status"] != "PASS" or not completion["formal_summarization_authorized"]:
        raise AssertionError("v1.0.2 completion gate has not authorized summarization")
    if completion["eligible_constraint_satisfaction_rate"] != 1.0:
        raise AssertionError("eligible constraint satisfaction is not 100%")
    frozen_hash_checks = {
        "eligibility": file_sha256(ELIGIBILITY) == eligibility_summary["eligibility_csv_sha256"],
        "matched_b1": file_sha256(MATCHED_B1) == matched_summary["matched_b1_view_sha256"],
        "matched_b0": file_sha256(MATCHED_B0) == matched_summary["matched_b0_view_sha256"],
        "b2": file_sha256(B2_STRUCTURES) == completion["b2_structures_v1_0_2_sha256"],
    }
    if not all(frozen_hash_checks.values()):
        raise AssertionError(f"formal input hash check failed: {frozen_hash_checks}")

    records = load_records()
    manifests = load_manifests()
    b2 = load_b2()
    primary_b1, matched_ids = load_matched_rows()
    if matched_ids != set(b2):
        raise AssertionError("matched B0/B1 manifest IDs differ from complete B2 IDs")
    with ELIGIBILITY.open(encoding="utf-8", newline="") as handle:
        ineligible_ids = {
            row["manifest_id"]
            for row in csv.DictReader(handle)
            if row["eligibility_status"] != "R2_ELIGIBLE"
        }
    if ineligible_ids & matched_ids:
        raise AssertionError("capability-ineligible manifest entered formal metric universe")

    zero_by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in b2.values():
        if int(row["density_percent"]) == 0:
            zero_by_rna[row["rna_id"]].append(row)
    zero_audit_rows = []
    historical_zero_rows = []
    for rna_id in sorted(zero_by_rna):
        rows = zero_by_rna[rna_id]
        input_hashes = {row["folding_input_sha256"] for row in rows}
        output_hashes = {row["output_sha256"] for row in rows}
        if len(rows) != 10 or len(input_hashes) != 1 or len(output_hashes) != 1:
            raise AssertionError(f"v1.0.2 zero-density identity failed: {rna_id}")
        zero_audit_rows.append(
            {
                "rna_id": rna_id,
                "realization_count": len(rows),
                "channel_count": len({row["channel"] for row in rows}),
                "evidence_seed_count": len({row["evidence_seed"] for row in rows}),
                "unique_folding_input_count": len(input_hashes),
                "unique_output_count": len(output_hashes),
                "identity_pass": True,
            }
        )
        r2_pairs = rows[0]["pairs"]
        historical_pairs = records[(rna_id, "rnafold")]["original"]
        historical_zero_rows.append(
            {
                "rna_id": rna_id,
                "historical_pair_count": len(historical_pairs),
                "r2_zero_pair_count": len(r2_pairs),
                "exact_pair_set_identity": historical_pairs == r2_pairs,
                "context_only_not_r2_failure": True,
            }
        )
    if len(zero_audit_rows) != 121:
        raise AssertionError("v1.0.2 zero-density audit RNA count mismatch")

    matched_wide: list[dict[str, Any]] = []
    method_rows: list[dict[str, Any]] = []
    decomposition_rows: list[dict[str, Any]] = []
    scope_rows: list[dict[str, Any]] = []
    identity_checks = scope_checks = 0
    for manifest_id in sorted(matched_ids):
        manifest = manifests[manifest_id]
        b2_row = b2[manifest_id]
        evidence_pairs, evidence_positions = delivered_items(manifest)
        for source in SOURCES:
            record = records[(manifest["rna_id"], source)]
            sequence = record["sequence"]
            length = len(sequence)
            truth = record["ground_truth"]
            original = record["original"]
            refolded = set(validate_pairs(b2_row["pairs"], sequence=sequence))
            original_eval = evaluate_pairs(original, truth, sequence_length=length)
            refold_eval = evaluate_pairs(refolded, truth, sequence_length=length)
            b1 = primary_b1[(manifest_id, source)]
            for name in ("tp", "fp", "fn"):
                if int(b1[f"original_{name}"]) != getattr(original_eval, name):
                    raise AssertionError(f"B1 original metric mismatch: {manifest_id}/{source}/{name}")
            b1_tp, b1_fp, b1_fn = (int(b1[name]) for name in ("tp", "fp", "fn"))
            b1_precision, b1_recall, b1_f1 = metric_values_from_counts(b1_tp, b1_fp, b1_fn)
            if any(
                abs(float(b1[name]) - value) > 1e-12
                for name, value in (
                    ("precision", b1_precision), ("recall", b1_recall), ("f1", b1_f1)
                )
            ):
                raise AssertionError(f"shared evaluator mismatch in frozen B1 row: {manifest_id}/{source}")
            parts = full_refold_edit_decomposition(
                original, truth, refolded, sequence_length=length
            )
            counts = count_parts(parts)
            identity_checks += 6
            base = {
                "manifest_id": manifest_id,
                "rna_id": manifest["rna_id"],
                "source_model": source,
                "channel": manifest["evidence_channel"],
                "density_percent": int(manifest["density_percent"]),
                "evidence_seed": int(manifest["evidence_seed"]),
                "evidence_item_count": int(manifest["delivered_item_count"]),
                "sequence_length": length,
            }
            wide = {
                **base,
                **metric_fields("b0_", original_eval),
                "b1_tp": b1_tp,
                "b1_fp": b1_fp,
                "b1_fn": b1_fn,
                "b1_precision": b1_precision,
                "b1_recall": b1_recall,
                "b1_f1": b1_f1,
                **metric_fields("b2_", refold_eval),
                "b1_delta_f1_vs_b0": b1_f1 - original_eval.f1,
                "b2_delta_f1_vs_b0": refold_eval.f1 - original_eval.f1,
                "b2_delta_f1_vs_b1": refold_eval.f1 - b1_f1,
                "b2_output_sha256": b2_row["output_sha256"],
            }
            matched_wide.append(wide)

            original_pair_count = len(original)
            b0_method = method_row(
                base,
                "B0_ORIGINAL",
                tp=original_eval.tp,
                fp=original_eval.fp,
                fn=original_eval.fn,
                original_tp=original_eval.tp,
                original_fp=original_eval.fp,
                original_fn=original_eval.fn,
                preserved_tp=original_eval.tp,
                lost_tp=0,
                removed_fp=0,
                preserved_original_fp=original_eval.fp,
                new_tp=0,
                new_fp=0,
                unchanged_pairs=original_pair_count,
                deleted_pairs=0,
                added_pairs=0,
                b0_f1=original_eval.f1,
            )
            b1_method = method_row(
                base,
                "B1_LOCAL_HARD",
                tp=b1_tp,
                fp=b1_fp,
                fn=b1_fn,
                original_tp=original_eval.tp,
                original_fp=original_eval.fp,
                original_fn=original_eval.fn,
                preserved_tp=original_eval.tp - int(b1["harmful_deletions"]),
                lost_tp=int(b1["harmful_deletions"]),
                removed_fp=int(b1["beneficial_deletions"]),
                preserved_original_fp=original_eval.fp - int(b1["beneficial_deletions"]),
                new_tp=int(b1["beneficial_insertions"]),
                new_fp=int(b1["harmful_insertions"]),
                unchanged_pairs=original_pair_count - int(b1["removed_pair_count"]),
                deleted_pairs=int(b1["removed_pair_count"]),
                added_pairs=int(b1["added_pair_count"]),
                b0_f1=original_eval.f1,
            )
            b2_method = method_row(
                base,
                "B2_GLOBAL_REFOLD",
                tp=refold_eval.tp,
                fp=refold_eval.fp,
                fn=refold_eval.fn,
                original_tp=original_eval.tp,
                original_fp=original_eval.fp,
                original_fn=original_eval.fn,
                preserved_tp=counts["preserved_tp"],
                lost_tp=counts["lost_tp"],
                removed_fp=counts["removed_fp"],
                preserved_original_fp=counts["preserved_original_fp"],
                new_tp=counts["new_tp"],
                new_fp=counts["new_fp"],
                unchanged_pairs=counts["unchanged_pairs"],
                deleted_pairs=counts["deleted_pairs"],
                added_pairs=counts["added_pairs"],
                b0_f1=original_eval.f1,
            )
            method_rows.extend((b0_method, b1_method, b2_method))
            decomposition_rows.append(
                {
                    **base,
                    **counts,
                    "original_tp": original_eval.tp,
                    "original_fp": original_eval.fp,
                    "tp_preservation": b2_method["tp_preservation"],
                    "fp_removal": b2_method["fp_removal"],
                    "modification_precision": b2_method["modification_precision"],
                }
            )

            if manifest["evidence_channel"] == PAIR_CHANNEL:
                scopes = pair_scope_partition(truth, original, refolded, evidence_pairs)
                before_compliance = len(evidence_pairs & original)
                after_compliance = len(evidence_pairs & refolded)
            else:
                scopes = unpaired_scope_partition(
                    truth, original, refolded, evidence_positions
                )
                original_endpoints = {endpoint for pair in original for endpoint in pair}
                refolded_endpoints = {endpoint for pair in refolded for endpoint in pair}
                before_compliance = sum(
                    position not in original_endpoints for position in evidence_positions
                )
                after_compliance = sum(
                    position not in refolded_endpoints for position in evidence_positions
                )
            if set().union(*scopes.values()) != truth | original | refolded:
                raise AssertionError("scope partition is not exhaustive")
            scope_checks += 1
            for scope_name, scope in scopes.items():
                domain = (
                    "nucleotide"
                    if manifest["evidence_channel"] == UNPAIRED_CHANNEL
                    and scope_name == "DIRECT_EVIDENCE_EFFECT"
                    else "pair"
                )
                scope_rows.append(
                    scope_row(
                        base,
                        scope_name,
                        scope,
                        sequence_length=length,
                        original=original,
                        truth=truth,
                        refolded=refolded,
                        scope_domain=domain,
                        direct_compliance_before=(
                            before_compliance if scope_name == "DIRECT_EVIDENCE_EFFECT" else 0
                        ),
                        direct_compliance_b2=(
                            after_compliance if scope_name == "DIRECT_EVIDENCE_EFFECT" else 0
                        ),
                    )
                )

    expected_matched = 7153 * 3
    if len(matched_wide) != expected_matched or len(decomposition_rows) != expected_matched:
        raise AssertionError("per-source matched row count mismatch")
    if len(method_rows) != expected_matched * 3 or len(scope_rows) != expected_matched * 3:
        raise AssertionError("method/scope row count mismatch")
    if any(row["evidence_item_count"] == 0 and row["delta_f1_per_evidence_item"] is not None for row in method_rows):
        raise AssertionError("zero-density evidence efficiency is not NA")

    density_source = grouped_summary(
        method_rows, ("source_model", "channel", "density_percent", "method")
    )
    density_channel = grouped_summary(method_rows, ("channel", "density_percent", "method"))
    source_summary = grouped_summary(method_rows, ("source_model", "channel", "method"))
    channel_summary = grouped_summary(method_rows, ("channel", "method"))
    overall_summary = grouped_summary(method_rows, ("method",))
    edit_summary = grouped_summary(
        [row for row in method_rows if row["method"] == "B2_GLOBAL_REFOLD"],
        ("source_model", "channel", "density_percent", "method"),
    )
    scope_summary = grouped_summary(
        scope_rows, ("source_model", "channel", "density_percent", "scope", "scope_domain")
    )
    scope_source_channel_summary = grouped_summary(
        scope_rows, ("source_model", "channel", "scope", "scope_domain")
    )
    scope_channel_summary = grouped_summary(
        scope_rows, ("channel", "scope", "scope_domain")
    )
    scope_overall_summary = grouped_summary(scope_rows, ("scope", "scope_domain"))
    for row in (
        scope_summary
        + scope_source_channel_summary
        + scope_channel_summary
        + scope_overall_summary
    ):
        if row["scope_domain"] == "nucleotide":
            for prefix in ("micro_", "macro_"):
                for metric in ("precision", "recall", "f1", "tp_preservation", "fp_removal", "modification_precision"):
                    row[f"{prefix}{metric}"] = None

    efficiency = [
        {
            key: row[key]
            for key in (
                "source_model",
                "channel",
                "density_percent",
                "method",
                "eligible_realization_count",
                "eligible_rna_count",
                "missing_rna_count",
                "sum_removed_fp",
                "sum_evidence_item_count",
                "micro_fp_removed_per_evidence_item",
                "macro_fp_removed_per_evidence_item",
                "micro_delta_f1_vs_b0",
                "macro_delta_f1_vs_b0",
                "micro_delta_f1_per_evidence_item",
                "macro_delta_f1_per_evidence_item",
                "macro_delta_f1_per_evidence_item_defined_rna_count",
            )
        }
        for row in density_source
        if int(row["density_percent"]) > 0 and row["method"] in ("B1_LOCAL_HARD", "B2_GLOBAL_REFOLD")
    ]

    coverage_rows = []
    for row in eligibility_summary["coverage_by_density"]:
        coverage_rows.append(
            {
                **row,
                "missing_rna_count": 121 - int(row["eligible_rna_count"]),
                "missing_status": (
                    "NA_MISSING_ELIGIBILITY"
                    if int(row["eligible_rna_count"]) < 121
                    else "COMPLETE"
                ),
            }
        )
    zero_coverage_rows = eligibility_summary["zero_coverage_rna_density_strata"]

    write_csv(R2 / "metrics/per_source_matched_b0_b1_b2.csv", matched_wide)
    write_csv(R2 / "metrics/per_realization_method_metrics.csv", method_rows)
    write_csv(R2 / "metrics/full_refold_edit_decomposition.csv", decomposition_rows)
    write_csv(R2 / "metrics/scope_edit_decomposition.csv", scope_rows)
    write_csv(R2 / "summaries/density_source_summary.csv", density_source)
    write_csv(R2 / "summaries/density_channel_summary.csv", density_channel)
    write_csv(R2 / "summaries/source_wise_summary.csv", source_summary)
    write_csv(R2 / "summaries/channel_wise_summary.csv", channel_summary)
    write_csv(R2 / "summaries/overall_summary.csv", overall_summary)
    write_csv(R2 / "summaries/full_refold_edit_summary.csv", edit_summary)
    write_csv(R2 / "summaries/scope_summary.csv", scope_summary)
    write_csv(
        R2 / "summaries/scope_source_channel_summary.csv", scope_source_channel_summary
    )
    write_csv(R2 / "summaries/scope_channel_summary.csv", scope_channel_summary)
    write_csv(R2 / "summaries/scope_overall_summary.csv", scope_overall_summary)
    write_csv(R2 / "summaries/evidence_efficiency_summary.csv", efficiency)
    write_csv(R2 / "summaries/capability_coverage_by_density.csv", coverage_rows)
    write_csv(R2 / "summaries/zero_coverage_rna_density.csv", zero_coverage_rows)
    write_csv(R2 / "integrity/zero_density_identity_audit_v1_0_2.csv", zero_audit_rows)
    write_csv(
        R2 / "integrity/historical_rnafold_vs_r2_zero_audit_v1_0_2.csv",
        historical_zero_rows,
    )
    write_csv(
        R2 / "summaries/rna_balanced_macro_by_density.csv",
        [
            {key: value for key, value in row.items() if key.startswith("macro_") or key in (
                "source_model", "channel", "density_percent", "method", "eligible_realization_count", "eligible_rna_count", "missing_rna_count"
            )}
            for row in density_source
        ],
    )
    write_csv(
        R2 / "summaries/event_pooled_micro_by_density.csv",
        [
            {key: value for key, value in row.items() if key.startswith("micro_") or key.startswith("sum_") or key in (
                "source_model", "channel", "density_percent", "method", "eligible_realization_count", "eligible_rna_count", "missing_rna_count"
            )}
            for row in density_source
        ],
    )

    output_paths = [
        R2 / "metrics/per_source_matched_b0_b1_b2.csv",
        R2 / "metrics/per_realization_method_metrics.csv",
        R2 / "metrics/full_refold_edit_decomposition.csv",
        R2 / "metrics/scope_edit_decomposition.csv",
        R2 / "summaries/density_source_summary.csv",
        R2 / "summaries/density_channel_summary.csv",
        R2 / "summaries/source_wise_summary.csv",
        R2 / "summaries/channel_wise_summary.csv",
        R2 / "summaries/overall_summary.csv",
        R2 / "summaries/full_refold_edit_summary.csv",
        R2 / "summaries/scope_summary.csv",
        R2 / "summaries/scope_source_channel_summary.csv",
        R2 / "summaries/scope_channel_summary.csv",
        R2 / "summaries/scope_overall_summary.csv",
        R2 / "summaries/evidence_efficiency_summary.csv",
        R2 / "summaries/capability_coverage_by_density.csv",
        R2 / "summaries/zero_coverage_rna_density.csv",
        R2 / "summaries/rna_balanced_macro_by_density.csv",
        R2 / "summaries/event_pooled_micro_by_density.csv",
        R2 / "integrity/zero_density_identity_audit_v1_0_2.csv",
        R2 / "integrity/historical_rnafold_vs_r2_zero_audit_v1_0_2.csv",
    ]
    integrity = {
        "status": "PASS",
        "protocol_version": R2_PROTOCOL_VERSION,
        "formal_summarization_first_run_after_v1_0_2_completion_gate": True,
        "eligible_manifest_count": len(matched_ids),
        "capability_ineligible_manifest_count": len(ineligible_ids),
        "capability_ineligible_entered_metric_universe_count": len(ineligible_ids & matched_ids),
        "matched_source_realization_count": len(matched_wide),
        "method_metric_row_count": len(method_rows),
        "full_refold_decomposition_row_count": len(decomposition_rows),
        "scope_row_count": len(scope_rows),
        "edit_accounting_identity_check_count": identity_checks,
        "edit_accounting_identity_failure_count": 0,
        "scope_partition_check_count": scope_checks,
        "scope_partition_failure_count": 0,
        "eligible_constraint_satisfaction_rate": completion["eligible_constraint_satisfaction_rate"],
        "zero_density_evidence_efficiency_na_pass": True,
        "zero_density_reproducibility_rna_count": len(zero_audit_rows),
        "zero_density_reproducibility_pass_count": sum(
            row["identity_pass"] for row in zero_audit_rows
        ),
        "historical_rnafold_vs_r2_zero_identity_count": sum(
            row["exact_pair_set_identity"] for row in historical_zero_rows
        ),
        "historical_rnafold_vs_r2_zero_identity_rate": mean_defined(
            1.0 if row["exact_pair_set_identity"] else 0.0 for row in historical_zero_rows
        ),
        "pair_density_20_eligible_rna_count": next(
            row["eligible_rna_count"]
            for row in coverage_rows
            if row["channel"] == PAIR_CHANNEL and int(row["density_percent"]) == 20
        ),
        "pair_density_50_eligible_rna_count": next(
            row["eligible_rna_count"]
            for row in coverage_rows
            if row["channel"] == PAIR_CHANNEL and int(row["density_percent"]) == 50
        ),
        "output_hashes": {
            str(path.relative_to(ROOT)): file_sha256(path) for path in output_paths
        },
        "learned_model_trained": False,
        "historical_e2_executed": False,
        "external77_accessed": False,
        "r3_started": False,
    }
    integrity_path = R2 / "integrity/formal_summary_integrity_v1_0_2.json"
    integrity_path.write_text(json.dumps(integrity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(integrity, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
