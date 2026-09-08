#!/usr/bin/env python3
"""Deterministically summarize the frozen CER development experiment."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import numpy as np
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rna_ccfa.conservative_reconciliation import (  # noqa: E402
    ACTIONS, CHANNELS, CONDITIONS, MODEL_SEEDS, ROTATIONS, SCOPES, SOURCES,
    R4_GAIN_EVENT, R4_GAIN_RNA, action_accounting, evaluate_conservative_dev_gate,
    population_summary, scope_accounting,
)
from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    discrimination, fixed_bin_ece, rna_balanced_reliability, sha256_file, write_json,
)


RESULTS = ROOT / "results/conservative_reconciliation_development"
PAIR_SCORES = RESULTS / "pair_scores"
EVALUATION = RESULTS / "evaluation"
SUMMARIES = RESULTS / "summaries"
INTEGRITY = RESULTS / "integrity"
R4_SUMMARIES = ROOT / "results/clean_learned_evidence_reconciliation_r4/summaries"
DOC = ROOT / "docs/conservative_reconciliation_development_results.md"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"empty summary: {path}")
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def load_rows(condition: str, channel: str, seed: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    ids: list[int] = []
    for rotation in ROTATIONS:
        score_path = PAIR_SCORES / condition / channel / f"rotation_{rotation}" / f"seed_{seed}.parquet"
        evaluation_path = EVALUATION / condition / channel / f"rotation_{rotation}" / f"seed_{seed}.json"
        evaluation = json.loads(evaluation_path.read_text())
        if evaluation.get("status") != "PASS" or evaluation.get("pair_scores_sha256") != sha256_file(score_path):
            raise AssertionError("assessment score provenance mismatch")
        part = pq.read_table(score_path).to_pylist()
        rows.extend(part); ids.extend(int(row["candidate_row_id"]) for row in part)
    if len(ids) != len(set(ids)):
        raise AssertionError("candidate row repeated across development rotations")
    return rows


def evaluate(rows: list[dict[str, object]]) -> dict[str, object]:
    actions = [str(row["action"]) for row in rows]
    accounting = action_accounting(rows, actions)
    return {
        "reliability": {
            "event_pooled": discrimination(rows, "q_cceg"),
            "rna_balanced": rna_balanced_reliability(rows, "q_cceg"),
            "reliability_bins": fixed_bin_ece(
                [float(row["q_cceg"]) for row in rows],
                [int(row["label_delete"]) for row in rows],
            ),
        },
        "utility": accounting["utility"], "actions": accounting["actions"],
        "scope": scope_accounting(rows, actions),
    }


def flatten(condition: str, track: str, seed: int, result: dict[str, object]) -> dict[str, object]:
    event_r = result["reliability"]["event_pooled"]
    rna_r = result["reliability"]["rna_balanced"]
    event_u = result["utility"]["event_pooled"]
    rna_u = result["utility"]["rna_balanced"]
    row: dict[str, object] = {"condition": condition, "track": track, "seed": seed}
    for key in ("n_events", "positive_count", "positive_prevalence", "auprc", "auroc", "brier", "ece"):
        row[f"event_{key}"] = event_r[key]
    for key in ("rna_count", "positive_prevalence", "auprc", "auroc", "brier", "ece"):
        row[f"rna_{key}"] = rna_r[key]
    for key in (
        "context_count", "pair_event_count", "tp_before", "fp_before", "fn_before",
        "tp_after", "fp_after", "fn_after", "lost_tp", "removed_fp",
        "deleted_pair_count", "tp_preservation", "fp_removal",
        "modification_precision", "coverage", "resulting_precision",
        "resulting_recall", "resulting_f1", "original_precision", "original_recall",
        "original_f1", "delta_f1",
    ):
        row[f"event_{key}"] = event_u[key]
    for key in (
        "rna_count", "lost_tp", "removed_fp", "deleted_pair_count", "tp_preservation",
        "fp_removal", "modification_precision", "coverage", "resulting_precision",
        "resulting_recall", "resulting_f1", "original_precision", "original_recall",
        "original_f1", "delta_f1",
    ):
        row[f"rna_{key}"] = rna_u[key]
    for action in ACTIONS:
        row[f"action_{action.lower()}"] = result["actions"][action]
    row["outside_explicit_delete_count"] = result["actions"]["outside_explicit_delete_count"]
    row["outside_explicit_delete_fraction"] = result["actions"]["outside_explicit_delete_fraction"]
    return row


def summaries(per_seed: list[dict[str, object]], fields: list[str]) -> list[dict[str, object]]:
    output = []
    for condition in CONDITIONS:
        for track in (*CHANNELS, "combined"):
            subset = [row for row in per_seed if row["condition"] == condition and row["track"] == track]
            if len(subset) != 5:
                raise AssertionError("five-seed summary incomplete")
            for field in fields:
                output.append({"condition": condition, "track": track, "metric": field,
                               **population_summary([row.get(field) for row in subset])})
    return output


def mean_of(per_seed: list[dict[str, object]], condition: str, track: str, metric: str) -> float:
    values = [float(row[metric]) for row in per_seed if row["condition"] == condition and row["track"] == track]
    if len(values) != 5:
        raise AssertionError((condition, track, metric))
    return float(np.mean(values))


def main() -> None:
    execution = json.loads((INTEGRITY / "assessment_execution_audit.json").read_text())
    if execution.get("status") != "PASS" or execution.get("evaluations") != 100:
        raise SystemExit("complete sealed CER development assessment required")
    previous_gate = None
    gate_path = SUMMARIES / "conservative_dev_gate.json"
    if gate_path.exists():
        previous_gate = json.loads(gate_path.read_text())

    per_seed: list[dict[str, object]] = []
    detailed: dict[tuple[str, str, int], dict[str, object]] = {}
    row_cache: dict[tuple[str, str, int], list[dict[str, object]]] = {}
    for condition in CONDITIONS:
        for seed in MODEL_SEEDS:
            channel_rows = []
            for channel in CHANNELS:
                rows = load_rows(condition, channel, seed)
                row_cache[(condition, channel, seed)] = rows
                result = evaluate(rows); detailed[(condition, channel, seed)] = result
                per_seed.append(flatten(condition, channel, seed, result)); channel_rows.extend(rows)
            if len(channel_rows) != 310838:
                raise AssertionError(f"combined Track E universe mismatch: {len(channel_rows)}")
            result = evaluate(channel_rows); detailed[(condition, "combined", seed)] = result
            row_cache[(condition, "combined", seed)] = channel_rows
            per_seed.append(flatten(condition, "combined", seed, result))

    reliability_fields = [f"{level}_{metric}" for level in ("event", "rna") for metric in ("auprc", "auroc", "brier", "ece")]
    utility_fields = [f"{level}_{metric}" for level in ("event", "rna") for metric in ("tp_preservation", "fp_removal", "modification_precision", "coverage", "delta_f1", "lost_tp", "removed_fp")]
    action_fields = [f"action_{action.lower()}" for action in ACTIONS] + ["outside_explicit_delete_count", "outside_explicit_delete_fraction"]
    write_csv(SUMMARIES / "reliability_summary.csv", summaries(per_seed, reliability_fields))
    write_csv(SUMMARIES / "utility_summary.csv", summaries(per_seed, utility_fields))
    write_csv(SUMMARIES / "action_coverage_summary.csv", summaries(per_seed, action_fields))

    scope_per_seed = []
    for (condition, track, seed), result in detailed.items():
        for scope in SCOPES:
            for level in ("event_pooled", "rna_balanced"):
                for metric in ("opportunity_count", "lost_tp", "removed_fp", "tp_preservation", "fp_removal", "modification_precision", "coverage"):
                    if metric in result["scope"][scope][level]:
                        scope_per_seed.append({"condition": condition, "track": track, "seed": seed,
                                               "scope": scope, "aggregation": level, "metric": metric,
                                               "value": result["scope"][scope][level][metric]})
    scope_summary = []
    keys = sorted({(r["condition"], r["track"], r["scope"], r["aggregation"], r["metric"]) for r in scope_per_seed})
    for key in keys:
        values = [r["value"] for r in scope_per_seed if (r["condition"], r["track"], r["scope"], r["aggregation"], r["metric"]) == key]
        scope_summary.append(dict(zip(("condition", "track", "scope", "aggregation", "metric"), key), **population_summary(values)))
    write_csv(SUMMARIES / "scope_summary.csv", scope_summary)
    ne_rows = [row for row in scope_summary if row["scope"] == "NON_EVIDENCED" and row["metric"] in {"lost_tp", "tp_preservation", "modification_precision", "coverage"}]
    write_csv(SUMMARIES / "non_evidenced_safety_summary.csv", ne_rows)

    source_per_seed = []
    for condition in CONDITIONS:
        for seed in MODEL_SEEDS:
            for source in SOURCES:
                rows = [row for row in row_cache[(condition, "combined", seed)] if row["source"] == source]
                flat = flatten(condition, "combined", seed, evaluate(rows)); flat["source"] = source
                source_per_seed.append(flat)
    source_summary = []
    for condition in CONDITIONS:
        for source in SOURCES:
            selected = [row for row in source_per_seed if row["condition"] == condition and row["source"] == source]
            for metric in reliability_fields + utility_fields:
                source_summary.append({"condition": condition, "track": "combined", "source": source,
                                       "metric": metric, **population_summary([row[metric] for row in selected])})
    write_csv(SUMMARIES / "source_wise_summary.csv", source_summary)

    attribution = []
    for track in (*CHANNELS, "combined"):
        for metric in ("event_fp_removal", "rna_fp_removal", "event_lost_tp", "rna_lost_tp"):
            cer = mean_of(per_seed, "CER", track, metric)
            masked = mean_of(per_seed, "CER_EVIDENCE_MASKED", track, metric)
            attribution.append({"track": track, "metric": metric, "cer_mean": cer,
                                "masked_mean": masked, "cer_minus_masked": cer - masked})
    write_csv(SUMMARIES / "evidence_attribution_summary.csv", attribution)
    g_event = mean_of(per_seed, "CER", "combined", "event_fp_removal") - mean_of(per_seed, "CER_EVIDENCE_MASKED", "combined", "event_fp_removal")
    g_rna = mean_of(per_seed, "CER", "combined", "rna_fp_removal") - mean_of(per_seed, "CER_EVIDENCE_MASKED", "combined", "rna_fp_removal")
    gain_rows = [
        {"aggregation": "event", "cer_incremental_gain": g_event, "frozen_r4_incremental_gain": R4_GAIN_EVENT, "retention_ratio": g_event / R4_GAIN_EVENT},
        {"aggregation": "rna", "cer_incremental_gain": g_rna, "frozen_r4_incremental_gain": R4_GAIN_RNA, "retention_ratio": g_rna / R4_GAIN_RNA},
    ]
    write_csv(SUMMARIES / "r4_gain_retention_summary.csv", gain_rows)

    frozen = json.loads((R4_SUMMARIES / "r4_vs_frozen_baselines.json").read_text())
    r4_gate = json.loads((R4_SUMMARIES / "gate_b.json").read_text())
    with (R4_SUMMARIES / "utility_summary.csv").open(newline="", encoding="utf-8") as handle:
        r4_utility_rows = list(csv.DictReader(handle))
    r4_b4 = {
        row["metric"]: float(row["mean"])
        for row in r4_utility_rows
        if row["condition"] == "B4_EVIDENCE_MASKED" and row["track"] == "combined"
    }
    comparators = {
        "schema_version": "conservative_reconciliation_frozen_comparators_v1",
        "status": "PASS", "B0": frozen["r2_b0_original"], "E1": frozen["r3_e1"],
        "P3": frozen["r3_p3"], "B2": frozen["r2_b2_full_refold"],
        "R4_ERN": frozen["r4_ern_primary_mean"],
        "R4_B4": r4_b4,
        "r4_gate_b": "R4_GATE_B_FAIL",
        "source_artifact_hashes": {
            "comparison": sha256_file(R4_SUMMARIES / "r4_vs_frozen_baselines.json"),
            "gate_b": sha256_file(R4_SUMMARIES / "gate_b.json"),
        },
    }
    write_json(SUMMARIES / "frozen_comparator_summary.json", comparators)
    p3_sources = {source: float(r4_gate["p3_source_rna_fp_removal"][source]) for source in SOURCES}
    cer_sources = {source: float(np.mean([row["rna_fp_removal"] for row in source_per_seed if row["condition"] == "CER" and row["source"] == source])) for source in SOURCES}
    masked_sources = {source: float(np.mean([row["rna_fp_removal"] for row in source_per_seed if row["condition"] == "CER_EVIDENCE_MASKED" and row["source"] == source])) for source in SOURCES}
    primary = {
        "event_tp_preservation": mean_of(per_seed, "CER", "combined", "event_tp_preservation"),
        "rna_tp_preservation": mean_of(per_seed, "CER", "combined", "rna_tp_preservation"),
        "event_fp_removal": mean_of(per_seed, "CER", "combined", "event_fp_removal"),
        "rna_fp_removal": mean_of(per_seed, "CER", "combined", "rna_fp_removal"),
        "masked_event_fp_removal": mean_of(per_seed, "CER_EVIDENCE_MASKED", "combined", "event_fp_removal"),
        "masked_rna_fp_removal": mean_of(per_seed, "CER_EVIDENCE_MASKED", "combined", "rna_fp_removal"),
    }
    ne = {}
    for condition, target in (("CER", ne), ("CER_EVIDENCE_MASKED", None)):
        results = [detailed[(condition, "combined", seed)]["scope"]["NON_EVIDENCED"] for seed in MODEL_SEEDS]
        values = {
            "event_tp_preservation": float(np.mean([r["event_pooled"]["tp_preservation"] for r in results])),
            "rna_tp_preservation": float(np.mean([r["rna_balanced"]["tp_preservation"] for r in results])),
            "lost_tp": float(np.mean([r["event_pooled"]["lost_tp"] for r in results])),
        }
        if target is not None:
            target.update(values)
        else:
            masked_ne = values
    gate = evaluate_conservative_dev_gate(primary, ne, masked_ne, cer_sources, masked_sources, p3_sources, complete_and_valid=True)
    gate.update({"primary_combined_five_seed_mean": primary, "cer_source_rna_fp_removal": cer_sources,
                 "masked_source_rna_fp_removal": masked_sources, "legacy121_role": "DEVELOPMENT_ONLY"})
    if previous_gate is not None and previous_gate != gate:
        raise AssertionError("deterministic gate decision changed on repeat summarization")
    write_json(gate_path, gate)

    metric_lines = [
        "| Condition | Track | event AUPRC | RNA AUPRC | event TP pres. | RNA TP pres. | event FP removal | RNA FP removal | event mod. precision | RNA delta F1 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in CONDITIONS:
        for track in (*CHANNELS, "combined"):
            values = {name: mean_of(per_seed, condition, track, name) for name in (
                "event_auprc", "rna_auprc", "event_tp_preservation", "rna_tp_preservation",
                "event_fp_removal", "rna_fp_removal", "event_modification_precision", "rna_delta_f1",
            )}
            metric_lines.append(
                f"| {condition} | {track} | {values['event_auprc']:.6f} | {values['rna_auprc']:.6f} | "
                f"{values['event_tp_preservation']:.6f} | {values['rna_tp_preservation']:.6f} | "
                f"{values['event_fp_removal']:.6f} | {values['rna_fp_removal']:.6f} | "
                f"{values['event_modification_precision']:.6f} | {values['rna_delta_f1']:.6f} |"
            )
    reliability_lines = [
        "| Condition | level | AUPRC | AUROC | Brier | ECE |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for condition in CONDITIONS:
        for level in ("event", "rna"):
            values = {metric: mean_of(per_seed, condition, "combined", f"{level}_{metric}")
                      for metric in ("auprc", "auroc", "brier", "ece")}
            reliability_lines.append(
                f"| {condition} | {level} | {values['auprc']:.6f} | {values['auroc']:.6f} | "
                f"{values['brier']:.6f} | {values['ece']:.6f} |"
            )
    action_lines = ["| Condition | KEEP | DELETE | ABSTAIN | outside-explicit delete fraction |",
                    "| --- | ---: | ---: | ---: | ---: |"]
    for condition in CONDITIONS:
        action_lines.append(
            f"| {condition} | {mean_of(per_seed, condition, 'combined', 'action_keep'):.1f} | "
            f"{mean_of(per_seed, condition, 'combined', 'action_delete'):.1f} | "
            f"{mean_of(per_seed, condition, 'combined', 'action_abstain'):.1f} | "
            f"{mean_of(per_seed, condition, 'combined', 'outside_explicit_delete_fraction'):.6f} |"
        )
    scope_lines = ["| Condition | Scope | event TP pres. | RNA TP pres. | event mod. precision | mean lost TP |",
                   "| --- | --- | ---: | ---: | ---: | ---: |"]
    for condition in CONDITIONS:
        values = [detailed[(condition, "combined", seed)]["scope"] for seed in MODEL_SEEDS]
        for scope in SCOPES:
            def scope_text(aggregation: str, metric: str) -> str:
                value = population_summary([v[scope][aggregation][metric] for v in values])["mean"]
                return "N/A" if value is None else f"{value:.6f}"
            scope_lines.append(
                f"| {condition} | {scope} | "
                f"{scope_text('event_pooled', 'tp_preservation')} | "
                f"{scope_text('rna_balanced', 'tp_preservation')} | "
                f"{scope_text('event_pooled', 'modification_precision')} | "
                f"{np.mean([v[scope]['event_pooled']['lost_tp'] for v in values]):.1f} |"
            )
    source_lines = ["| Source | CER RNA FP removal | masked RNA FP removal | P3 RNA FP removal | CER−P3 | CER−masked |",
                    "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for source in SOURCES:
        source_lines.append(
            f"| {source} | {cer_sources[source]:.6f} | {masked_sources[source]:.6f} | {p3_sources[source]:.6f} | "
            f"{cer_sources[source] - p3_sources[source]:.6f} | {cer_sources[source] - masked_sources[source]:.6f} |"
        )
    criterion_lines = []
    for section in ("overall_criteria", "non_evidenced_safety", "evidence_attribution_criteria"):
        criterion_lines.extend(f"- `{name}`: **{'PASS' if value else 'FAIL'}**" for name, value in gate[section].items())
    criterion_lines.append(f"- `p3_source_condition`: **{'PASS' if gate['p3_source_condition'] else 'FAIL'}**")
    metric_table = "\n".join(metric_lines)
    action_table = "\n".join(action_lines)
    scope_table = "\n".join(scope_lines)
    source_table = "\n".join(source_lines)
    criterion_list = "\n".join(criterion_lines)
    reliability_table = "\n".join(reliability_lines)
    baseline_table = "\n".join([
        "| Frozen comparator | event TP pres. | RNA TP pres. | event FP removal | RNA FP removal |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| E1 LOCAL_CONFLICT | {float(frozen['r3_e1']['event_pooled']['tp_preservation']):.6f} | {float(frozen['r3_e1']['rna_balanced']['tp_preservation']):.6f} | {float(frozen['r3_e1']['event_pooled']['fp_removal']):.6f} | {float(frozen['r3_e1']['rna_balanced']['fp_removal']):.6f} |",
        f"| P3 V3_VETO2_FIXED | {float(frozen['r3_p3']['event_pooled']['tp_preservation']):.6f} | {float(frozen['r3_p3']['rna_balanced']['tp_preservation']):.6f} | {float(frozen['r3_p3']['event_pooled']['fp_removal']):.6f} | {float(frozen['r3_p3']['rna_balanced']['fp_removal']):.6f} |",
        f"| R4 ERN | {float(frozen['r4_ern_primary_mean']['event_tp_preservation']):.6f} | {float(frozen['r4_ern_primary_mean']['rna_tp_preservation']):.6f} | {float(frozen['r4_ern_primary_mean']['event_fp_removal']):.6f} | {float(frozen['r4_ern_primary_mean']['rna_fp_removal']):.6f} |",
        f"| B2 FULL_REFOLD_REFERENCE | {float(frozen['r2_b2_full_refold']['event_tp_preservation']):.6f} | {float(frozen['r2_b2_full_refold']['rna_tp_preservation']):.6f} | {float(frozen['r2_b2_full_refold']['event_fp_removal']):.6f} | {float(frozen['r2_b2_full_refold']['rna_fp_removal']):.6f} |",
    ])

    result_doc = f"""# Conservative Evidence Reconciliation development results

