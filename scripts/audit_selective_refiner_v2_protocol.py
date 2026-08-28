#!/usr/bin/env python3
"""Reconstruct v1 failure evidence and audit GT-free cross-model signals.

This is a Legacy121 development-only audit. It does not train a model and it
does not access the external77 tree.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from rna_ccfa.cross_model import SOURCE_MODELS, cross_model_agreement_features
from rna_ccfa.metrics import metric_values_from_counts
from rna_ccfa.selective_refiner import extract_feature_rows

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "results/selective_refiner/v1"
NORM = ROOT / "normalized/legacy121_v1/predictions.jsonl"
OUT = ROOT / "results/selective_refiner/v2_protocol_audit"
SEEDS = (17, 29, 41, 53, 67)
POOLED = ("POOLED_SOURCE_AWARE", "POOLED_SOURCE_AGNOSTIC")
LOMO = (
    "LOMO_HOLDOUT_RNAFOLD",
    "LOMO_HOLDOUT_PETFOLD",
    "LOMO_HOLDOUT_TRROSETTARNA2",
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_records() -> tuple[dict[tuple[str, str], dict], dict[str, dict[str, set[tuple[int, int]]]]]:
    records: dict[tuple[str, str], dict] = {}
    predictions: dict[str, dict[str, set[tuple[int, int]]]] = defaultdict(dict)
    for line in NORM.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        source = record["source_model"]["name"]
        records[(record["rna_id"], source)] = record
        predictions[record["rna_id"]][source] = {
            tuple(pair) for pair in record["predicted_structure"]["pairs"]
        }
    if len(records) != 363 or len(predictions) != 121:
        raise AssertionError("Legacy121 normalized matrix is incomplete")
    if any(set(rows) != set(SOURCE_MODELS) for rows in predictions.values()):
        raise AssertionError("cross-model audit requires exactly three sources per RNA")
    return records, predictions


def structure_metrics(scored: list[dict[str, str]], threshold: float, records: dict) -> tuple[dict, list[dict]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in scored:
        grouped[(row["rna_id"], row["source_model"])].append(row)
    per_rna = []
    for key, rows in grouped.items():
        record = records[key]
        original = {tuple(pair) for pair in record["predicted_structure"]["pairs"]}
        ground_truth = {tuple(pair) for pair in record["ground_truth_structure"]["pairs"]}
        deleted = {
            (int(row["i"]), int(row["j"]))
            for row in rows
            if float(row["p_delete"]) >= threshold
        }
        refined = original - deleted
        before = (len(original & ground_truth), len(original - ground_truth), len(ground_truth - original))
        after = (len(refined & ground_truth), len(refined - ground_truth), len(ground_truth - refined))
        beneficial = len(deleted & (original - ground_truth))
        harmful = len(deleted & ground_truth)
        if beneficial + harmful != len(deleted):
            raise AssertionError("beneficial + harmful != modified")
        if after[0] != before[0] - harmful or after[1] != before[1] - beneficial or after[2] != before[2] + harmful:
            raise AssertionError("deletion accounting identity failed")
        _, _, f_before = metric_values_from_counts(*before)
        _, _, f_after = metric_values_from_counts(*after)
        per_rna.append({
            "rna_id": key[0], "source_model": key[1], "before": before, "after": after,
            "beneficial": beneficial, "harmful": harmful, "modified": len(deleted),
            "delta_f1": f_after - f_before,
        })

    def aggregate(rows: list[dict]) -> dict[str, float | int | None]:
        before = tuple(sum(row["before"][idx] for row in rows) for idx in range(3))
        after = tuple(sum(row["after"][idx] for row in rows) for idx in range(3))
        _, _, f_before = metric_values_from_counts(*before)
        _, _, f_after = metric_values_from_counts(*after)
        beneficial = sum(row["beneficial"] for row in rows)
        harmful = sum(row["harmful"] for row in rows)
        modified = beneficial + harmful
        return {
            "macro_delta_f1": statistics.fmean(row["delta_f1"] for row in rows),
            "micro_delta_f1": f_after - f_before,
            "modification_precision": beneficial / modified if modified else None,
            "delete_recall": beneficial / before[1] if before[1] else None,
            "correct_pair_preservation": after[0] / before[0] if before[0] else 1.0,
            "modified_pair_count": modified,
            "modified_rna_count": sum(row["modified"] > 0 for row in rows),
            "beneficial_edit_count": beneficial,
            "harmful_edit_count": harmful,
        }

    pooled = aggregate(per_rna)
    source_rows = []
    for source in SOURCE_MODELS:
        subset = [row for row in per_rna if row["source_model"] == source]
        if subset:
            source_rows.append({"source_model": source, **aggregate(subset)})
    return pooled, source_rows


def reconstruct_v1(records: dict) -> tuple[list[dict], dict]:
    run_rows: list[dict] = []
    configs = list(V1.glob("*/fold_*/seed_*/config.json"))
    scores = list(V1.glob("*/fold_*/seed_*/per_pair_scores.csv"))
    if len(configs) != 200 or len(scores) != 200:
        raise AssertionError("expected 200 final configs and score files")
    if any(json.loads(path.read_text())["seed"] not in SEEDS for path in configs):
        raise AssertionError("unexpected seed in final configurations")

    for score_path in sorted(scores):
        rel = score_path.relative_to(V1)
        variant, fold_dir, seed_dir = rel.parts[:3]
        fold, seed = int(fold_dir.split("_")[1]), int(seed_dir.split("_")[1])
        scored = list(csv.DictReader(score_path.open(encoding="utf-8")))
        threshold = json.loads((score_path.parent / "selected_threshold.json").read_text())["threshold"]
        for mode, value in (("LEARNED_UNGATED", 0.5), ("LEARNED_SELECTIVE", threshold)):
            if value is None:
                continue
            pooled, source_metrics = structure_metrics(scored, float(value), records)
            run_rows.append({
                "variant": variant, "fold": fold, "seed": seed, "mode": mode,
                "source_model": "pooled", "threshold": value, **pooled,
            })
            for source_row in source_metrics:
                run_rows.append({
                    "variant": variant, "fold": fold, "seed": seed, "mode": mode,
                    "threshold": value, **source_row,
                })

    expected_variants = {path.relative_to(V1).parts[0] for path in configs}
    if len(expected_variants) != 8:
        raise AssertionError("expected eight preregistered variants")
    deployable = {
        variant: sum(
            1 for path in V1.glob(f"{variant}/fold_*/seed_*/selected_threshold.json")
            if json.loads(path.read_text())["threshold"] is not None
        )
        for variant in sorted(expected_variants)
    }
    reconstruction = {
        "final_training_runs": 200,
        "successful_final_runs": 200,
        "failed_final_runs": 0,
        "variants": sorted(expected_variants),
        "selective_deployable_runs": deployable,
        "development_gate": json.loads((V1 / "summary/development_gate.json").read_text()),
    }
    return run_rows, reconstruction


def describe(values: list[float], folds: list[int]) -> dict[str, float | int]:
    fold_values: dict[int, list[float]] = defaultdict(list)
    for value, fold in zip(values, folds):
        fold_values[fold].append(value)
    fold_means = [statistics.fmean(items) for _, items in sorted(fold_values.items())]
    return {
        "n_runs": len(values),
        "mean": statistics.fmean(values),
        "std_population": statistics.pstdev(values),
        "median": statistics.median(values),
        "fold_mean_min": min(fold_means),
        "fold_mean_max": max(fold_means),
        "n_folds_with_deployable_runs": len(fold_means),
    }


def source_distribution(run_rows: list[dict]) -> list[dict]:
    output = []
    metrics = (
        "modification_precision", "delete_recall", "correct_pair_preservation",
        "macro_delta_f1", "micro_delta_f1", "modified_rna_count",
    )
    for variant in POOLED:
        for source in SOURCE_MODELS:
            subset = [
                row for row in run_rows
                if row["variant"] == variant and row["mode"] == "LEARNED_SELECTIVE"
                and row["source_model"] == source
            ]
            for metric in metrics:
                valid = [(float(row[metric]), int(row["fold"])) for row in subset if row[metric] is not None]
                output.append({
                    "variant": variant, "source_model": source, "metric": metric,
                    **describe([value for value, _ in valid], [fold for _, fold in valid]),
                })
    return output


def variant_mode_summary(run_rows: list[dict]) -> list[dict]:
    output = []
    metrics = (
        "modification_precision", "delete_recall", "correct_pair_preservation",
        "macro_delta_f1", "micro_delta_f1", "modified_rna_count",
    )
    variants = sorted({row["variant"] for row in run_rows})
    for variant in variants:
        for mode in ("LEARNED_UNGATED", "LEARNED_SELECTIVE"):
            for source in ("pooled", *SOURCE_MODELS):
                subset = [
                    row for row in run_rows
                    if row["variant"] == variant and row["mode"] == mode
                    and row["source_model"] == source
                ]
                if not subset:
                    continue
                for metric in metrics:
                    valid = [(float(row[metric]), int(row["fold"])) for row in subset if row[metric] is not None]
                    if valid:
                        output.append({
                            "variant": variant, "mode": mode, "source_model": source,
                            "metric": metric,
                            **describe([value for value, _ in valid], [fold for _, fold in valid]),
                        })
    return output


def mean_metric(run_rows: list[dict], variant: str, source: str, metric: str, mode: str = "LEARNED_SELECTIVE") -> float:
    values = [
        float(row[metric]) for row in run_rows
        if row["variant"] == variant and row["mode"] == mode
        and row["source_model"] == source and row[metric] is not None
    ]
    return statistics.fmean(values)


def gate_decomposition(run_rows: list[dict], reconstruction: dict) -> list[dict]:
    rows = []
    for variant in POOLED:
        value = mean_metric(run_rows, variant, "pooled", "correct_pair_preservation")
        rows.append({
            "failure_component": "A_PRESERVATION", "variant": variant, "source_model": "pooled",
            "metric": "correct_pair_preservation", "observed": value, "required": 0.99,
            "margin_observed_minus_required": value - 0.99, "status": "PASS" if value >= 0.99 else "FAIL",
            "responsible_source": "pooled aggregate",
        })
        for source in SOURCE_MODELS:
            value = mean_metric(run_rows, variant, source, "correct_pair_preservation")
            rows.append({
                "failure_component": "A_PRESERVATION", "variant": variant, "source_model": source,
                "metric": "correct_pair_preservation", "observed": value, "required": 0.98,
                "margin_observed_minus_required": value - 0.98, "status": "PASS" if value >= 0.98 else "FAIL",
                "responsible_source": source,
            })
        positive_sources = 0
        for source in SOURCE_MODELS:
            macro = mean_metric(run_rows, variant, source, "macro_delta_f1")
            micro = mean_metric(run_rows, variant, source, "micro_delta_f1")
            passed = macro > 0 and micro > 0
            positive_sources += passed
            rows.append({
                "failure_component": "B_PER_SOURCE_DELTA_F1", "variant": variant, "source_model": source,
                "metric": "macro_and_micro_delta_f1_positive", "observed": int(passed), "required": 1,
                "margin_observed_minus_required": int(passed) - 1, "status": "PASS" if passed else "FAIL",
                "macro_delta_f1": macro, "micro_delta_f1": micro, "responsible_source": source,
            })
        rows.append({
            "failure_component": "B_PER_SOURCE_DELTA_F1", "variant": variant, "source_model": "pooled_gate",
            "metric": "sources_with_positive_macro_and_micro_delta_f1", "observed": positive_sources,
            "required": 2, "margin_observed_minus_required": positive_sources - 2,
            "status": "PASS" if positive_sources >= 2 else "FAIL",
            "responsible_source": "rnafold;petfold" if positive_sources < 2 else "",
        })

    heldout = {
        "LOMO_HOLDOUT_RNAFOLD": "rnafold",
        "LOMO_HOLDOUT_PETFOLD": "petfold",
        "LOMO_HOLDOUT_TRROSETTARNA2": "trrosettarna2_native_ss",
    }
    for variant, source in heldout.items():
        observed = {
            "modification_precision": mean_metric(run_rows, variant, source, "modification_precision"),
            "correct_pair_preservation": mean_metric(run_rows, variant, source, "correct_pair_preservation"),
            "macro_delta_f1": mean_metric(run_rows, variant, source, "macro_delta_f1"),
            "micro_delta_f1": mean_metric(run_rows, variant, source, "micro_delta_f1"),
        }
        requirements = {"modification_precision": 0.80, "correct_pair_preservation": 0.98, "macro_delta_f1": 0.0, "micro_delta_f1": 0.0}
        for metric, required in requirements.items():
            strict = metric.endswith("delta_f1")
            passed = observed[metric] > required if strict else observed[metric] >= required
            rows.append({
                "failure_component": "C_LOMO_TRANSFER", "variant": variant, "source_model": source,
                "metric": metric, "observed": observed[metric], "required": f">{required}" if strict else required,
                "margin_observed_minus_required": observed[metric] - required,
                "status": "PASS" if passed else "FAIL", "responsible_source": source if not passed else "",
            })
    for variant, count in reconstruction["selective_deployable_runs"].items():
        rows.append({
            "failure_component": "DEPLOYABILITY_DIAGNOSTIC", "variant": variant, "source_model": "applicable",
            "metric": "deployable_fold_seed_runs", "observed": count, "required": "not a frozen v1 gate",
            "margin_observed_minus_required": "", "status": "DESCRIPTIVE",
            "responsible_source": "",
        })
    return rows


def topology_cache(records: dict) -> dict[tuple[str, str, tuple[int, int]], dict]:
    cache = {}
    for (rna_id, source), record in records.items():
        rows = extract_feature_rows(
            rna_id, record["sequence"], record["predicted_structure"]["pairs"],
            record["ground_truth_structure"]["pairs"], source, True,
        )
        for row in rows:
            cache[(rna_id, source, row.pair)] = {**row.features, "label_delete": row.label}
    return cache


def harmful_breakdown(records: dict) -> list[dict]:
    features = topology_cache(records)
    counts: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
    for variant in POOLED:
        for score_path in sorted(V1.glob(f"{variant}/fold_*/seed_*/per_pair_scores.csv")):
            threshold = json.loads((score_path.parent / "selected_threshold.json").read_text())["threshold"]
            if threshold is None:
                continue
            for row in csv.DictReader(score_path.open(encoding="utf-8")):
                if float(row["p_delete"]) < float(threshold):
                    continue
                key = (row["rna_id"], row["source_model"], (int(row["i"]), int(row["j"])))
                feature = features[key]
                outcome = "beneficial" if feature["label_delete"] == 1 else "harmful"
                stem_len = int(feature["strict_stem_length"])
                if feature["singleton_flag"]:
                    position = "singleton"
                elif feature["outer_boundary_flag"]:
                    position = "outer_boundary"
                elif feature["inner_boundary_flag"]:
                    position = "inner_boundary"
                else:
                    position = "stem_interior"
                raw = int(feature["raw_separation"])
                relative = float(feature["relative_separation"])
                categories = {
                    "singleton": "yes" if feature["singleton_flag"] else "no",
                    "strict_stem": "yes" if stem_len >= 2 else "no",
                    "two_pair_stem": "yes" if stem_len == 2 else "no",
                    "outer_boundary": "yes" if feature["outer_boundary_flag"] else "no",
                    "inner_boundary": "yes" if feature["inner_boundary_flag"] else "no",
                    "topology_position": position,
                    "pair_type": str(feature["pair_type"]),
                    "raw_separation_bin": "lt10" if raw < 10 else "10_24" if raw < 25 else "25_49" if raw < 50 else "ge50",
                    "relative_separation_bin": "q0_0.25" if relative <= .25 else "q0.25_0.50" if relative <= .5 else "q0.50_0.75" if relative <= .75 else "q0.75_1.00",
                    "stem_length": "singleton" if stem_len == 0 else str(stem_len) if stem_len < 5 else "5_plus",
                }
                for dimension, category in categories.items():
                    counts[(variant, row["source_model"], outcome, dimension, category)] += 1
    totals: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for (variant, source, outcome, dimension, _), count in counts.items():
        totals[(variant, source, outcome, dimension)] += count
    return [
        {
            "variant": variant, "source_model": source, "edit_outcome": outcome,
            "feature_dimension": dimension, "category": category, "edit_count": count,
            "fraction_within_source_outcome_dimension": count / totals[(variant, source, outcome, dimension)],
        }
        for (variant, source, outcome, dimension, category), count in sorted(counts.items())
    ]


def cross_model_audit(records: dict, predictions: dict) -> tuple[list[dict], list[dict], dict]:
    # Prediction-only features are fully materialized before labels are joined.
    observable_rows = []
    for rna_id, source_predictions in sorted(predictions.items()):
        for source in SOURCE_MODELS:
            for pair in sorted(source_predictions[source]):
                record = records[(rna_id, source)]
                local = next(
                    row for row in extract_feature_rows(
                        rna_id, record["sequence"], record["predicted_structure"]["pairs"],
                        [], source, True,
                    ) if row.pair == pair
                )
                observable_rows.append({
                    "rna_id": rna_id, "source_model": source, "pair": pair,
                    "singleton_flag": local.features["singleton_flag"],
                    **cross_model_agreement_features(
                        source, pair, source_predictions, sequence_length=len(record["sequence"])
                    ),
                })
    if len(observable_rows) != 5290:
        raise AssertionError("cross-model observable rows do not match frozen pair inventory")

    labelled = []
    for row in observable_rows:
        gt = {tuple(pair) for pair in records[(row["rna_id"], row["source_model"])]["ground_truth_structure"]["pairs"]}
        labelled.append({**row, "label_delete": int(row["pair"] not in gt)})

    conditions = {
        "support_other_count_0": lambda row: row["exact_support_other_count"] == 0,
        "support_other_count_1": lambda row: row["exact_support_other_count"] == 1,
        "support_other_count_2": lambda row: row["exact_support_other_count"] == 2,
        "no_exact_support_plus_partner_conflict": lambda row: row["exact_support_other_count"] == 0 and row["any_partner_conflict"] == 1,
        "no_exact_support_plus_singleton": lambda row: row["exact_support_other_count"] == 0 and row["singleton_flag"] == 1,
        "exact_support_by_one_other_model": lambda row: row["exact_support_other_count"] == 1,
        "exact_support_by_both_other_models": lambda row: row["exact_support_other_count"] == 2,
    }

    def summarize(rows: list[dict], condition_name: str, scope: str, source: str) -> dict:
        total = len(rows); fp = sum(row["label_delete"] for row in rows); tp = total - fp
        return {
            "scope": scope, "source_model": source, "condition": condition_name,
            "total_predicted_pairs": total, "tp_count": tp, "fp_count": fp,
            "fp_fraction": fp / total if total else None,
            "beneficial_deletion_potential_count": fp,
            "beneficial_deletion_potential_fraction": fp / total if total else None,
        }

    pooled_rows = []
    source_rows = []
    for name, predicate in conditions.items():
        pooled_rows.append(summarize([row for row in labelled if predicate(row)], name, "pooled", "pooled"))
        for source in SOURCE_MODELS:
            source_rows.append(summarize(
                [row for row in labelled if row["source_model"] == source and predicate(row)],
                name, "source", source,
            ))

    support_stats = {}
    for source in ("pooled", *SOURCE_MODELS):
        subset = labelled if source == "pooled" else [row for row in labelled if row["source_model"] == source]
        fractions = []
        for support_count in (0, 1, 2):
            rows = [row for row in subset if row["exact_support_other_count"] == support_count]
            fractions.append(sum(row["label_delete"] for row in rows) / len(rows))
        support_stats[source] = {
            "fp_fraction_support_0_1_2": fractions,
            "correct_probability_support_0_1_2": [1 - value for value in fractions],
            "monotonic_correctness_increase": all(
                1 - fractions[idx] < 1 - fractions[idx + 1] for idx in range(2)
            ),
            "zero_support_fp_enrichment_vs_source_baseline": fractions[0] / (
                sum(row["label_delete"] for row in subset) / len(subset)
            ),
        }
    return pooled_rows, source_rows, support_stats


def main() -> None:
    records, predictions = load_records()
    run_rows, reconstruction = reconstruct_v1(records)
    distribution = source_distribution(run_rows)
    variant_summary = variant_mode_summary(run_rows)
    gate_rows = gate_decomposition(run_rows, reconstruction)
    harmful_rows = harmful_breakdown(records)
    enrichment, by_source, support_stats = cross_model_audit(records, predictions)

    # Independently reconstructed headline means must reproduce the frozen report.
    expected = {
        ("POOLED_SOURCE_AWARE", "modification_precision"): 0.8753865496061206,
        ("POOLED_SOURCE_AWARE", "delete_recall"): 0.4397344717235926,
        ("POOLED_SOURCE_AWARE", "correct_pair_preservation"): 0.9880795569112636,
        ("POOLED_SOURCE_AGNOSTIC", "modification_precision"): 0.8572464144169508,
        ("POOLED_SOURCE_AGNOSTIC", "delete_recall"): 0.4283801292195618,
        ("POOLED_SOURCE_AGNOSTIC", "correct_pair_preservation"): 0.9850926072157197,
    }
    checks = {}
    for (variant, metric), target in expected.items():
        observed = mean_metric(run_rows, variant, "pooled", metric)
        checks[f"{variant}.{metric}"] = {"observed": observed, "frozen": target, "absolute_difference": abs(observed - target)}
        if not math.isclose(observed, target, rel_tol=0, abs_tol=1e-12):
            raise AssertionError(f"v1 reconstruction mismatch: {variant} {metric}")
    reconstruction["headline_metric_checks"] = checks
    reconstruction["cross_model_support_stats"] = support_stats
    reconstruction["external77_accessed"] = False

    write_csv(OUT / "v1_reconstructed_run_metrics.csv", run_rows)
    write_csv(OUT / "v1_pooled_source_distribution.csv", distribution)
    write_csv(OUT / "v1_variant_mode_summary.csv", variant_summary)
    write_csv(OUT / "v1_gate_failure_decomposition.csv", gate_rows)
    write_csv(OUT / "harmful_edit_feature_breakdown.csv", harmful_rows)
    write_csv(OUT / "cross_model_support_label_enrichment.csv", enrichment)
    write_csv(OUT / "cross_model_support_by_source.csv", by_source)
    (OUT / "v1_reconstruction.json").write_text(json.dumps(reconstruction, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "final_runs": reconstruction["final_training_runs"],
        "failed_runs": reconstruction["failed_final_runs"],
        "support_stats": support_stats,
        "output": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
