#!/usr/bin/env python3
"""Execute the frozen, no-retraining Legacy121 selective-refiner v3 study.

The only model scores read here are the locally reconstructed, audited v1
POOLED_SOURCE_AGNOSTIC validation/test probabilities. No external77 path is
referenced by this script.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

from rna_ccfa.metrics import metric_values_from_counts

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "results/selective_refiner/v1/POOLED_SOURCE_AGNOSTIC"
V1_BASE = ROOT / "results/selective_refiner/v2/base_reconstructed/POOLED_SOURCE_AGNOSTIC"
NORM = ROOT / "normalized/legacy121_v1/predictions.jsonl"
OUT = ROOT / "results/selective_refiner/v3"
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
SEEDS = (17, 29, 41, 53, 67)
GRID = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_records():
    records = {}
    predictions = defaultdict(dict)
    for line in NORM.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        source = record["source_model"]["name"]
        key = (record["rna_id"], source)
        records[key] = record
        predictions[record["rna_id"]][source] = {tuple(pair) for pair in record["predicted_structure"]["pairs"]}
    if len(records) != 363 or len(predictions) != 121:
        raise AssertionError("Legacy121 normalized matrix is incomplete")
    if any(set(predictions[rna]) != set(SOURCES) for rna in predictions):
        raise AssertionError("Legacy121 does not have exactly three source predictions per RNA")
    return records, predictions


def support_count(rna_id, source, pair, predictions):
    return sum(pair in predictions[rna_id][other] for other in SOURCES if other != source)


def audit_full_support(records, predictions):
    counts = {0: [0, 0, 0], 1: [0, 0, 0], 2: [0, 0, 0]}
    for (rna_id, source), record in sorted(records.items()):
        gt = {tuple(pair) for pair in record["ground_truth_structure"]["pairs"]}
        for raw_pair in record["predicted_structure"]["pairs"]:
            pair = tuple(raw_pair)
            support = support_count(rna_id, source, pair, predictions)
            counts[support][0] += 1
            counts[support][1 if pair in gt else 2] += 1
    expected = {0: (504, 80, 424), 1: (586, 216, 370), 2: (4200, 4101, 99)}
    observed = {support: tuple(values) for support, values in counts.items()}
    if observed != expected:
        raise AssertionError(f"support audit mismatch: {observed} != {expected}")
    return observed


def read_rows(path):
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    keys = [(row["rna_id"], row["source_model"], int(row["i"]), int(row["j"])) for row in rows]
    if len(keys) != len(set(keys)):
        raise AssertionError(f"duplicate pair rows in {path}")
    return rows


def audit_score_inputs(records):
    runs = {}
    for fold in range(5):
        for seed in SEEDS:
            v1_dir = V1 / f"fold_{fold}" / f"seed_{seed}"
            base_dir = V1_BASE / f"fold_{fold}" / f"seed_{seed}"
            config = json.loads((v1_dir / "config.json").read_text(encoding="utf-8"))
            if config["variant"] != "POOLED_SOURCE_AGNOSTIC" or int(config["fold"]) != fold or int(config["seed"]) != seed:
                raise AssertionError("v1 config identity mismatch")
            threshold = json.loads((v1_dir / "selected_threshold.json").read_text(encoding="utf-8"))["threshold"]
            validation = read_rows(base_dir / "validation_pair_scores.csv")
            test = read_rows(base_dir / "test_pair_scores.csv")
            if not validation or not test or any(row["partition"] != part for row in validation for part in ["validation"]):
                raise AssertionError("invalid reconstructed v1 validation partition")
            if any(row["partition"] != "test" for row in test):
                raise AssertionError("invalid reconstructed v1 test partition")
            if any((row["rna_id"], row["source_model"]) not in records for row in validation + test):
                raise AssertionError("score row references unknown Legacy121 record")
            reconstructed_threshold = json.loads((base_dir / "global_threshold.json").read_text(encoding="utf-8"))["threshold"]
            if reconstructed_threshold != threshold:
                raise AssertionError("v1 authoritative threshold does not match reconstruction")
            for row in validation + test:
                for field in ("i", "j", "label_delete", "p_delete"):
                    if field not in row or row[field] == "":
                        raise AssertionError(f"missing score field {field}")
            runs[(fold, seed)] = {"threshold": threshold, "validation": validation, "test": test, "v1_config": config}
    if len(runs) != 25:
        raise AssertionError("expected 25 v1 score realizations")
    return runs


def choose_recalibrated_threshold(rows, predictions):
    tp = sum(int(row["label_delete"]) == 0 for row in rows)
    support2 = sum(support_count(row["rna_id"], row["source_model"], (int(row["i"]), int(row["j"])), predictions) == 2 for row in rows)
    candidates = []
    for threshold in GRID:
        deleted = [row for row in rows if support_count(row["rna_id"], row["source_model"], (int(row["i"]), int(row["j"])), predictions) < 2 and float(row["p_delete"]) >= threshold]
        harmful = sum(int(row["label_delete"]) == 0 for row in deleted)
        beneficial = sum(int(row["label_delete"]) == 1 for row in deleted)
        _, _, f1 = metric_values_from_counts(beneficial, harmful, sum(int(row["label_delete"]) == 1 for row in rows) - beneficial)
        preservation = 1.0 - harmful / tp if tp else 1.0
        candidates.append({"threshold": threshold, "eligible": preservation >= .99, "validation_preservation": preservation, "validation_delete_f1": f1, "forced_keep_pairs": support2, "deletion_candidates": len(deleted), "beneficial_deletions": beneficial, "harmful_deletions": harmful})
    eligible = [row for row in candidates if row["eligible"]]
    selected = max(eligible, key=lambda row: (row["validation_delete_f1"], row["threshold"], -row["deletion_candidates"])) if eligible else None
    return selected, candidates


def apply_condition(rows, records, predictions, mode, threshold):
    decisions = []
    grouped = defaultdict(list)
    for row in rows:
        pair = (int(row["i"]), int(row["j"]))
        support = support_count(row["rna_id"], row["source_model"], pair, predictions)
        if mode == "agreement_zero_support":
            delete = support == 0
        elif threshold is None:
            delete = False
        else:
            delete = float(row["p_delete"]) >= float(threshold) and (mode == "base" or support < 2)
        decisions.append({**row, "support_other_count": support, "delete": int(delete), "decision": "DELETE" if delete else "KEEP"})
        grouped[(row["rna_id"], row["source_model"])].append((row, pair, delete))
    per_rna = []
    before_counts = [0, 0, 0]
    after_counts = [0, 0, 0]
    beneficial = harmful = modified = modified_rnas = 0
    for key, items in sorted(grouped.items()):
        record = records[key]
        original = {tuple(pair) for pair in record["predicted_structure"]["pairs"]}
        gt = {tuple(pair) for pair in record["ground_truth_structure"]["pairs"]}
        deleted = {pair for _, pair, delete in items if delete}
        refined = original - deleted
        before = (len(original & gt), len(original - gt), len(gt - original))
        after = (len(refined & gt), len(refined - gt), len(gt - refined))
        b = len(deleted & (original - gt)); h = len(deleted & gt)
        if b + h != len(deleted) or after[0] != before[0] - h or after[1] != before[1] - b or after[2] != before[2] + h:
            raise AssertionError(f"v3 deletion accounting failure for {key}")
        for idx in range(3): before_counts[idx] += before[idx]; after_counts[idx] += after[idx]
        beneficial += b; harmful += h; modified += len(deleted); modified_rnas += int(bool(deleted))
        _, _, f_before = metric_values_from_counts(*before); _, _, f_after = metric_values_from_counts(*after)
        per_rna.append({"rna_id": key[0], "source_model": key[1], "original_f1": f_before, "refined_f1": f_after, "delta_f1": f_after - f_before, "beneficial_edits": b, "harmful_edits": h, "modified_pairs": len(deleted), "tp_before": before[0], "tp_after": after[0], "fp_before": before[1], "fp_after": after[1], "fn_before": before[2], "fn_after": after[2], "original_pairs": sorted(original), "refined_pairs": sorted(refined)})
    _, _, original_f1 = metric_values_from_counts(*before_counts)
    _, _, refined_f1 = metric_values_from_counts(*after_counts)
    return {"macro_delta_f1": statistics.fmean(row["delta_f1"] for row in per_rna), "micro_delta_f1": refined_f1 - original_f1, "modification_precision": beneficial / (beneficial + harmful) if beneficial + harmful else None, "delete_recall": beneficial / before_counts[1] if before_counts[1] else 0.0, "correct_pair_preservation": after_counts[0] / before_counts[0] if before_counts[0] else 1.0, "modified_pair_count": modified, "modified_rna_count": modified_rnas, "eligible_rna_count": len(per_rna), "beneficial_edit_count": beneficial, "harmful_edit_count": harmful, "original_tp_count": before_counts[0], "tp_after_count": after_counts[0], "original_fp_count": before_counts[1], "per_rna": per_rna, "decisions": decisions}


def aggregate(rows):
    beneficial = sum(row["beneficial_edit_count"] for row in rows); harmful = sum(row["harmful_edit_count"] for row in rows)
    tp_before = sum(row["original_tp_count"] for row in rows); tp_after = sum(row["tp_after_count"] for row in rows); fp_before = sum(row["original_fp_count"] for row in rows)
    return {"modification_precision": beneficial / (beneficial + harmful) if beneficial + harmful else None, "delete_recall": beneficial / fp_before if fp_before else 0.0, "correct_pair_preservation": tp_after / tp_before if tp_before else 1.0, "macro_delta_f1": statistics.fmean(row["macro_delta_f1"] for row in rows), "micro_delta_f1": statistics.fmean(row["micro_delta_f1"] for row in rows), "beneficial_edit_count": beneficial, "harmful_edit_count": harmful, "modified_pair_count": sum(row["modified_pair_count"] for row in rows), "modified_rna_count": sum(row["modified_rna_count"] for row in rows), "eligible_rna_count": sum(row["eligible_rna_count"] for row in rows), "modified_rna_fraction": sum(row["modified_rna_count"] for row in rows) / sum(row["eligible_rna_count"] for row in rows)}


def main():
    records, predictions = load_records()
    support_audit = audit_full_support(records, predictions)
    runs = audit_score_inputs(records)
    conditions = {"V3_BASE": "base", "V3_VETO2_FIXED": "fixed", "V3_VETO2_RECALIBRATED": "recalibrated", "AGREEMENT_ZERO_SUPPORT_RULE": "agreement_zero_support"}
    condition_outcomes = defaultdict(list); source_outcomes = defaultdict(list); threshold_rows = []; integrity_failures = []
    for (fold, seed), run in runs.items():
        recal_selected, search = choose_recalibrated_threshold(run["validation"], predictions)
        base_threshold = run["threshold"]
        threshold_rows.append({"fold": fold, "seed": seed, "base_threshold": base_threshold, "veto2_recalibrated_threshold": recal_selected["threshold"] if recal_selected else None, "base_deployable": base_threshold is not None, "primary_deployable": recal_selected is not None, "base_abstention_converted": base_threshold is None and recal_selected is not None, "validation_delete_f1": recal_selected["validation_delete_f1"] if recal_selected else None, "validation_preservation": recal_selected["validation_preservation"] if recal_selected else None, "validation_forced_keep_pairs": recal_selected["forced_keep_pairs"] if recal_selected else sum(support_count(row["rna_id"], row["source_model"], (int(row["i"]), int(row["j"])), predictions) == 2 for row in run["validation"]), "validation_deletion_candidates": recal_selected["deletion_candidates"] if recal_selected else sum(support_count(row["rna_id"], row["source_model"], (int(row["i"]), int(row["j"])), predictions) < 2 for row in run["validation"]), "threshold_relation": "BASE_ABSTAIN_CONVERTED" if base_threshold is None and recal_selected is not None else "PRIMARY_ABSTAIN" if recal_selected is None else "LOWER" if recal_selected["threshold"] < base_threshold else "EQUAL" if recal_selected["threshold"] == base_threshold else "ABOVE"})
        for condition, mode in conditions.items():
            threshold = base_threshold if mode in ("base", "fixed") else (recal_selected["threshold"] if recal_selected else None)
            if mode == "fixed" and base_threshold is None: threshold = None
            outcome = apply_condition(run["test"], records, predictions, mode, threshold)
            condition_outcomes[condition].append({"condition": condition, "fold": fold, "seed": seed, "threshold": threshold, "deployable": threshold is not None or mode == "agreement_zero_support", **{key: value for key, value in outcome.items() if key not in ("per_rna", "decisions")}})
            outdir = OUT / ("base" if condition == "V3_BASE" else "veto2_fixed" if condition == "V3_VETO2_FIXED" else "veto2_recalibrated" if condition == "V3_VETO2_RECALIBRATED" else "agreement_zero_support") / f"fold_{fold}" / f"seed_{seed}"
            outdir.mkdir(parents=True, exist_ok=True)
            write_csv(outdir / "per_pair_decisions.csv", outcome["decisions"])
            write_csv(outdir / "per_rna_metrics.csv", outcome["per_rna"])
            (outdir / "selected_threshold.json").write_text(json.dumps({"threshold": threshold, "status": "APPLY_THRESHOLD" if threshold is not None or mode == "agreement_zero_support" else "ABSTAIN_NO_REFINEMENT", "validation_only": mode == "recalibrated"}), encoding="utf-8")
            (outdir / "accounting_validation.json").write_text(json.dumps({"status": "PASS", "beneficial_plus_harmful_equals_modified": True, "tp_after_identity": True, "fp_after_identity": True, "fn_after_identity": True}), encoding="utf-8")
            (outdir / "config.json").write_text(json.dumps({"protocol_version": "selective_refiner_v3", "condition": condition, "fold": fold, "seed": seed, "new_neural_training_runs": 0, "score_backbone": "authoritative_v1_POOLED_SOURCE_AGNOSTIC", "external77_evaluated": False}), encoding="utf-8")
            for source in SOURCES:
                source_rows = [row for row in run["test"] if row["source_model"] == source]
                source_outcome = apply_condition(source_rows, records, predictions, mode, threshold)
                source_outcomes[condition].append({"condition": condition, "source_model": source, "fold": fold, "seed": seed, "deployable": threshold is not None or mode == "agreement_zero_support", **{key: value for key, value in source_outcome.items() if key not in ("per_rna", "decisions")}})
            write_csv(outdir / "validation_threshold_search.csv", search)
    summary = OUT / "summary"; summary.mkdir(parents=True, exist_ok=True)
    write_csv(summary / "threshold_recalibration_summary.csv", threshold_rows)
    write_csv(summary / "metrics_by_source.csv", [row for condition in conditions for row in source_outcomes[condition]])
    condition_summary = [{"condition": condition, **aggregate(condition_outcomes[condition]), "threshold_deployable_runs": sum(bool(row["deployable"]) for row in condition_outcomes[condition]), "runs": len(condition_outcomes[condition])} for condition in conditions]
    write_csv(summary / "condition_summary.csv", condition_summary)
    pairs = []
    for fold in range(5):
        for seed in SEEDS:
            base = next(row for row in condition_outcomes["V3_BASE"] if row["fold"] == fold and row["seed"] == seed)
            for condition in ("V3_VETO2_FIXED", "V3_VETO2_RECALIBRATED"):
                current = next(row for row in condition_outcomes[condition] if row["fold"] == fold and row["seed"] == seed)
                pairs.append({"fold": fold, "seed": seed, "comparison": f"{condition}_vs_V3_BASE", "base_deployable": base["deployable"], "condition_deployable": current["deployable"], "preservation_gain": current["correct_pair_preservation"] - base["correct_pair_preservation"], "macro_delta_f1_gain": current["macro_delta_f1"] - base["macro_delta_f1"], "micro_delta_f1_gain": current["micro_delta_f1"] - base["micro_delta_f1"], "beneficial_gain": current["beneficial_edit_count"] - base["beneficial_edit_count"], "harmful_gain": current["harmful_edit_count"] - base["harmful_edit_count"]})
    write_csv(summary / "base_vs_fixed_veto.csv", [row for row in pairs if row["comparison"].startswith("V3_VETO2_FIXED")])
    write_csv(summary / "base_vs_recalibrated.csv", [row for row in pairs if row["comparison"].startswith("V3_VETO2_RECALIBRATED")])
    agreement_unique = []
    for fold in range(5):
        rows = [row for row in condition_outcomes["AGREEMENT_ZERO_SUPPORT_RULE"] if row["fold"] == fold]
        agreement_unique.append({"condition": "AGREEMENT_ZERO_SUPPORT_RULE", "aggregation_unit": "unique_fold", "fold": fold, **aggregate(rows[:1])})
    agreement_repeated = {"condition": "AGREEMENT_ZERO_SUPPORT_RULE", "aggregation_unit": "repeated_fold_seed_25", **aggregate(condition_outcomes["AGREEMENT_ZERO_SUPPORT_RULE"])}
    write_csv(summary / "agreement_rule_comparison.csv", agreement_unique + [agreement_repeated])
    fixed = aggregate(condition_outcomes["V3_VETO2_FIXED"]); recal = aggregate(condition_outcomes["V3_VETO2_RECALIBRATED"]); base = aggregate(condition_outcomes["V3_BASE"])
    primary_sources = {source: aggregate([row for row in source_outcomes["V3_VETO2_RECALIBRATED"] if row["source_model"] == source]) for source in SOURCES}
    source_base = {source: aggregate([row for row in source_outcomes["V3_BASE"] if row["source_model"] == source]) for source in SOURCES}
    paired_recal = [next(row for row in condition_outcomes["V3_VETO2_RECALIBRATED"] if row["fold"] == fold and row["seed"] == seed) for fold in range(5) for seed in SEEDS]
    paired_base = [next(row for row in condition_outcomes["V3_BASE"] if row["fold"] == fold and row["seed"] == seed) for fold in range(5) for seed in SEEDS]
    criteria = {"threshold_deployability_25_of_25": sum(bool(row["deployable"]) for row in condition_outcomes["V3_VETO2_RECALIBRATED"]) == 25, "pooled_modification_precision": recal["modification_precision"] is not None and recal["modification_precision"] >= .80, "pooled_DELETE_recall": recal["delete_recall"] >= .10, "pooled_preservation": recal["correct_pair_preservation"] >= .99, "every_source_preservation": all(primary_sources[s]["correct_pair_preservation"] >= .98 for s in SOURCES), "positive_macro_and_micro_sources": sum(primary_sources[s]["macro_delta_f1"] > 0 and primary_sources[s]["micro_delta_f1"] > 0 for s in SOURCES) >= 2, "useful_source_fraction": all(primary_sources[s]["modified_rna_fraction"] >= .10 for s in SOURCES if primary_sources[s]["macro_delta_f1"] > 0 and primary_sources[s]["micro_delta_f1"] > 0), "pooled_preservation_gt_base": recal["correct_pair_preservation"] > base["correct_pair_preservation"], "pooled_precision_gte_base": recal["modification_precision"] is not None and base["modification_precision"] is not None and recal["modification_precision"] >= base["modification_precision"], "recall_drop_limit": recal["delete_recall"] - base["delete_recall"] >= -.05, "paired_macro_nonnegative": statistics.fmean(c["macro_delta_f1"] - b["macro_delta_f1"] for c, b in zip(paired_recal, paired_base)) >= 0, "paired_micro_nonnegative": statistics.fmean(c["micro_delta_f1"] - b["micro_delta_f1"] for c, b in zip(paired_recal, paired_base)) >= 0, "non_trrosetta_positive": any(primary_sources[s]["macro_delta_f1"] > 0 and primary_sources[s]["micro_delta_f1"] > 0 for s in SOURCES[:2]), "no_catastrophic_degradation": all(primary_sources[s]["correct_pair_preservation"] >= .98 and primary_sources[s]["macro_delta_f1"] >= -.005 and primary_sources[s]["micro_delta_f1"] >= -.005 for s in SOURCES)}
    gate = {"protocol_version": "selective_refiner_v3", "primary_condition": "V3_VETO2_RECALIBRATED", "matched_control": "V3_BASE", "decision": "V3_DEVELOPMENT_GATE_PASS" if all(criteria.values()) else "V3_DEVELOPMENT_GATE_FAIL", "criteria": criteria, "primary_metrics": recal, "base_metrics": base, "fixed_veto_metrics": fixed, "source_metrics": primary_sources, "base_source_metrics": source_base, "support_audit": support_audit, "new_neural_training_runs": 0, "external77_evaluated": False}
    (summary / "primary_gate_metrics.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    (summary / "primary_gate_decision.json").write_text(json.dumps({"decision": gate["decision"], "external77_evaluated": False}), encoding="utf-8")
    (summary / "veto_mechanism_summary.json").write_text(json.dumps({"base_harmful_edits": base["harmful_edit_count"], "base_beneficial_edits": base["beneficial_edit_count"], "fixed_veto_harmful_edits": fixed["harmful_edit_count"], "fixed_veto_beneficial_edits": fixed["beneficial_edit_count"], "harmful_deletions_prevented": base["harmful_edit_count"] - fixed["harmful_edit_count"], "beneficial_deletions_prevented": base["beneficial_edit_count"] - fixed["beneficial_edit_count"], "external77_evaluated": False}, indent=2), encoding="utf-8")
    (summary / "evaluation_integrity.json").write_text(json.dumps({"status": "PASS", "score_input_audit": "PASS", "support_audit": support_audit, "accounting_failures": integrity_failures, "new_neural_training_runs": 0, "v3_conditions_evaluated": 100, "external77_accessed": False, "v1_v2_modified": False}, indent=2), encoding="utf-8")
    print(json.dumps({"score_realizations": 25, "conditions": 4, "condition_outcomes": 100, "new_neural_training_runs": 0, "primary_deployable": sum(bool(row["deployable"]) for row in condition_outcomes["V3_VETO2_RECALIBRATED"]), "decision": gate["decision"], "external77_evaluated": False}, indent=2))


if __name__ == "__main__":
    main()