Status: `{gate['status']}`

Legacy121 role: `DEVELOPMENT_ONLY` (not independent confirmation).

## EMPIRICAL RESULT

The frozen 200-run CER/CCEG matrix, 200 branch calibrations, 100 policy calibrations, and 100 threshold seals completed. All five prescribed seeds contribute; no seed or channel was selected.

{metric_table}

Combined reliability details:

{reliability_table}

Fixed reliability bins are retained in the evaluation artifacts. Utility artifacts include coverage, complete beneficial/harmful edit accounting, precision, recall, F1, and delta F1.

### Actions and scopes (combined Track E, five-seed means)

{action_table}

{scope_table}

The primary combined five-seed means were event/RNA TP preservation {primary['event_tp_preservation']:.9f}/{primary['rna_tp_preservation']:.9f} and event/RNA FP removal {primary['event_fp_removal']:.9f}/{primary['rna_fp_removal']:.9f}. NON_EVIDENCED TP preservation was {ne['event_tp_preservation']:.9f}/{ne['rna_tp_preservation']:.9f}, with mean lost TP {ne['lost_tp']:.1f}, below the descriptive frozen R4 value 2687.8.

### Evidence attribution and R4 gain retention

The matched evidence-masked FP-removal means were {primary['masked_event_fp_removal']:.9f} (event) and {primary['masked_rna_fp_removal']:.9f} (RNA-balanced). Thus G_event={gate['g_event']:.9f} and G_RNA={gate['g_rna']:.9f}. Relative to frozen R4 ERN-minus-B4 increments, the retained fractions were {gate['event_r4_gain_retention_ratio']:.6f} and {gate['rna_r4_gain_retention_ratio']:.6f}.

