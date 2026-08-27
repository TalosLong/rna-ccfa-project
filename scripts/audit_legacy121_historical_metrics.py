#!/usr/bin/env python3
"""Audit local historical Legacy121 metric sources without changing source assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from rna_ccfa.structure import parse_extended_dot_bracket


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = "legacy121_v1"
EXPECTED_RNAS = 121
EXPECTED_MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")

HISTORICAL_PROJECT = Path("/root/autodl-tmp/models/trRosettaRNA2")
HISTORICAL_SS_SCRIPT = HISTORICAL_PROJECT / "scripts/tools/ss_quality_analysis.py"
HISTORICAL_SS_RESULTS = HISTORICAL_PROJECT / "results/ss_quality_vs_3d.csv"
HISTORICAL_SS_REPORT = HISTORICAL_PROJECT / "reports/实验总结_20260516-0703.md"
HISTORICAL_SS_PLOT_SCRIPT = HISTORICAL_PROJECT / "scripts/plot_step_figures.py"
HISTORICAL_SCORE_ROOT = HISTORICAL_PROJECT / "ss_predictions_native"
HISTORICAL_GT_ROOT = HISTORICAL_PROJECT / "gt_ss_dir_full"

NMR_F1_SUMMARY = (
    HISTORICAL_PROJECT
    / "data/nmr_f1_top1_matrices/nmr_f1_top1_summary.csv"
)
NMR_F1_LOG = HISTORICAL_PROJECT / "data/nmr_f1_top1_matrices/run.log"
NMR_F1_CONSUMER = HISTORICAL_PROJECT / "scripts/evaluate/eval_nmr_f1.py"
NMR_F1_STRATIFIED = HISTORICAL_PROJECT / "results/nmr_f1_stratified.csv"

FROZEN_BASELINE = {
    "rnafold": {
        "macro_f1": 0.9058176119079561,
        "micro_f1": 0.8744434550311665,
        "sum_tp": 1473,
        "sum_fp": 220,
        "sum_fn": 203,
    },
    "petfold": {
        "macro_f1": 0.8968492212485739,
        "micro_f1": 0.8656804733727811,
        "sum_tp": 1463,
        "sum_fp": 241,
        "sum_fn": 213,
    },
    "trrosettarna2_native_ss": {
        "macro_f1": 0.8428713642132949,
        "micro_f1": 0.8187167273746148,
        "sum_tp": 1461,
        "sum_fp": 432,
        "sum_fn": 215,
    },
}

COMPARISON_FIELDS = (
    "source_model",
    "historical_source",
    "historical_metric_name",
    "historical_value",
    "shared_metric_name",
    "shared_value",
    "absolute_difference",
    "compatibility",
    "sample_count_historical",
    "sample_count_shared",
    "mismatch_reason",
    "notes",
)


class MetricAuditError(RuntimeError):
    """A required historical or frozen audit invariant failed."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-summary",
        type=Path,
        default=PROJECT_ROOT / "results/baseline_legacy121_v1/summary_by_model.csv",
    )
    parser.add_argument(
        "--per-sample",
        type=Path,
        default=PROJECT_ROOT / "results/baseline_legacy121_v1/per_sample.csv",
    )
    parser.add_argument(
        "--normalized-input",
        type=Path,
        default=PROJECT_ROOT / "normalized/legacy121_v1/predictions.jsonl",
    )
    parser.add_argument(
        "--comparison-output",
        type=Path,
        default=PROJECT_ROOT / "results/metric_audit/legacy121_metric_comparison.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=PROJECT_ROOT
        / "results/metric_audit/legacy121_metric_audit_summary.json",
    )
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise MetricAuditError(f"missing required audit source: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_normalized_trrna2(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record["source_model"]["name"] != "trrosettarna2_native_ss":
                continue
            rna_id = record["rna_id"]
            if rna_id in records:
                raise MetricAuditError(f"duplicate trRosettaRNA2 normalized RNA: {rna_id}")
            records[rna_id] = record
    if len(records) != EXPECTED_RNAS:
        raise MetricAuditError(
            f"expected {EXPECTED_RNAS} normalized trRosettaRNA2 records, observed {len(records)}"
        )
    return records


def _verify_frozen_baseline(path: Path) -> dict[str, dict[str, int | float]]:
    rows = _read_csv(path)
    if len(rows) != len(EXPECTED_MODELS):
        raise MetricAuditError("frozen baseline summary must have exactly three model rows")
    observed: dict[str, dict[str, int | float]] = {}
    for row in rows:
        model = row["source_model"]
        if model not in EXPECTED_MODELS:
            raise MetricAuditError(f"unexpected frozen baseline model: {model}")
        values: dict[str, int | float] = {
            "n_samples": int(row["n_samples"]),
            "sum_tp": int(row["sum_tp"]),
            "sum_fp": int(row["sum_fp"]),
            "sum_fn": int(row["sum_fn"]),
            "macro_precision": float(row["macro_precision"]),
            "macro_recall": float(row["macro_recall"]),
            "macro_f1": float(row["macro_f1"]),
            "micro_precision": float(row["micro_precision"]),
            "micro_recall": float(row["micro_recall"]),
            "micro_f1": float(row["micro_f1"]),
        }
        if values["n_samples"] != EXPECTED_RNAS:
            raise MetricAuditError(f"{model}: frozen baseline sample count changed")
        for key, expected in FROZEN_BASELINE[model].items():
            if values[key] != expected:
                raise MetricAuditError(
                    f"{model}: frozen {key} changed from {expected!r} to {values[key]!r}"
                )
        observed[model] = values
    return observed


def _dot_bracket_from_file(path: Path) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in lines:
        if not line.startswith(">"):
            return line
    raise MetricAuditError(f"no structure line found in {path}")


def _threshold_pairs(score_path: Path) -> set[tuple[int, int]]:
    with np.load(score_path) as archive:
        scores = archive["ss"]
    binary = (scores > 0.5) | (scores.T > 0.5)
    np.fill_diagonal(binary, False)
    length = binary.shape[0]
    return {
        (i, j)
        for i in range(length)
        for j in range(i + 1, length)
        if bool(binary[i, j])
    }


def _historical_metric_values(
    predicted: set[tuple[int, int]],
    ground_truth: set[tuple[int, int]],
) -> dict[str, int | float]:
    """Copy the historical script's upper-triangle metric convention for audit only."""

    tp = len(predicted & ground_truth)
    fp = len(predicted - ground_truth)
    fn = len(ground_truth - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _audit_historical_native(
    normalized: dict[str, dict[str, Any]],
    shared_per_sample: dict[str, dict[str, str]],
) -> dict[str, Any]:
    rows = _read_csv(HISTORICAL_SS_RESULTS)
    ids = [row["seq_id"] for row in rows]
    if len(rows) != 119 or len(set(ids)) != 119:
        raise MetricAuditError("historical native SS table is no longer the audited 119-row source")
    if not set(ids) <= set(normalized):
        raise MetricAuditError("historical native SS table contains an RNA outside Legacy121 v1")

    missing_ids = sorted(set(normalized) - set(ids))
    if missing_ids != ["2N1Q_155_4wj_nmr_A", "9G7C_224_4wj_cryoEM_A"]:
        raise MetricAuditError(f"unexpected historical length-filter exclusions: {missing_ids}")

    metric_matches = Counter()
    threshold_equals_dbn = 0
    threshold_pair_count_equals_dbn = 0
    threshold_multiple_partner_samples = 0
    historical_gt_equals_normalized = 0
    reconstructed_counts = Counter()

    for row in rows:
        rna_id = row["seq_id"]
        record = normalized[rna_id]
        length = len(record["sequence"])
        score_path = HISTORICAL_SCORE_ROOT / rna_id / f"{rna_id}_ss_prob.npz"
        historical_pairs = _threshold_pairs(score_path)
        historical_gt_dbn = _dot_bracket_from_file(HISTORICAL_GT_ROOT / f"{rna_id}.dbn")
        historical_gt = set(parse_extended_dot_bracket(historical_gt_dbn, sequence_length=length))
        normalized_gt = set(map(tuple, record["ground_truth_structure"]["pairs"]))
        normalized_dbn = set(map(tuple, record["predicted_structure"]["pairs"]))

        if historical_gt == normalized_gt:
            historical_gt_equals_normalized += 1
        if historical_pairs == normalized_dbn:
            threshold_equals_dbn += 1
        if len(historical_pairs) == len(normalized_dbn):
            threshold_pair_count_equals_dbn += 1

        partners = Counter(endpoint for pair in historical_pairs for endpoint in pair)
        if any(count > 1 for count in partners.values()):
            threshold_multiple_partner_samples += 1

        metrics = _historical_metric_values(historical_pairs, historical_gt)
        reconstructed_counts.update(
            {key: int(metrics[key]) for key in ("tp", "fp", "fn")}
        )
        if int(row["pairs_native"]) != len(historical_pairs):
            raise MetricAuditError(f"{rna_id}: reconstructed historical prediction count changed")
        if int(row["pairs_gt"]) != len(historical_gt):
            raise MetricAuditError(f"{rna_id}: reconstructed historical GT count changed")
        for metric in ("precision", "recall", "f1"):
            if round(float(metrics[metric]), 4) == float(row[f"native_{metric}"]):
                metric_matches[metric] += 1

    if historical_gt_equals_normalized != 119:
        raise MetricAuditError("historical and normalized GT pairs do not agree for all 119 rows")
    if any(metric_matches[metric] != 119 for metric in ("precision", "recall", "f1")):
        raise MetricAuditError("current historical script logic does not reproduce its stored table")

    historical_macro = {
        metric: sum(float(row[f"native_{metric}"]) for row in rows) / len(rows)
        for metric in ("precision", "recall", "f1", "mcc")
    }
    shared_subset_macro = {
        metric: sum(float(shared_per_sample[rna_id][metric]) for rna_id in ids) / len(ids)
        for metric in ("precision", "recall", "f1")
    }
    sum_tp = reconstructed_counts["tp"]
    sum_fp = reconstructed_counts["fp"]
    sum_fn = reconstructed_counts["fn"]
    audit_reconstructed_micro = {
        "precision": sum_tp / (sum_tp + sum_fp),
        "recall": sum_tp / (sum_tp + sum_fn),
        "f1": 2 * sum_tp / (2 * sum_tp + sum_fp + sum_fn),
        "sum_tp": sum_tp,
        "sum_fp": sum_fp,
        "sum_fn": sum_fn,
    }
    return {
        "sample_count": len(rows),
        "sample_ids_all_in_legacy121_v1": True,
        "excluded_by_length_filter": missing_ids,
        "historical_gt_pair_sets_equal_normalized": historical_gt_equals_normalized,
        "threshold_pair_sets_equal_historical_dbn": threshold_equals_dbn,
        "threshold_pair_counts_equal_historical_dbn": threshold_pair_count_equals_dbn,
        "threshold_samples_with_multiple_partners": threshold_multiple_partner_samples,
        "stored_metric_rows_reproduced": dict(metric_matches),
        "historical_macro_from_stored_rounded_samples": historical_macro,
        "shared_macro_on_same_119_ids": shared_subset_macro,
        "audit_reconstructed_historical_micro_not_reported_by_source": audit_reconstructed_micro,
    }


def _audit_nmr_topology_source(
    shared_per_sample: dict[str, dict[str, str]],
) -> dict[str, Any]:
    rows = _read_csv(NMR_F1_SUMMARY)
    single_chain = [row for row in rows if row["dataset"] == "single_chain"]
    successful = [row for row in single_chain if row["success"] == "TRUE"]
    failed = [row for row in single_chain if row["success"] != "TRUE"]
    shared_keys = {rna_id.removesuffix("_A") for rna_id in shared_per_sample}
    successful_ids = {row["entry_id"] for row in successful}
    if len(single_chain) != 123 or len(successful) != 121:
        raise MetricAuditError("NMR topology source no longer has the audited 123/121 handling")
    if successful_ids != shared_keys:
        raise MetricAuditError("NMR topology successful IDs differ from Legacy121 v1")
    failed_ids = sorted(row["entry_id"] for row in failed)
    if failed_ids != ["8Q4O_23_g4_nmr", "8TNS_24_g4_nmr"]:
        raise MetricAuditError(f"unexpected NMR topology failed IDs: {failed_ids}")

    shared_gt_counts = {
        rna_id.removesuffix("_A"): int(row["gt_pair_count"])
        for rna_id, row in shared_per_sample.items()
    }
    gt_count_matches = sum(
        shared_gt_counts[row["entry_id"]] == int(row["gt_pairs"])
        for row in successful
    )
    macro = {
        metric: sum(float(row[f"best_{metric}"]) for row in successful) / len(successful)
        for metric in ("precision", "recall", "f1")
    }
    return {
        "nominal_single_chain_rows": len(single_chain),
        "successful_single_chain_rows": len(successful),
        "failed_gt_only_rows": failed_ids,
        "successful_ids_equal_legacy121_v1": True,
        "gt_pair_counts_equal_shared": gt_count_matches,
        "historical_macro_from_stored_samples": macro,
        "all_successful_precision_values_equal_one": all(
            float(row["best_precision"]) == 1.0 for row in successful
        ),
        "original_generator_script_found": False,
        "referenced_original_output_root_exists": Path(
            "/root/autodl-tmp/NMR_secondary"
        ).exists(),
    }


def _comparison_rows(
    baseline: dict[str, dict[str, int | float]],
    native_audit: dict[str, Any],
    nmr_audit: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    historical_path = str(HISTORICAL_SS_RESULTS)
    mismatch_reason = (
        "119-vs-121 length-filtered universe and thresholded NPZ pair set rather than the "
        "historical DBN; threshold output also permits multiple partners"
    )
    for metric in ("precision", "recall", "f1"):
        rows.append(
            {
                "source_model": "trrosettarna2_native_ss",
                "historical_source": historical_path,
                "historical_metric_name": f"macro_native_{metric}_from_stored_rounded_samples",
                "historical_value": native_audit[
                    "historical_macro_from_stored_rounded_samples"
                ][metric],
                "shared_metric_name": f"macro_{metric}",
                "shared_value": baseline["trrosettarna2_native_ss"][f"macro_{metric}"],
                "absolute_difference": "",
                "compatibility": "PARTIALLY_COMPATIBLE",
                "sample_count_historical": 119,
                "sample_count_shared": 121,
                "mismatch_reason": mismatch_reason,
                "notes": (
                    "Values are shown for context only; no reproduction-failure difference is "
                    "computed because prediction representation and sample universe differ."
                ),
            }
        )
    rows.append(
        {
            "source_model": "trrosettarna2_native_ss",
            "historical_source": historical_path,
            "historical_metric_name": "macro_native_mcc_from_stored_rounded_samples",
            "historical_value": native_audit[
                "historical_macro_from_stored_rounded_samples"
            ]["mcc"],
            "shared_metric_name": "",
            "shared_value": "",
            "absolute_difference": "",
            "compatibility": "PARTIALLY_COMPATIBLE",
            "sample_count_historical": 119,
            "sample_count_shared": 121,
            "mismatch_reason": (
                "historical MCC uses all upper-triangle residue pairs as negatives; shared MCC "
                "is intentionally deferred and has no frozen value"
            ),
            "notes": "MCC is inventoried from the retained table only and was not recomputed.",
        }
    )

    nmr_path = str(NMR_F1_SUMMARY)
    for metric in ("precision", "recall", "f1"):
        rows.append(
            {
                "source_model": "nmr_derived_topology_not_a_source_predictor",
                "historical_source": nmr_path,
                "historical_metric_name": f"macro_best_{metric}_single_chain_successes",
                "historical_value": nmr_audit["historical_macro_from_stored_samples"][metric],
                "shared_metric_name": "",
                "shared_value": "",
                "absolute_difference": "",
                "compatibility": "INCOMPATIBLE",
                "sample_count_historical": 121,
                "sample_count_shared": 121,
                "mismatch_reason": (
                    "prediction source is an NMR-derived selected topology, not RNAfold, PETfold, "
                    "or trRosettaRNA2 native SS"
                ),
                "notes": (
                    "The equal successful sample count and matching GT pair counts do not make "
                    "this a source-predictor reproduction reference."
                ),
            }
        )
    return rows


def main() -> int:
    args = _parse_args()
    baseline = _verify_frozen_baseline(args.baseline_summary.resolve())
    normalized_path = args.normalized_input.resolve()
    normalized_sha_before = _sha256(normalized_path)
    normalized = _read_normalized_trrna2(normalized_path)

    per_sample_rows = _read_csv(args.per_sample.resolve())
    shared_trrna2 = {
        row["rna_id"]: row
        for row in per_sample_rows
        if row["source_model"] == "trrosettarna2_native_ss"
    }
    if len(shared_trrna2) != EXPECTED_RNAS:
        raise MetricAuditError("shared per-sample table lacks 121 trRosettaRNA2 rows")

    native_audit = _audit_historical_native(normalized, shared_trrna2)
    nmr_audit = _audit_nmr_topology_source(shared_trrna2)
    comparison_rows = _comparison_rows(baseline, native_audit, nmr_audit)

    historical_assets = [
        HISTORICAL_SS_SCRIPT,
        HISTORICAL_SS_RESULTS,
        HISTORICAL_SS_REPORT,
        HISTORICAL_SS_PLOT_SCRIPT,
        NMR_F1_SUMMARY,
        NMR_F1_LOG,
        NMR_F1_CONSUMER,
        NMR_F1_STRATIFIED,
    ]
    source_hashes = {str(path): _sha256(path) for path in historical_assets}
    unresolved_items = [
        (
            "No historical Legacy121 secondary-structure metric result or evaluation script was "
            "found for RNAfold or PETfold."
        ),
        (
            "The current ss_quality_analysis.py was modified after the stored CSV and writes to "
            "benchmark_results/ while the observed table is under results/; the audited metric "
            "logic nevertheless reproduces all 119 stored rounded metric rows."
        ),
        (
            "The historical threshold decoder's tie/conflict resolution is absent because it did "
            "not enforce one partner per nucleotide; the separate historical DBN decoder identity "
            "and settings remain unknown."
        ),
        (
            "The historical report labels the F1 stratification as 119 samples but its printed bin "
            "counts sum to 120 (it lists 14 rather than the CSV-derived 13 in the 0.7-0.8 bin)."
        ),
        (
            "The NMR topology generator script and its referenced /root/autodl-tmp/NMR_secondary "
            "outputs are absent, so candidate-selection and exact pair-matching details cannot be "
            "fully reconstructed from the retained summary alone."
        ),
    ]
    summary = {
        "dataset": DATASET,
        "generated_at_utc": _utc_now(),
        "search_scope": {
            "root": "/root/autodl-tmp",
            "read_only": True,
            "artifact_types": [
                "scripts",
                "CSV/TSV/JSON tables",
                "logs",
                "notebooks",
                "Markdown/HTML reports",
                "presentation/PDF filenames and derivative source notes",
            ],
            "search_terms": [
                "RNAfold",
                "PETfold",
                "trRosettaRNA2/native SS",
                "Legacy/RNA-Puzzles/NMR 121/123",
                "Precision/Recall/F1/MCC/base-pair metrics",
            ],
            "dependency_and_environment_trees_excluded_after_screening": True,
        },
        "frozen_shared_baseline": baseline,
        "normalized_input_path": str(normalized_path),
        "normalized_input_sha256": normalized_sha_before,
        "historical_sources_found": 2,
        "compatible_sources": 0,
        "partially_compatible_sources": 1,
        "incompatible_sources": 1,
        "unknown_sources": 0,
        "source_classifications": [
            {
                "source_id": "trrna2_native_threshold_ss_quality_bundle",
                "compatibility": "PARTIALLY_COMPATIBLE",
                "primary_path": str(HISTORICAL_SS_RESULTS),
                "supporting_paths": [
                    str(HISTORICAL_SS_SCRIPT),
                    str(HISTORICAL_SS_REPORT),
                    str(HISTORICAL_SS_PLOT_SCRIPT),
                ],
            },
            {
                "source_id": "nmr_derived_topology_f1_bundle",
                "compatibility": "INCOMPATIBLE",
                "primary_path": str(NMR_F1_SUMMARY),
                "supporting_paths": [
                    str(NMR_F1_LOG),
                    str(NMR_F1_CONSUMER),
                    str(NMR_F1_STRATIFIED),
                ],
            },
        ],
        "historical_source_sha256": source_hashes,
        "historical_native_threshold_audit": native_audit,
        "nmr_derived_topology_audit": nmr_audit,
        "genuinely_compatible_historical_metric_source_exists": False,
        "direct_numerical_comparisons_performed": 0,
        "compatible_mismatches": 0,
        "compatible_mismatch_details": [],
        "unresolved_items": unresolved_items,
        "phase0_audit_passed": True,
        "phase0_audit_pass_reason": (
            "Systematic read-only search completed; all relevant retained metric-source bundles "
            "were classified and documented, and no unsupported reproduction-failure claim was made."
        ),
        "new_predictor_inference_performed": False,
        "mcc_recomputed_by_audit": False,
        "mcc_implemented_or_added_to_shared_evaluator": False,
        "normalized_input_unchanged": _sha256(normalized_path) == normalized_sha_before,
    }
    if not summary["normalized_input_unchanged"]:
        raise MetricAuditError("normalized input changed during read-only metric audit")

    comparison_output = args.comparison_output.resolve()
    summary_output = args.summary_output.resolve()
    comparison_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    with comparison_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMPARISON_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(comparison_rows)
    with summary_output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
