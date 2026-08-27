#!/usr/bin/env python3
"""Consolidate frozen Legacy121 Phase 1 analyses without changing semantics."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rna_ccfa.consolidation import (
    RankedPattern,
    rank_same_unit,
    rate,
    relative_consistency,
    require_fields,
)


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/error_analysis"
BASELINE = ROOT / "results/baseline_legacy121_v1"
MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")
EXPECTED = {
    "rnafold": (1473, 220, 203),
    "petfold": (1463, 241, 213),
    "trrosettarna2_native_ss": (1461, 432, 215),
}
EXPECTED_STEMS = {
    "rnafold": (335, 326, 227, 5, 44, 2, 1, 10, 5, 46, 42, 5),
    "petfold": (335, 312, 203, 4, 42, 2, 1, 35, 16, 48, 44, 16),
    "trrosettarna2_native_ss": (335, 295, 112, 1, 103, 6, 5, 68, 32, 40, 36, 32),
}
HIGHEST_BIN = "relative_q90_q100_long_range"


def read_csv_by_model(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {row["source_model"]: row for row in rows}
    if set(result) != set(MODELS):
        raise RuntimeError(f"unexpected models in {path}")
    return result


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty table {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fp_stem_attribution() -> dict[str, Counter[str]]:
    """Count FP pairs by predicted-stem disposition without changing labels."""

    partitions = {row["record_id"]: row for row in read_jsonl(BASELINE / "pair_partitions.jsonl")}
    totals: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for event in read_jsonl(RESULTS / "stem_error_events.jsonl"):
        model = event["source_model"]
        fp = {tuple(pair) for pair in partitions[event["record_id"]]["false_positive_pairs"]}
        covered: set[tuple[int, int]] = set()
        for match in event["isolated_matches"]:
            pairs = {tuple(pair) for pair in match["predicted_stem"]["pairs"]}
            selected = pairs & fp
            totals[model][f"isolated_{match['state']}_fp_pairs"] += len(selected)
            covered.update(selected)
        for component in event["ambiguous_components"]:
            for stem in component["predicted_stems"]:
                selected = {tuple(pair) for pair in stem["pairs"]} & fp
                totals[model]["ambiguous_predicted_stem_fp_pairs"] += len(selected)
                covered.update(selected)
        for stem in event["unmatched_predicted_stems"]:
            selected = {tuple(pair) for pair in stem["pairs"]} & fp
            totals[model]["unmatched_predicted_stem_fp_pairs"] += len(selected)
            covered.update(selected)
        totals[model]["fp_pairs_in_predicted_strict_stems"] += len(covered)
        totals[model]["fp_pairs_total"] += len(fp)
    for model in MODELS:
        totals[model]["fp_pairs_outside_predicted_strict_stems"] = (
            totals[model]["fp_pairs_total"]
            - totals[model]["fp_pairs_in_predicted_strict_stems"]
        )
    return dict(totals)


def build_model_summaries() -> list[dict[str, Any]]:
    baseline = read_csv_by_model(BASELINE / "summary_by_model.csv")
    pair = read_csv_by_model(RESULTS / "pair_error_summary_by_model.csv")
    stem = read_csv_by_model(RESULTS / "stem_error_summary_by_model.csv")
    inventory = {
        row["source_model"]: row
        for row in csv.DictReader((RESULTS / "stem_inventory_summary.csv").open())
        if row["structure_role"] == "prediction"
    }
    gt_inventory = next(
        row
        for row in csv.DictReader((RESULTS / "stem_inventory_summary.csv").open())
        if row["structure_role"] == "ground_truth"
    )
    with (RESULTS / "pair_error_by_separation_bin.csv").open(newline="", encoding="utf-8") as handle:
        highest = {
            row["source_model"]: row
            for row in csv.DictReader(handle)
            if row["separation_bin"] == HIGHEST_BIN
        }
    attribution = fp_stem_attribution()
    rows: list[dict[str, Any]] = []
    for model in MODELS:
        b, p, s, high = baseline[model], pair[model], stem[model], highest[model]
        require_fields(b, ("n_samples", "sum_tp", "sum_fp", "sum_fn"))
        require_fields(p, ("wrong_partner_event_count", "pure_false_positive_count", "missing_pairs_linked_to_wrong_partner", "pure_missing_pair_count"))
        tp, fp, fn = int(b["sum_tp"]), int(b["sum_fp"]), int(b["sum_fn"])
        if (tp, fp, fn) != EXPECTED[model]:
            raise RuntimeError(f"frozen baseline mismatch for {model}")
        gt_pairs, predicted_pairs = tp + fn, tp + fp
        gt_stems, pred_stems = int(s["gt_stem_instances"]), int(s["predicted_stem_instances"])
        state_counts = {
            key: int(s[key])
            for key in (
                "exact_count",
                "stem_truncation_count",
                "stem_extension_count",
                "stem_shift_count",
                "isolated_complex_mismatch_count",
                "ambiguous_gt_stem_count",
                "ambiguous_predicted_stem_count",
                "stem_missing_count",
                "unmatched_predicted_stem_count",
            )
        }
        observed_stems = (
            gt_stems,
            pred_stems,
            state_counts["exact_count"],
            state_counts["stem_truncation_count"],
            state_counts["stem_extension_count"],
            state_counts["stem_shift_count"],
            state_counts["isolated_complex_mismatch_count"],
            state_counts["ambiguous_gt_stem_count"],
            state_counts["ambiguous_predicted_stem_count"],
            state_counts["stem_missing_count"],
            state_counts["unmatched_predicted_stem_count"],
            int(s["ambiguous_component_count"]),
        )
        if observed_stems != EXPECTED_STEMS[model]:
            raise RuntimeError(f"frozen stem summary mismatch for {model}")
        gt_accounted = sum(
            state_counts[key]
            for key in (
                "exact_count",
                "stem_truncation_count",
                "stem_extension_count",
                "stem_shift_count",
                "isolated_complex_mismatch_count",
                "ambiguous_gt_stem_count",
                "stem_missing_count",
            )
        )
        pred_accounted = sum(
            state_counts[key]
            for key in (
                "exact_count",
                "stem_truncation_count",
                "stem_extension_count",
                "stem_shift_count",
                "isolated_complex_mismatch_count",
                "ambiguous_predicted_stem_count",
                "unmatched_predicted_stem_count",
            )
        )
        if gt_accounted != gt_stems or pred_accounted != pred_stems:
            raise RuntimeError(f"frozen stem accounting mismatch for {model}")
        wrong = int(p["wrong_partner_event_count"])
        pure_fp = int(p["pure_false_positive_count"])
        linked_missing = int(p["missing_pairs_linked_to_wrong_partner"])
        pure_missing = int(p["pure_missing_pair_count"])
        if wrong + pure_fp != fp or linked_missing + pure_missing != fn:
            raise RuntimeError(f"pair taxonomy mismatch for {model}")
        isolated_matches = sum(
            state_counts[key]
            for key in (
                "exact_count",
                "stem_truncation_count",
                "stem_extension_count",
                "stem_shift_count",
                "isolated_complex_mismatch_count",
            )
        )
        a = attribution[model]
        row: dict[str, Any] = {
            "source_model": model,
            "n_samples": int(b["n_samples"]),
            "gt_pair_count": gt_pairs,
            "predicted_pair_count": predicted_pairs,
            "tp_count": tp,
            "fp_count": fp,
            "fn_count": fn,
            "wrong_partner_event_count": wrong,
            "pure_false_positive_count": pure_fp,
            "missing_pairs_linked_to_wrong_partner": linked_missing,
            "pure_missing_pair_count": pure_missing,
            "fp_rate_among_predictions": rate(fp, predicted_pairs),
            "fn_rate_among_gt": rate(fn, gt_pairs),
            "wrong_partner_fraction_of_fp": rate(wrong, fp),
            "pure_fp_fraction_of_fp": rate(pure_fp, fp),
            "linked_missing_fraction_of_fn": rate(linked_missing, fn),
            "pure_missing_fraction_of_fn": rate(pure_missing, fn),
            "gt_stem_instances": gt_stems,
            "predicted_stem_instances": pred_stems,
            **state_counts,
            "ambiguous_component_count": int(s["ambiguous_component_count"]),
            "isolated_match_count": isolated_matches,
            "fraction_gt_stems_exact": rate(state_counts["exact_count"], gt_stems),
            "fraction_gt_stems_truncation": rate(state_counts["stem_truncation_count"], gt_stems),
            "fraction_gt_stems_extension": rate(state_counts["stem_extension_count"], gt_stems),
            "fraction_gt_stems_shift": rate(state_counts["stem_shift_count"], gt_stems),
            "fraction_gt_stems_isolated_complex": rate(state_counts["isolated_complex_mismatch_count"], gt_stems),
            "fraction_gt_stems_missing": rate(state_counts["stem_missing_count"], gt_stems),
            "fraction_gt_stems_ambiguous": rate(state_counts["ambiguous_gt_stem_count"], gt_stems),
            "fraction_predicted_stems_ambiguous": rate(state_counts["ambiguous_predicted_stem_count"], pred_stems),
            "fraction_predicted_stems_unmatched": rate(state_counts["unmatched_predicted_stem_count"], pred_stems),
            "fraction_isolated_matches_exact": rate(state_counts["exact_count"], isolated_matches),
            "fraction_isolated_matches_truncation": rate(state_counts["stem_truncation_count"], isolated_matches),
            "fraction_isolated_matches_extension": rate(state_counts["stem_extension_count"], isolated_matches),
            "fraction_isolated_matches_shift": rate(state_counts["stem_shift_count"], isolated_matches),
            "fraction_isolated_matches_complex": rate(state_counts["isolated_complex_mismatch_count"], isolated_matches),
            "highest_separation_fp_fraction": float(high["fp_fraction_within_model"]),
            "highest_separation_fn_fraction": float(high["fn_fraction_within_model"]),
            "fp_pairs_in_extension_stems": a["isolated_stem_extension_fp_pairs"],
            "fp_pairs_in_unmatched_predicted_stems": a["unmatched_predicted_stem_fp_pairs"],
            "fp_pairs_in_ambiguous_predicted_stems": a["ambiguous_predicted_stem_fp_pairs"],
            "fp_pairs_outside_predicted_strict_stems": a["fp_pairs_outside_predicted_strict_stems"],
            "fraction_fp_in_extension_stems": rate(a["isolated_stem_extension_fp_pairs"], fp),
            "fraction_fp_in_unmatched_predicted_stems": rate(a["unmatched_predicted_stem_fp_pairs"], fp),
            "mean_gt_strict_stem_length": float(gt_inventory["mean_stem_length"]),
            "mean_predicted_strict_stem_length": float(inventory[model]["mean_stem_length"]),
        }
        if any(
            isinstance(value, float) and not 0 <= value <= 1
            for key, value in row.items()
            if "rate" in key or "fraction" in key
        ):
            raise RuntimeError(f"rate outside [0,1] for {model}")
        rows.append(row)
    return rows


def build_top_patterns(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    descriptions = {
        "rnafold": (
            "no_clear_unique_dominant_pattern; core profile resembles PETfold",
            "MODERATE",
            "missing and extension GT-stem rates are near-tied; ambiguity is lower than the other models",
        ),
        "petfold": (
            "no_clear_unique_dominant_pattern; core profile resembles RNAfold",
            "MODERATE",
            "missing and extension lead, with an intermediate ambiguous-GT-stem rate",
        ),
        "trrosettarna2_native_ss": (
            "stem_extension_and_ambiguous_gt_stem_skew_with_pure_fp_dominance",
            "HIGH",
            "extension and ambiguity rates exceed both other models; pure FP is the largest pair-error partition",
        ),
    }
    rows = []
    for summary in summaries:
        model = summary["source_model"]
        pair_denominator = summary["fp_count"] + summary["fn_count"]
        pair_patterns = rank_same_unit(
            [
                RankedPattern("missing_pair", summary["fn_count"], rate(summary["fn_count"], pair_denominator), "pair_error_event", "fp_plus_fn"),
                RankedPattern("wrong_partner_fp", summary["wrong_partner_event_count"], rate(summary["wrong_partner_event_count"], pair_denominator), "pair_error_event", "fp_plus_fn"),
                RankedPattern("pure_false_positive_pair", summary["pure_false_positive_count"], rate(summary["pure_false_positive_count"], pair_denominator), "pair_error_event", "fp_plus_fn"),
            ]
        )
        stem_patterns = rank_same_unit(
            [
                RankedPattern("stem_extension", summary["stem_extension_count"], summary["fraction_gt_stems_extension"], "gt_stem_error_disposition", "gt_stem_instances"),
                RankedPattern("stem_missing", summary["stem_missing_count"], summary["fraction_gt_stems_missing"], "gt_stem_error_disposition", "gt_stem_instances"),
                RankedPattern("ambiguous_gt_stem", summary["ambiguous_gt_stem_count"], summary["fraction_gt_stems_ambiguous"], "gt_stem_error_disposition", "gt_stem_instances"),
                RankedPattern("stem_truncation", summary["stem_truncation_count"], summary["fraction_gt_stems_truncation"], "gt_stem_error_disposition", "gt_stem_instances"),
                RankedPattern("stem_shift", summary["stem_shift_count"], summary["fraction_gt_stems_shift"], "gt_stem_error_disposition", "gt_stem_instances"),
                RankedPattern("isolated_complex_mismatch", summary["isolated_complex_mismatch_count"], summary["fraction_gt_stems_isolated_complex"], "gt_stem_error_disposition", "gt_stem_instances"),
            ]
        )
        dominant, confidence, basis = descriptions[model]
        row: dict[str, Any] = {
            "source_model": model,
            "pair_level_ranking_basis": "mutually_exclusive pair-error events; denominator=FP+FN",
        }
        for index, pattern in enumerate(pair_patterns[:3], start=1):
            row[f"pair_level_rank_{index}"] = pattern.name
            row[f"pair_level_rank_{index}_count"] = pattern.count
            row[f"pair_level_rank_{index}_fraction_of_pair_errors"] = pattern.rate
        row["stem_level_ranking_basis"] = "GT-side error dispositions; denominator=gt_stem_instances; exact excluded"
        for index, pattern in enumerate(stem_patterns[:3], start=1):
            row[f"stem_level_rank_{index}"] = pattern.name
            row[f"stem_level_rank_{index}_count"] = pattern.count
            row[f"stem_level_rank_{index}_fraction_of_gt_stems"] = pattern.rate
        row.update(
            {
                "unmatched_predicted_stem_count": summary["unmatched_predicted_stem_count"],
                "unmatched_predicted_rate": summary["fraction_predicted_stems_unmatched"],
                "dominant_model_specific_pattern": dominant,
                "confidence_of_description": confidence,
                "confidence_basis": basis,
            }
        )
        rows.append(row)
    return rows


def build_shared_patterns(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model = {row["source_model"]: row for row in summaries}
    definitions = [
        ("wrong_partner", "false_positive_pair annotation", "fp_count", "wrong_partner_event_count", "wrong_partner_fraction_of_fp", "lower conditional share in trRosettaRNA2"),
        ("pure_false_positive", "false_positive_pair partition", "fp_count", "pure_false_positive_count", "pure_fp_fraction_of_fp", "higher conditional share in trRosettaRNA2"),
        ("linked_missing_pair", "false_negative_pair annotation", "fn_count", "missing_pairs_linked_to_wrong_partner", "linked_missing_fraction_of_fn", "observed in all models"),
        ("stem_extension", "GT strict-stem disposition", "gt_stem_instances", "stem_extension_count", "fraction_gt_stems_extension", "shared presence but trRosettaRNA2-skewed, not shared dominance"),
        ("stem_missing", "GT strict-stem disposition", "gt_stem_instances", "stem_missing_count", "fraction_gt_stems_missing", "similar GT-side rate across all models"),
        ("ambiguous_gt_stem", "GT strict-stem disposition", "gt_stem_instances", "ambiguous_gt_stem_count", "fraction_gt_stems_ambiguous", "strong source-model skew"),
        ("unmatched_predicted_stem", "predicted strict-stem residual", "predicted_stem_instances", "unmatched_predicted_stem_count", "fraction_predicted_stems_unmatched", "similar predicted-side rate across all models"),
        ("stem_truncation", "GT strict-stem disposition", "gt_stem_instances", "stem_truncation_count", "fraction_gt_stems_truncation", "observed across all models but rare"),
        ("stem_shift", "GT strict-stem disposition", "gt_stem_instances", "stem_shift_count", "fraction_gt_stems_shift", "observed across all models but rare"),
    ]
    rows = []
    for name, unit, denominator, count_field, rate_field, notes in definitions:
        rates = [by_model[model][rate_field] for model in MODELS]
        counts = [by_model[model][count_field] for model in MODELS]
        rows.append(
            {
                "pattern_name": name,
                "analysis_unit": unit,
                "denominator_name": denominator,
                "rnafold_rate": rates[0],
                "petfold_rate": rates[1],
                "trrosettarna2_rate": rates[2],
                "present_in_all_models": str(all(value > 0 for value in counts)).lower(),
                "relative_consistency": relative_consistency(rates),
                "notes": notes,
            }
        )
    return rows


def main() -> None:
    summaries = build_model_summaries()
    write_csv(RESULTS / "error_summary_by_model.csv", summaries)
    dataset_rows = [
        {
            "dataset": "legacy121_v1",
            "cross_dataset_evidence_available": "false",
            "cross_dataset_notes": "single-dataset descriptive evidence only",
            **row,
        }
        for row in summaries
    ]
    write_csv(RESULTS / "error_summary_by_dataset.csv", dataset_rows)
    write_csv(RESULTS / "top_error_patterns_by_model.csv", build_top_patterns(summaries))
    write_csv(RESULTS / "shared_error_patterns.csv", build_shared_patterns(summaries))
    print(json.dumps({"models": len(summaries), "frozen_counts_preserved": True}, indent=2))


if __name__ == "__main__":
    main()