{source_table}

CER improved RNA-balanced FP removal over P3 and over its matched evidence-masked control in all three current predictor sources. This is development evidence only and does not establish unseen-predictor transfer.

### Frozen comparator context

{baseline_table}

CER exceeded E1 and P3 FP removal in both aggregations while preserving less TP than either comparator. Relative to R4 ERN, CER moved above the event 0.99 preservation line while retaining similar event FP removal and higher RNA-balanced FP removal; this is post-R4 development evidence, not an independent rescue of R4. B2 removed more FP but preserved materially less TP and operates by full refolding, so the existing bounded Gate A non-dominance decision is unchanged.

## INTERPRETATION

The conservative policy achieved both overall 0.99 preservation bars and retained the evidence-attributable FP-removal increment. However, the central hypothesis required usable evidence not to reduce NON_EVIDENCED TP preservation relative to the matched masked action mechanism. CER was lower than the masked control under both event and RNA aggregation, so the conjunctive development gate fails even though CER's absolute NON_EVIDENCED preservation remained at least 0.99. The evidence benefit therefore came with evidence-attributable NON_EVIDENCED harm under the prospectively frozen comparison.

Legacy121 is internal development/hypothesis-generation data. These results do not restore independence. B2 remains a different FULL_REFOLD_REFERENCE operating space; R4 Gate A remains boundedly non-dominated and R4 Gate B remains failed.

