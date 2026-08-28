#!/usr/bin/env python3
"""Audit the v2 failure and freeze-input evidence for selective-refiner v3.

This script is retrospective Legacy121 development analysis only. It reads the
authoritative v1 pooled source-agnostic held-out scores and immutable Legacy121
predictions. It does not select or evaluate a v3 policy and has no external77
input path.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "results/selective_refiner/v1/POOLED_SOURCE_AGNOSTIC"
V2_GATE = ROOT / "results/selective_refiner/v2/summary/primary_gate_metrics.json"
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
OUTPUT = ROOT / "results/selective_refiner/v3_protocol_audit"
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
SEEDS = (17, 29, 41, 53, 67)


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_prediction_sets() -> dict[str, dict[str, set[tuple[int, int]]]]:
    predictions: dict[str, dict[str, set[tuple[int, int]]]] = defaultdict(dict)
    for line in NORMALIZED.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        source = record["source_model"]["name"]
        predictions[record["rna_id"]][source] = {
            tuple(pair) for pair in record["predicted_structure"]["pairs"]
        }
    if len(predictions) != 121:
        raise AssertionError("Legacy121 RNA count is not 121")
    if any(set(source_sets) != set(SOURCES) for source_sets in predictions.values()):
        raise AssertionError("Legacy121 three-source matrix is incomplete")
    return predictions


def v2_failure_rows() -> list[dict]:
    gate = json.loads(V2_GATE.read_text(encoding="utf-8"))
    rows = []
    metrics = (
        "beneficial_edit_count", "harmful_edit_count", "modification_precision",
        "delete_recall", "correct_pair_preservation", "macro_delta_f1",
        "micro_delta_f1",
    )
    scopes = [("pooled", "ALL", gate["base_metrics"], gate["primary_metrics"])]
    scopes.extend(
        ("source", source, values["base"], values["cross"])
        for source, values in gate["source_aggregates"].items()
    )
    for scope, source, base, cross in scopes:
        for metric in metrics:
            rows.append({
                "scope": scope, "source_model": source, "metric": metric,
                "base": base[metric], "cross": cross[metric],
                "cross_minus_base": cross[metric] - base[metric],
            })
    rows.extend([
        {"scope": "gate", "source_model": "ALL", "metric": "cross_global_deployable_runs", "base": "NA", "cross": 8, "cross_minus_base": "NA", "required": 25, "pass": False},
        {"scope": "gate", "source_model": "ALL", "metric": "delete_recall_drop_limit", "base": gate["base_metrics"]["delete_recall"], "cross": gate["primary_metrics"]["delete_recall"], "cross_minus_base": gate["primary_metrics"]["delete_recall"] - gate["base_metrics"]["delete_recall"], "required": ">=-0.02", "pass": False},
        {"scope": "gate", "source_model": "ALL", "metric": "paired_mean_macro_delta_f1_gain", "base": "paired", "cross": gate["paired_mean_macro_delta_f1_gain"], "cross_minus_base": gate["paired_mean_macro_delta_f1_gain"], "required": ">0", "pass": False},
        {"scope": "gate", "source_model": "ALL", "metric": "paired_mean_micro_delta_f1_gain", "base": "paired", "cross": gate["paired_mean_micro_delta_f1_gain"], "cross_minus_base": gate["paired_mean_micro_delta_f1_gain"], "required": ">0", "pass": False},
    ])
    return rows


def base_edit_support_rows(predictions) -> tuple[list[dict], dict]:
    counts: dict[tuple[str, int], dict[str, int]] = defaultdict(
        lambda: {"candidate_deletion_events": 0, "beneficial_deletions": 0, "harmful_deletions": 0}
    )
    deployable = 0
    abstained = 0
    total_score_rows = 0
    for fold in range(5):
        for seed in SEEDS:
            run = V1 / f"fold_{fold}" / f"seed_{seed}"
            threshold = json.loads((run / "selected_threshold.json").read_text(encoding="utf-8"))["threshold"]
            score_rows = list(csv.DictReader((run / "per_pair_scores.csv").open(encoding="utf-8")))
            if any(row["partition"] != "test" for row in score_rows):
                raise AssertionError("authoritative v1 score file contains non-test rows")
            total_score_rows += len(score_rows)
            if threshold is None:
                abstained += 1
                continue
            deployable += 1
            for row in score_rows:
                if float(row["p_delete"]) < float(threshold):
                    continue
                source = row["source_model"]
                pair = (int(row["i"]), int(row["j"]))
                other_sources = [other for other in SOURCES if other != source]
                support = sum(pair in predictions[row["rna_id"]][other] for other in other_sources)
                label = int(row["label_delete"])
                for scope_source in ("ALL", source):
                    cell = counts[(scope_source, support)]
                    cell["candidate_deletion_events"] += 1
                    cell["beneficial_deletions"] += int(label == 1)
                    cell["harmful_deletions"] += int(label == 0)

    rows = []
    for scope_source in ("ALL", *SOURCES):
        total_beneficial = sum(counts[(scope_source, support)]["beneficial_deletions"] for support in range(3))
        total_harmful = sum(counts[(scope_source, support)]["harmful_deletions"] for support in range(3))
        for support in range(3):
            cell = counts[(scope_source, support)]
            edits = cell["candidate_deletion_events"]
            beneficial = cell["beneficial_deletions"]
            harmful = cell["harmful_deletions"]
            rows.append({
                "scope": "pooled" if scope_source == "ALL" else "source",
                "source_model": scope_source,
                "support_other_count": support,
                **cell,
                "deletion_precision": beneficial / edits if edits else "NA",
                "fraction_of_scope_harmful_deletions": harmful / total_harmful if total_harmful else "NA",
                "fraction_of_scope_beneficial_deletions": beneficial / total_beneficial if total_beneficial else "NA",
            })
    pooled = [row for row in rows if row["source_model"] == "ALL"]
    if sum(row["beneficial_deletions"] for row in pooled) != 1571:
        raise AssertionError("BASE beneficial edit total does not reproduce v2.0.1")
    if sum(row["harmful_deletions"] for row in pooled) != 282:
        raise AssertionError("BASE harmful edit total does not reproduce v2.0.1")
    audit = {
        "dataset": "Legacy121 development only",
        "authoritative_score_backbone": "v1 POOLED_SOURCE_AGNOSTIC",
        "fold_seed_runs": 25,
        "deployable_runs": deployable,
        "abstain_no_refinement_runs": abstained,
        "test_pair_score_rows_across_runs": total_score_rows,
        "beneficial_deletions": 1571,
        "harmful_deletions": 282,
        "v3_policy_evaluated": False,
        "external77_accessed": False,
    }
    return rows, audit


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    predictions = load_prediction_sets()
    failure = v2_failure_rows()
    support, audit = base_edit_support_rows(predictions)
    write_csv(OUTPUT / "v2_failure_decomposition.csv", failure)
    write_csv(OUTPUT / "base_edit_support_breakdown.csv", support)
    (OUTPUT / "base_edit_support_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    support2 = next(row for row in support if row["source_model"] == "ALL" and row["support_other_count"] == 2)
    print(json.dumps({
        "status": "PASS", "deployable_base_runs": audit["deployable_runs"],
        "base_beneficial": audit["beneficial_deletions"], "base_harmful": audit["harmful_deletions"],
        "support2_beneficial": support2["beneficial_deletions"],
        "support2_harmful": support2["harmful_deletions"],
        "v3_policy_evaluated": False, "external77_accessed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