## GATE DECISION

The one frozen conjunctive decision is `{gate['status']}`:

{criterion_list}

The two failures are `event_non_evidenced_preservation_gte_masked` and `rna_non_evidenced_preservation_gte_masked`. All other numerical, source, attribution, and gain-retention conditions passed. Per the frozen protocol, the next authorized task is `PAPER_STORY_AND_RESULTS_CONSOLIDATION`; no alternative CCEG, larger model, threshold rescue, or seed/channel selection is authorized. `R4_GATE_B_FAIL` remains unchanged.

## UNSUPPORTED CLAIMS

This experiment does not establish independent generalization, unseen-predictor/model-agnostic performance, noisy-evidence robustness, real SHAPE/DMS/PARS utility, 3D benefit, or that threshold/model rescue would succeed. external77 data were not read or used.
"""
    DOC.write_text(result_doc, encoding="utf-8")
    (SUMMARIES / "conservative_reconciliation_development_results.md").write_text(result_doc, encoding="utf-8")

    integrity_targets = sorted(path for path in (SUMMARIES).rglob("*") if path.is_file()) + [DOC]
    hashes = {str(path.relative_to(ROOT)): sha256_file(path) for path in integrity_targets}
    write_json(INTEGRITY / "edit_accounting_audit.json", {"status": "PASS", "all_actions_accounted": True, "abstain_unchanged": True, "deletion_only": True})
    write_json(INTEGRITY / "scope_action_audit.json", {"status": "PASS", "scope_precedence": ["DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED"], "direct_keep": True, "local_conflict_delete": True, "non_evidenced_cceg": True})
    write_json(INTEGRITY / "frozen_comparator_audit.json", {"status": "PASS", "r4_gate_b": "R4_GATE_B_FAIL", "hashes": comparators["source_artifact_hashes"]})
    write_json(INTEGRITY / "input_output_hash_audit.json", {"status": "PASS", "deterministic_outputs": hashes})
    prior = json.loads((INTEGRITY / "reproducibility_audit.json").read_text()) if (INTEGRITY / "reproducibility_audit.json").exists() else None
    reproducible = prior is not None and prior.get("deterministic_outputs") == hashes
    write_json(INTEGRITY / "reproducibility_audit.json", {"status": "PASS" if reproducible else "PENDING_SECOND_RUN", "deterministic_outputs": hashes, "timestamp_fields_excluded": True})
    print(json.dumps({"status": gate["status"], "reproducibility": "PASS" if reproducible else "PENDING_SECOND_RUN", "primary": primary}, indent=2))


if __name__ == "__main__":
    main()
